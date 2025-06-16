import logging
import json
import math
import os
from typing import Optional, Dict, Any, List, Union, Tuple
from classes.battle import Battle
from classes.item import Item
from classes.pokemon import Pokemon
from classes.pokemon_master import PokemonMaster
from classes.redis_manager import RedisManager
from classes.database_manager import DatabaseManager
from classes.user import User
from redis.exceptions import RedisError # Import RedisError for handling cache issues
import psycopg2 # Import psycopg2 for handling database specific errors
from dotenv import load_dotenv

load_dotenv() # This loads variables from .env into os.environ

# Configure logging for the storage manager
logger = logging.getLogger(__name__)
REDIS_PREFIX = os.getenv("REDIS_PREFIX")

class StorageManager:
    """
    Orchestrates storage and retrieval operations, leveraging Redis for caching
    and PostgreSQL for persistent storage. Implements a cache-aside strategy.
    """

    def __init__(self, redis_manager: RedisManager, database_manager: DatabaseManager):
        """
        Initializes the StorageManager with instances of RedisManager and DatabaseManager.

        Args:
            redis_manager (RedisManager): An initialized RedisManager instance.
            db_manager (DatabaseManager): An initialized DatabaseManager instance.
        """
        self.redis = redis_manager
        self.db = database_manager
        self.cache_ttl = 500 
        logger.debug("StorageManager: Initialized with Redis and Database managers.")

    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Internal helper to get data from Redis cache.
        Assumes data is stored as a Redis Hash.
        """
        try:
            # Redis stores data as bytes, self.redis.decode_responses should handle decoding
            data = await self.redis.hgetall(key)
            if data:
                logger.debug(f"StorageManager: Cache hit for key '{key}'.")
                # Convert string values from Redis to appropriate types if necessary
                # This basic conversion assumes simple JSON-like structures.
                # For complex types, you might need a more robust deserialization.
                # Example: trying to convert 'level' from string to int
                converted_data = {}
                for k, v in data.items():
                    try:
                        converted_data[k] = json.loads(v) if isinstance(v, str) and (v.startswith('{') or v.startswith('[')) else v
                    except json.JSONDecodeError:
                        converted_data[k] = v # Keep as string if not valid JSON
                return converted_data
            logger.debug(f"StorageManager: Cache miss for key '{key}'.")
            return None
        except RedisError as e:
            logger.warning(f"StorageManager: Error fetching from Redis cache for key '{key}': {e}")
            return None # Treat cache errors as a cache miss

    async def _set_to_cache(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Internal helper to set data to Redis cache.
        Stores data as a Redis Hash.
        """
        if not data:
            logger.debug(f"StorageManager: No data to set for cache key '{key}'.")
            return False
        try:
            # Convert values to strings for Redis HSET (or JSON strings for complex values)
            hset_data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()}
            result = await self.redis.hset(key, mapping=hset_data) # type: ignore
            if ttl:
                await self.redis.expire(key, ttl)
                logger.debug(f"StorageManager: Cache set for key '{key}' with TTL {ttl}s.")
            else:
                logger.debug(f"StorageManager: Cache set for key '{key}'.")
            return bool(result) # hset returns number of new fields, convert to bool
        except RedisError as e:
            logger.warning(f"StorageManager: Error setting to Redis cache for key '{key}': {e}")
            return False

    async def _invalidate_cache(self, key: str) -> bool:
        """Internal helper to invalidate data in Redis cache."""
        try:
            deleted_count = await self.redis.delete(key)
            if deleted_count > 0:
                logger.debug(f"StorageManager: Cache invalidated for key '{key}'.")
                return True
            return False
        except RedisError as e:
            logger.warning(f"StorageManager: Error invalidating Redis cache for key '{key}': {e}")
            return False
        
    async def get_user(self, user_id):
        cache_key = f"{REDIS_PREFIX}user_id:{user_id}"
        # 1. Try cache
        user_data = await self._get_from_cache(cache_key)
        if user_data:
            logger.info(f"StorageManager: Retrieved user data for {user_id} from cache with key: ({cache_key}).")
            return User.from_dict(user_data)
        # 2. Cache miss, try database
        logger.info(f"StorageManager: Cache miss for user data {user_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from users WHERE id = %(user_id)s"
            user_data = self.db.fetch_one(sql_query, {"user_id": user_id})
            if user_data:
                logger.info(f"StorageManager: Retrieved user data for {user_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, user_data, ttl=self.cache_ttl)
                return User.from_dict(user_data)
            logger.info(f"StorageManager: User data for {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting user profile {user_id}: {e}")
            return None # Return None or re-raise based on desired error handling

    async def save_object(self, obj, cache_key, table_name, unique_columns):
        obj_id = obj.id
        obj_data = obj.to_dict()
        try:
            rows_affected = self.db.upsert_data(
                table_name=table_name,
                unique_columns=unique_columns,
                data=obj_data
            )
            if rows_affected > 0:
                logger.debug(f"Storage Manager: Obj Data ({table_name}) for {obj_id} upserted")
                if cache_key:
                    await self._set_to_cache(cache_key, obj_data, self.cache_ttl)
                return True
            logger.warning(f"Storage Manager: Obj Data ({table_name}) for {obj_id} failed to save")
            return False 
        except psycopg2.Error as e:
            logger.error(f"Storage Manager: Obj Data ({table_name}) for {obj_id} failed to save")

    async def get_user_items(self, user):
        try:
            sql_query = "SELECT * from user_items WHERE user_id = %(user_id)s "
            item_data = await self.db.fetch_all(sql_query, {"user_id": user.id})
            result = []
            if len(item_data) > 0:
                for item in item_data:
                    result.append(Item.from_dict(item))
            return result
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Item Data for {user.id}: {e}")
            return None # Return None or re-raise based on desired error handling
        
    async def get_user_item_by_name(self, user, item_name):
        try:
            sql_query = f"SELECT * from user_items WHERE user_id = %(user_id)s and name = '{item_name}' "
            item_data = self.db.fetch_one(sql_query, {"user_id": user.id})
            return Item.from_dict(item_data)
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Item Data for {user.id}: {e}")
            return None # Return None or re-raise based on desired error handling
        
    async def get_user_pokemon_by_id(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}pokemon_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Pokemon Data for {pokemon_id} from cache.")
            return Pokemon.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Pokemon Data {pokemon_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from user_pokemon WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": pokemon_id})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return Pokemon.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Pokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling

    async def filter_user_pokemon(self, user_id, filter_string, order_by_string):
        try:
            sql_query = "SELECT * from user_pokemon WHERE user_id = %(user_id)s " + filter_string + order_by_string
            pokemon_data = self.db.fetch_all(sql_query, {"user_id": user_id})
            result = []
            for pokemon, i in zip(pokemon_data, range(pokemon_data.length)):
                pokemon['local_id'] = i
                new_pokemon = Pokemon.from_dict(pokemon)
                self.save_object(obj=new_pokemon, cache_key=None, table_name='user_pokemon', unique_columns=['id'])
                result.append(new_pokemon)
            return result
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Pokemon Data for {user_id}: {e}")
            return None # Return None or re-raise based on desired error handling
    
    async def list_pokemon(self, user, page=0, page_size=10):
        # Default filter and order, potentially overridden by user.filter and user.order_by
        default_filter = {
            'shiny': False,
            'type': [], # This refers to the 'types' array in DB - CORRECTLY INITIALIZED AS A LIST
            'name': '',
            'tier': 0,
            'level': 0,
            'nature': '',
            'region': '',
            'held_item': False #False means do not filter here, true means filter where held_item IS NOT NULL
        }
        default_order = {
            'pokedex': {'value': False, 'order': "ASC"}, # Maps to pokedex_id in DB
            'tier': {'value': False, 'order': "ASC"},
            'level': {'value': False, 'order': "ASC"},
        }

        # Use user's filter and order if available, otherwise use defaults
        # Ensure user.filter and user.order_by are dictionaries after deserialization
        current_filter = user.filter if isinstance(user.filter, dict) else default_filter
        current_order = user.order_by if isinstance(user.order_by, dict) else default_order


        filter_conditions = []
        params = {"user_id": user.id}

        # Build filter_string
        if current_filter.get('shiny') is True:
            filter_conditions.append("is_shiny = TRUE")

        # --- Adjusted string_fields processing ---
        # Special handling for 'types' (array) and 'name' (LIKE search)
        
        # Name: Use ILIKE for case-insensitive partial matching
        name_value = current_filter.get('name')
        if name_value:
            filter_conditions.append(f"name ILIKE %({'name'})s") # Use ILIKE for case-insensitive contains
            params['name'] = f"%{name_value.lower()}%" # Add wildcards

        # Types: Handle a list of types to check against the 'types' array column in DB
        type_values_list = current_filter.get('type') # 'type' is the filter key, now a list
        if type_values_list and isinstance(type_values_list, list) and len(type_values_list) > 0:
            # We want to find pokemon where ANY of the types in type_values_list
            # are present in the pokemon's 'types' array column.
            # This is commonly done with 'ANY' or '&&' (array overlap) in PostgreSQL.
            
            # Create a list of conditions for each type
            type_sub_conditions = []
            
            for idx, type_str in enumerate(type_values_list):
                param_name = f"type_{idx}" # Create unique parameter name for each type
                type_sub_conditions.append(f"%({param_name})s = ANY(types)")
                params[param_name] = type_str.lower() # Store the lowercase type value

            if type_sub_conditions:
                # Join individual type conditions with OR
                filter_conditions.append(f"({' OR '.join(type_sub_conditions)})")

        # Other simple string fields
        simple_string_fields = ['nature', 'region']
        for field in simple_string_fields:
            value = current_filter.get(field)
            if value: # Check if value is not empty string
                filter_conditions.append(f"{field} ILIKE %({field})s")
                params[field] = value.lower() # Assuming case-insensitive search or exact match

        numeric_fields = ['tier', 'level']
        for field in numeric_fields:
            value = current_filter.get(field)
            if value is not None and value > 0: # Check if value is provided and greater than 0
                filter_conditions.append(f"{field} = %({field})s")
                params[field] = value

        if current_filter.get('held_item') is True:
            filter_conditions.append("held_item_id IS NOT NULL") # Use held_item_id column

        # Construct the WHERE clause (used for both count and data fetch)
        where_clause = " WHERE user_id = %(user_id)s"
        if filter_conditions:
            where_clause += " AND " + " AND ".join(filter_conditions)

        # --- Calculate Total Records and Page Numbers ---
        count_sql_query = f"SELECT COUNT(*) as total_records FROM user_pokemon{where_clause}"
        total_records = int(self.db.fetch_one(count_sql_query, params)['total_records'])
        
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        
        # Adjust page if out of bounds
        if page < 0:
            page = 0
        elif page >= total_pages and total_pages > 0:
            page = total_pages - 1


        # Build order_string
        order_clauses = []
        # Define a desired order of preference for sorting
        order_preference = ['pokedex', 'tier', 'level'] # These are your filter/order keys

        for field_key in order_preference:
            order_data = current_order.get(field_key)
            if order_data and order_data.get('value') is True:
                db_column_name = field_key
                if field_key == 'pokedex': # Map 'pokedex' filter key to 'pokedex_id' column
                    db_column_name = 'pokedex_id'
                    
                order_type = order_data.get('order', "ASC").upper()
                if order_type not in ["ASC", "DESC"]:
                    order_type = "ASC" # Default to ASC if invalid
                order_clauses.append(f"{db_column_name} {order_type}")

        order_string = " ORDER BY " + ", ".join(order_clauses) if order_clauses else ""

        offset_string = f" OFFSET {page * page_size}"
        limit_string = f" LIMIT {page_size}"

        # Construct the final SQL query for fetching data
        sql_query = f"SELECT * FROM user_pokemon{where_clause}{order_string}{offset_string}{limit_string}"

        pokemon_data = await self.db.fetch_all(sql_query, params)
        
        result = []
        for pokemon in pokemon_data:
            result.append(Pokemon.from_dict(pokemon))
        
        return total_pages, result
    
    async def get_expired_battles(self):
        battles = await self.db.fetch_all("SELECT * FROM battles where status in ('active', 'joined') and end_time <= NOW()")
        result = []
        for battle in battles:
            result.append(Battle.from_dict(battle))
        return result
    
    async def get_battle_by_local_channel(self, local_id, channel_id):
        battle = self.db.fetch_one(f"SELECT * FROM battles where status in ('active', 'joined') and local_id = '{local_id}' and channel_id = '{channel_id}'")
        if battle:
            return Battle.from_dict(battle)
        return None
    
    async def get_battle_by_user(self, user_id):
        battle = self.db.fetch_one(f"SELECT * FROM battles where status in ('active', 'joined') and {user_id} = ANY(user_ids)")
        if battle:
            return Battle.from_dict(battle)
        return None
    
    async def delete_battle_by_id(self, battle_id):
        self.db.delete('battles', {'id': str(battle_id)})
        await self.redis.delete(f"{REDIS_PREFIX}battle_id:{battle_id}")
    
    async def delete_battle_pokemon_by_id(self, pokemon_id):
        self.db.delete('battle_pokemon', {'id': str(pokemon_id)})
        await self.redis.delete(f"{REDIS_PREFIX}battle_pokemon_id:{pokemon_id}")
    
    async def get_battle_pokemon_by_id(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}pokemon_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Battle Pokemon Data for {pokemon_id} from cache.")
            return Pokemon.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Battle Pokemon Data {pokemon_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from battle_pokemon WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": pokemon_id})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Battle Battle Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return Pokemon.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Battle Pokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Battle Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling
        
    async def get_pokemon_master_by_id(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}pokemon_master_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {pokemon_id} from cache.")
            return PokemonMaster.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Master Pokemon Data {pokemon_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from pokemon_master WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": pokemon_id})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return PokemonMaster.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Master Pokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Master Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling

    async def get_expired_raids(self):
        battles = await self.db.fetch_all("SELECT * FROM raids where status in ('active', 'joined') and end_time <= NOW()")
        result = []
        for battle in battles:
            result.append(Battle.from_dict(battle))
        return result
    
    async def get_raid_by_local_channel(self, local_id, channel_id):
        battle = self.db.fetch_one(f"SELECT * FROM raids where status in ('active', 'joined') and local_id = '{local_id}' and channel_id = '{channel_id}'")
        if battle:
            return Battle.from_dict(battle)
        return None
    
    async def get_raid_by_user(self, user_id):
        battle = self.db.fetch_one(f"SELECT * FROM raids where status in ('active', 'joined') and {user_id} = ANY(user_ids)")
        if battle:
            return Battle.from_dict(battle)
        return None
    
    async def delete_raid_by_id(self, battle_id):
        self.db.delete('raids', {'id': str(battle_id)})
        await self.redis.delete(f"{REDIS_PREFIX}battle_id:{battle_id}")
    
    async def delete_raid_pokemon_by_id(self, pokemon_id):
        self.db.delete('raid_pokemon', {'id': str(pokemon_id)})
        await self.redis.delete(f"{REDIS_PREFIX}raid_pokemon_id:{pokemon_id}")
    
    async def get_raid_pokemon_by_id(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}raid_pokemon_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Raid Pokemon Data for {pokemon_id} from cache.")
            return Pokemon.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Raid Pokemon Data {pokemon_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from raid_pokemon WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": pokemon_id})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Raid Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return Pokemon.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Raid Pokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Raid Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling
        
    async def get_raid_pokemon_master_by_id(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}raid_pokemon_master_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Master Raid Pokemon Data for {pokemon_id} from cache.")
            return PokemonMaster.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Master Raid Pokemon Data {pokemon_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from raid_pokemon_master WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": pokemon_id})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Master Raid Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return PokemonMaster.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Master RaidPokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Master Raid Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling

