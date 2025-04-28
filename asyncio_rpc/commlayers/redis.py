from typing import Optional
from uuid import uuid4

import redis.asyncio as async_redis

from ..models import SERIALIZABLE_MODELS, RPCBase, RPCResult, RPCStack
from .base import AbstractRPCCommLayer

RESULT_EXPIRE_TIME = 300  # seconds


class RPCRedisCommLayer(AbstractRPCCommLayer):
    """
    Redis remote procedure call communication layer
    """

    @classmethod
    async def create(
        cls,
        subchannel=b"subchannel",
        pubchannel=b"pubchannel",
        host="localhost",
        port=6379,
        serialization=None,
    ):
        """
        Use a static create method to allow async context,
        __init__ cannot be async.
        """

        self = RPCRedisCommLayer(subchannel, pubchannel)

        # Create communicationLayer
        self.host = host
        self.port = port
        self.serialization = serialization

        # Redis for publishing
        self.redis = async_redis.from_url(
            f"redis://{host}",
            socket_keepalive=True,
            retry_on_timeout=True,
            health_check_interval=None,  # no health checks for Redis pub/sub
        )

        # By default register all RPC models
        for model in SERIALIZABLE_MODELS:
            # Register models to serialization
            serialization.register(model)

        self.subscribed = False

        # Subscription has own redis
        self.sub_redis = None
        self.sub_channel = None

        # By default subscribe
        await self.do_subscribe()

        return self

    def __init__(self, subchannel, pubchannel):
        """
        Initialize and set the sub/pub channels
        """
        self.subchannel = subchannel
        self.pubchannel = pubchannel
        self.redis: async_redis.Redis
        self.pub_sub = None

    async def do_subscribe(self):
        if not self.subscribed:
            # By default subscribe
            self.sub_redis = async_redis.from_url(f"redis://{self.host}")
            self.pub_sub = self.sub_redis.pubsub(ignore_subscribe_messages=True)
            await self.pub_sub.subscribe(self.subchannel)
            self.subscribed = True

    async def publish(self, rpc_instance: RPCBase, channel=None):
        """
        Publish redis implementation, publishes RPCBase instances.

        :return: the number of receivers
        """
        # rpc_instance should be a subclass of RPCBase
        # For now just check if instance of RPCBase
        assert isinstance(rpc_instance, RPCBase)

        if isinstance(rpc_instance, RPCStack):
            # Add subchannel to RPCStack as respond_to
            rpc_instance.respond_to = self.subchannel
        elif isinstance(rpc_instance, RPCResult) and rpc_instance.data is not None:
            # Customized:
            # result data via redis.set
            # result without data via redis.publish
            redis_key = uuid4().hex

            # Store the result data via key/value in redis
            await self.redis.set(
                redis_key,
                self.serialization.dumpb(rpc_instance.data),
                ex=RESULT_EXPIRE_TIME,
            )

            # Set redis_key and remove data, since
            # this is stored in redis now
            rpc_instance.data = {"redis_key": redis_key}

        # Override the pub_channel with channel, if set
        pub_channel = channel if channel is not None else self.pubchannel

        # Publish rpc_instance and return number of listeners
        return await self.redis.publish(
            pub_channel, self.serialization.dumpb(rpc_instance)
        )

    async def get_data(self, redis_key, delete=True):
        """
        Helper function to get data by redis_key, by default
        delete the data after retrieval.
        """
        data = self.serialization.loadb(await self.redis.get(redis_key))
        if delete:
            await self.redis.delete(redis_key)
        return data

    async def _process_msg(self, msg, on_rpc_event_callback, channel_name):
        """
        Interal message processing, is called on every received
        message via the subscription.
        """
        event = self.serialization.loadb(msg)

        # rpc_instance should be a subclass of RPCBase
        # For now just check if instance of RPCBase
        assert isinstance(event, RPCBase)

        if on_rpc_event_callback:
            if isinstance(event, RPCResult):
                # Customized:
                # result data via redis.set
                # result without data via redis.publish

                # Get data from redis and put it on the event
                if isinstance(event.data, dict) and "redis_key" in event.data:
                    event.data = await self.get_data(event.data["redis_key"])

            await on_rpc_event_callback(event, channel=channel_name)

    async def subscribe(
        self,
        on_rpc_event_callback,
        channel: Optional[str] = None,
        redis: Optional[async_redis.Redis] = None,
    ):
        """
        Redis implementation for subscribe method, receives messages from
        subscription channel.

        Note: does block in while loop until .unsubscribe() is called.
        """
        pub_sub = self.pub_sub
        if redis is not None:
            pub_sub = redis.pubsub(ignore_subscribe_messages=True)

        if channel is not None:
            await pub_sub.subscribe(channel)
        async with pub_sub as ps:
            # Inside a while loop, wait for incoming events.
            async for message in ps.listen():
                if message is not None:
                    await self._process_msg(
                        message["data"], on_rpc_event_callback, message["channel"]
                    )
        self.subscribed = False

    async def unsubscribe(self):
        """
        Redis implementation for unsubscribe. Stops subscription and breaks
        out of the while loop in .subscribe()
        """
        if self.subscribed:
            await self.pub_sub.unsubscribe()
            self.subscribed = False
            await self.sub_redis.close()

    async def close(self):
        """
        Stop subscription & close everything
        """
        await self.unsubscribe()
        await self.redis.close()
