from .base import AbstractRPCCommLayer
from aioredis import create_redis
from ..models import RPCStack, RPCResult, RPCBase, SERIALIZABLE_MODELS

RESULT_EXPIRE_TIME = 300  # seconds


class RPCRedisCommLayer(AbstractRPCCommLayer):
    """
    Redis remote procedure call communication layer
    """

    @classmethod
    async def create(
            cls, subchannel=b'subchannel', pubchannel=b'pubchannel',
            host='localhost', port=6379, serialization=None):
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
        self.redis = await create_redis(
            f'redis://{host}')

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

    async def do_subscribe(self):
        if not self.subscribed:
            # By default subscribe
            self.sub_redis = await create_redis(
                f'redis://{self.host}')
            channels = await self.sub_redis.subscribe(
                self.subchannel)
            self.sub_channel = channels[0]
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
        elif ((isinstance(rpc_instance, RPCResult) and
               rpc_instance.data is not None)):
            # Customized:
            # result data via redis.set
            # result without data via redis.publish
            redis_key = self.subchannel + b'_' +\
                rpc_instance.uid.encode('utf-8')

            # Store the result data via key/value in redis
            await self.redis.set(
                redis_key,
                self.serialization.dumpb(rpc_instance.data),
                expire=RESULT_EXPIRE_TIME)

            # Set redis_key and remove data, since
            # this is stored in redis now
            rpc_instance.data = {'redis_key': redis_key}

        # Override the pub_channel with channel, if set
        pub_channel = channel if channel is not None else self.pubchannel

        # Publish rpc_instance and return number of listeners
        return await self.redis.publish(
            pub_channel,
            self.serialization.dumpb(rpc_instance))

    async def get_data(self, redis_key, delete=True):
        """
        Helper function to get data by redis_key, by default
        delete the data after retrieval.
        """
        data = self.serialization.loadb(
            await self.redis.get(redis_key))
        if delete:
            await self.redis.delete(redis_key)
        return data

    async def _process_msg(self, msg, on_rpc_event_callback, channel=None):
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
                if isinstance(event.data, dict) and 'redis_key' in event.data:
                    event.data = await self.get_data(event.data['redis_key'])

            await on_rpc_event_callback(
                event, channel=channel.name)

    async def subscribe(self, on_rpc_event_callback, channel=None, redis=None):
        """
        Redis implementation for subscribe method, receives messages from
        subscription channel.

        Note: does block in while loop until .unsubscribe() is called.
        """
        try:
            if channel is None:
                channel = self.sub_channel
            if redis is None:
                redis = self.sub_redis

            self.subscribed = True
            # Inside a while loop, wait for incoming events.
            while await channel.wait_message():
                await self._process_msg(
                    await channel.get(),
                    on_rpc_event_callback,
                    channel=channel)

        finally:
            # Close connections and cleanup
            self.subscribed = False
            redis.close()
            await redis.wait_closed()

    async def unsubscribe(self):
        """
        Redis implementation for unsubscribe. Stops subscription and breaks
        out of the while loop in .subscribe()
        """
        if self.subscribed:
            await self.sub_redis.unsubscribe(
                self.sub_channel.name)
            self.subscribed = False

    async def close(self):
        """
        Stop subscription & close everything
        """
        await self.unsubscribe()
        self.redis.close()
        await self.redis.wait_closed()
