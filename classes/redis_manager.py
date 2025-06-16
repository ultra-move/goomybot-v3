import os
import logging
import asyncio
from typing import Optional, Any, Dict, List, Union, AsyncIterator

# Change this import:
# from aioredis import RedisError, ConnectionError as RedisConnectionError
import redis.asyncio as aioredis # Import as 'aioredis' for minimal code changes below
from redis.exceptions import RedisError, ConnectionError as RedisConnectionConnectionError # Use exceptions from redis.exceptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisManager:
    """
    Manages asynchronous connections and operations with the Redis database.
    Leverages redis-py's asyncio client for async capabilities and connection pooling.
    """

    def __init__(self, redis_url: str, decode_responses: bool = True):
        """
        Initializes the Redis manager.

        Args:
            redis_url (str): The Redis connection string (e.g., "redis://localhost:6379/0").
                             Supports 'rediss://' for TLS.
            decode_responses (bool): If True, byte responses from Redis are decoded to UTF-8 strings.
        """
        self.redis_url = redis_url
        self.decode_responses = decode_responses
        self._redis_client: Optional[aioredis.Redis] = None # Change type hint
        logger.debug(f"RedisManager: Initializing with URL: {self.redis_url.split('@')[-1]} (password masked)")

    async def connect(self):
        """
        Establishes a connection to Redis.
        Should be called once, typically at application startup.
        """
        if self._redis_client:
            logger.warning("RedisManager: Connection already established. Skipping reconnect.")
            return

        try:
            # redis.asyncio.from_url automatically handles connection pooling
            self._redis_client = aioredis.from_url( # Use aioredis alias
                self.redis_url,
                encoding="utf-8",
                decode_responses=self.decode_responses,
                retry_on_timeout=True,
                health_check_interval=30 # Periodically check connection health
            )
            # Test connection
            await self._redis_client.ping()
            logger.debug("RedisManager: Successfully connected to Redis.")
        except RedisConnectionConnectionError as e: # Use corrected exception name
            logger.critical(f"RedisManager: Failed to connect to Redis: {e}")
            self._redis_client = None # Ensure client is None if connection fails
            raise
        except RedisError as e:
            logger.critical(f"RedisManager: An unexpected Redis error occurred during connect: {e}")
            self._redis_client = None
            raise
        except Exception as e:
            logger.critical(f"RedisManager: An unexpected error occurred during Redis connection: {e}")
            self._redis_client = None
            raise

    async def disconnect(self):
        """
        Closes the Redis connection pool.
        Should be called once, typically at application shutdown.
        """
        if self._redis_client:
            # Use aclose() for redis.asyncio clients
            await self._redis_client.aclose()
            self._redis_client = None
            logger.debug("RedisManager: Redis client connection closed.")
        else:
            logger.warning("RedisManager: No active connection to close.")

    async def _ensure_connected(self):
        """Internal method to ensure the Redis client is available."""
        if not self._redis_client:
            logger.warning("RedisManager: Redis client not initialized or connected. Attempting to connect...")
            await self.connect() # Attempt to reconnect if not already connected
        return self._redis_client

    # --- Basic Key-Value Operations ---

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        Sets a key-value pair in Redis.

        Args:
            key (str): The key to set.
            value (Any): The value to store. Can be str, int, float, bytes.
                         redis-py handles serialization for common types.
            ex (Optional[int]): Expiration time in seconds.

        Returns:
            bool: True if the key was set, False otherwise.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.set(key, value, ex=ex)
        except RedisError as e:
            logger.error(f"RedisManager: Error setting key '{key}': {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """
        Retrieves the value for a given key.

        Args:
            key (str): The key to retrieve.

        Returns:
            Optional[str]: The value as a string (if decode_responses is True), or None if key not found.
        """
        try:
            redis = await self._ensure_connected()
            value = await redis.get(key)
            return value
        except RedisError as e:
            logger.error(f"RedisManager: Error getting key '{key}': {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """
        Deletes one or more keys from Redis.

        Args:
            *keys (str): Variable number of keys to delete.

        Returns:
            int: The number of keys that were removed.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.delete(*keys)
        except RedisError as e:
            logger.error(f"RedisManager: Error deleting keys '{keys}': {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Checks if a key exists in Redis.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.exists(key) == 1
        except RedisError as e:
            logger.error(f"RedisManager: Error checking existence of key '{key}': {e}")
            return False

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increments the integer value of a key by the specified amount.
        If the key does not exist, it is set to 0 before performing the operation.

        Args:
            key (str): The key to increment.
            amount (int): The amount to increment by (default is 1).

        Returns:
            int: The value of key after the increment.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.incr(key, amount)
        except RedisError as e:
            logger.error(f"RedisManager: Error incrementing key '{key}': {e}")
            raise # Re-raise for callers to handle if increment fails

    async def decr(self, key: str, amount: int = 1) -> int:
        """
        Decrements the integer value of a key by the specified amount.
        If the key does not exist, it is set to 0 before performing the operation.

        Args:
            key (str): The key to decrement.
            amount (int): The amount to decrement by (default is 1).

        Returns:
            int: The value of key after the decrement.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.decr(key, amount)
        except RedisError as e:
            logger.error(f"RedisManager: Error decrementing key '{key}': {e}")
            raise # Re-raise for callers to handle if decrement fails

    # --- Hash Operations (for structured data like user profiles) ---

    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
            """
            Sets multiple field-value pairs in a hash.
            This is the preferred way to set multiple fields.

            Args:
                name (str): The name of the hash.
                mapping (Dict[str, Any]): A dictionary of field-value pairs to set.

            Returns:
                int: The number of fields that were *newly* set (0 if all existed, >0 if new fields).
            """
            if not mapping:
                logger.warning(f"RedisManager: hset called with empty mapping for hash '{name}'.")
                return 0
            try:
                redis = await self._ensure_connected()
                return await redis.hset(name, mapping=mapping)
            except RedisError as e:
                logger.error(f"RedisManager: Error setting hash fields in '{name}' with mapping {mapping}: {e}")
                return 0

    async def hget(self, name: str, key: str) -> Optional[str]:
        """
        Retrieves the value of a field from a hash.

        Args:
            name (str): The name of the hash.
            key (str): The field name within the hash.

        Returns:
            Optional[str]: The value of the field, or None if not found.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.hget(name, key)
        except RedisError as e:
            logger.error(f"RedisManager: Error getting hash field '{key}' from '{name}': {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, str]:
        """
        Retrieves all fields and values from a hash.

        Args:
            name (str): The name of the hash.

        Returns:
            Dict[str, str]: A dictionary of all fields and values in the hash.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.hgetall(name)
        except RedisError as e:
            logger.error(f"RedisManager: Error getting all fields from hash '{name}': {e}")
            return {}

    async def hdel(self, name: str, *keys: str) -> int:
        """
        Deletes one or more fields from a hash.

        Args:
            name (str): The name of the hash.
            *keys (str): Variable number of field names to delete.

        Returns:
            int: The number of fields that were removed.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.hdel(name, *keys)
        except RedisError as e:
            logger.error(f"RedisManager: Error deleting hash fields '{keys}' from '{name}': {e}")
            return 0

    # --- List Operations (for queues, recent activity, limited logs) ---

    async def lpush(self, key: str, *values: Any) -> int:
        """
        Inserts all the specified values at the head of the list stored at key.
        If key does not exist, it is created as empty list before pre-pending.

        Args:
            key (str): The list key.
            *values (Any): Values to push.

        Returns:
            int: The length of the list after the push operation.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.lpush(key, *values)
        except RedisError as e:
            logger.error(f"RedisManager: Error pushing to list '{key}': {e}")
            return 0

    async def rpush(self, key: str, *values: Any) -> int:
        """
        Inserts all the specified values at the tail of the list stored at key.

        Args:
            key (str): The list key.
            *values (Any): Values to push.

        Returns:
            int: The length of the list after the push operation.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.rpush(key, *values)
        except RedisError as e:
            logger.error(f"RedisManager: Error pushing to list '{key}': {e}")
            return 0

    async def lpop(self, key: str) -> Optional[str]:
        """
        Removes and returns the first element of the list stored at key.

        Args:
            key (str): The list key.

        Returns:
            Optional[str]: The element, or None if the list is empty.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.lpop(key)
        except RedisError as e:
            logger.error(f"RedisManager: Error popping from list '{key}': {e}")
            return None

    async def rpop(self, key: str) -> Optional[str]:
        """
        Removes and returns the last element of the list stored at key.

        Args:
            key (str): The list key.

        Returns:
            Optional[str]: The element, or None if the list is empty.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.rpop(key)
        except RedisError as e:
            logger.error(f"RedisManager: Error popping from list '{key}': {e}")
            return None

    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """
        Returns the specified elements of the list stored at key.

        Args:
            key (str): The list key.
            start (int): Start index (0-based).
            end (int): End index (0-based, -1 for last element).

        Returns:
            List[str]: A list of elements.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.lrange(key, start, end)
        except RedisError as e:
            logger.error(f"RedisManager: Error getting range from list '{key}': {e}")
            return []

    # --- Set Operations (for unique collections like features, roles, tracking members) ---

    async def sadd(self, key: str, *members: Any) -> int:
        """
        Adds the specified members to the set stored at key.

        Args:
            key (str): The set key.
            *members (Any): Members to add.

        Returns:
            int: The number of members that were actually added.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.sadd(key, *members)
        except RedisError as e:
            logger.error(f"RedisManager: Error adding to set '{key}': {e}")
            return 0

    async def srem(self, key: str, *members: Any) -> int:
        """
        Removes the specified members from the set stored at key.

        Args:
            key (str): The set key.
            *members (Any): Members to remove.

        Returns:
            int: The number of members that were removed from the set.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.srem(key, *members)
        except RedisError as e:
            logger.error(f"RedisManager: Error removing from set '{key}': {e}")
            return 0

    async def smembers(self, key: str) -> List[str]:
        """
        Returns all members of the set stored at key.

        Args:
            key (str): The set key.

        Returns:
            List[str]: A list of all members in the set.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.smembers(key)
        except RedisError as e:
            logger.error(f"RedisManager: Error getting members from set '{key}': {e}")
            return []

    async def sismember(self, key: str, member: Any) -> bool:
        """
        Returns if member is a member of the set stored at key.

        Args:
            key (str): The set key.
            member (Any): The member to check.

        Returns:
            bool: True if member is in the set, False otherwise.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.sismember(key, member)
        except RedisError as e:
            logger.error(f"RedisManager: Error checking member in set '{key}': {e}")
            return False

    # --- Expiration Operations ---

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Sets a timeout on key. After the timeout has expired, the key will automatically be deleted.

        Args:
            key (str): The key to set expiration for.
            seconds (int): The expiration time in seconds.

        Returns:
            bool: True if the timeout was set, False otherwise.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.expire(key, seconds)
        except RedisError as e:
            logger.error(f"RedisManager: Error setting expiration for '{key}': {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Returns the remaining time to live of a key that has a timeout.

        Args:
            key (str): The key to check TTL for.

        Returns:
            int: TTL in seconds, or -1 if the key exists but has no associated expire, or -2 if the key does not exist.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.ttl(key)
        except RedisError as e:
            logger.error(f"RedisManager: Error getting TTL for '{key}': {e}")
            return -2 # Indicate key not found in case of error

    # --- Pub/Sub Operations (for inter-process communication) ---

    async def publish(self, channel: str, message: Any) -> int:
        """
        Publishes a message to a given channel.

        Args:
            channel (str): The channel to publish to.
            message (Any): The message to publish.

        Returns:
            int: The number of clients that received the message.
        """
        try:
            redis = await self._ensure_connected()
            return await redis.publish(channel, message)
        except RedisError as e:
            logger.error(f"RedisManager: Error publishing to channel '{channel}': {e}")
            return 0

    async def subscribe(self, *channels: str) -> AsyncIterator[Any]:
        """
        Subscribes to one or more channels and yields messages.

        Args:
            *channels (str): Channels to subscribe to.

        Yields:
            Any: Messages received on the subscribed channels.
        """
        try:
            redis = await self._ensure_connected()
            # redis-py's pubsub is slightly different, requires explicit client acquisition
            pubsub = redis.pubsub()
            await pubsub.subscribe(*channels)
            logger.debug(f"RedisManager: Subscribed to channels: {channels}")
            async for message in pubsub.listen():
                if message and message['type'] == 'message':
                    # redis-py decodes message['data'] automatically if decode_responses=True
                    yield message['data']
            # Ensure pubsub connection is closed when the iterator is exhausted or loop exits
            await pubsub.close()
        except RedisError as e:
            logger.error(f"RedisManager: Error during Pub/Sub subscription or listening: {e}")
            # Re-raise for callers to handle if subscription fails
            raise
        finally:
            # Ensure the pubsub object is closed even if an exception occurs mid-listen
            if 'pubsub' in locals() and pubsub:
                await pubsub.close()

    # --- Transactions (Pipelines for atomic operations) ---

    def pipeline(self) -> aioredis.client.Pipeline: # Correct type hint
        """
        Returns a new pipeline object that can be used to chain commands.
        Commands are executed atomically.

        Returns:
            aioredis.client.Pipeline: A pipeline object.
        """
        if not self._redis_client:
            raise RuntimeError("RedisManager: Redis client not connected. Call .connect() first.")
        # pipeline method is directly on the client object
        return self._redis_client.pipeline()
    
    async def flush_all(self):
        try:
            redis = await self._ensure_connected()
            await redis.flushall(True)
        except RedisError as e:
            logger.error(f"RedisManager: Error during flush: {e}")
            # Re-raise for callers to handle if subscription fails
            raise