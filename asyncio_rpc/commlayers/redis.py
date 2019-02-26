from .base import AbstractRPCCommLayer
from aioredis import create_redis
from ..models import RPCStack, RPCResult, RPCBase, SERIALIZABLE_MODELS

RESULT_EXPIRE_TIME = 300  # seconds


class RPCRedisCommLayer(AbstractRPCCommLayer):
    @classmethod
    async def create(
            cls, subchannel=b'subchannel', pubchannel=b'pubchannel',
            host='localhost', port=6379, serialization=None):
        self = RPCRedisCommLayer(subchannel, pubchannel)
        # Create communicationLayer
        self.host = host
        self.port = port
        self.serialization = serialization
        self.redis = await create_redis(
            f'redis://{host}')

        for model in SERIALIZABLE_MODELS:
            # Register models to serialization
            serialization.register(model)

        # Not subscribed..
        self.subscribed = False

        self.sub_redis = None
        self.sub_channel = None

        # By default subscribe
        await self.do_subscribe()

        return self

    def __init__(self, subchannel, pubchannel):
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

        pub_channel = channel if channel is not None else self.pubchannel

        # Publish rpc_instance
        return await self.redis.publish(
            pub_channel,
            self.serialization.dumpb(rpc_instance))

    async def get_data(self, redis_key, delete=True):
        """
        Get data by redis_key
        """
        data = self.serialization.loadb(
            await self.redis.get(redis_key))
        if delete:
            await self.redis.delete(redis_key)
        return data

    async def _process_msg(self, msg, on_rpc_event_callback, channel=None):
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
            self.subscribed = False
            redis.close()
            await redis.wait_closed()

    async def unsubscribe(self):
        if self.subscribed:
            await self.sub_redis.unsubscribe(
                self.sub_channel.name)
            self.subscribed = False

    async def close(self):
        await self.unsubscribe()
        self.redis.close()
        await self.redis.wait_closed()
