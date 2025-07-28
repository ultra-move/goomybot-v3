import logging
import json
import math
import os
from typing import Optional, Dict, Any, List, Union, Tuple
from classes.battle import Battle
from classes.flex_log import FlexLog
from classes.item import Item
from classes.lottery import Lottery
from classes.move import Move
from classes.pokemon import Pokemon
from classes.pokemon_master import PokemonMaster
from classes.professor import Professor
from classes.quest import Quest
from classes.redis_manager import RedisManager
from classes.database_manager import DatabaseManager
from classes.trade import Trade
from classes.trainer_battle import TrainerBattle
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

    async def get_flex_log(self, user_id, channel, name):
        try:
            sql_query = "SELECT * from flex_log WHERE user_id = %(user_id)s and channel_id = %(channel)s and name = %(name)s and expiration_date >= now()"
            flex_entry = self.db.fetch_one(sql_query, {"user_id": user_id, 'channel': channel, 'name': name})
            if flex_entry:
                logger.info(f"StorageManager: Retrieved flex data for {user_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                return FlexLog.from_dict(flex_entry)
            logger.info(f"StorageManager: Flex data for {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting user profile {user_id}: {e}")
            return None # Return None or re-raise based on desired error handling

    async def get_evolutions(self, pokemon_id):
        sql_query = f'SELECT pm.* FROM public.pokemon_master AS pm WHERE pm.evolves_from_species_name = (SELECT name FROM public.pokemon_master WHERE id = {pokemon_id})'
        evolution_data = await self.db.fetch_all(sql_query)
        result = []
        for evolution in evolution_data:
            result.append(PokemonMaster.from_dict(evolution))
        return result
    
    async def get_all_users(self):
        sql_query = "SELECT * from users"
        user_data = await self.db.fetch_all(sql_query)
        result = []
        for user in user_data:
            result.append(User.from_dict(user))
        return result
            

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

    async def save_objects(self, objects: List[Any], cache_key_prefix: Optional[str], table_name: str, unique_columns: List[str]) -> bool:
        """
        Saves a list of objects to the database using a batch upsert operation.
        Optionally caches each object individually if a cache_key_prefix is provided.

        Args:
            objects (List[Any]): A list of objects (e.g., Move, Pokemon, LearnedBy instances)
                                 each having a 'to_dict()' method and an 'id' attribute.
            cache_key_prefix (Optional[str]): A prefix for the cache key. If provided,
                                               each object will be cached using
                                               f"{cache_key_prefix}:{obj.id}".
                                               If None, no caching is performed.
            table_name (str): The name of the database table to save the objects to.
            unique_columns (List[str]): A list of column names used to identify unique
                                        records for the upsert operation.

        Returns:
            bool: True if all objects were successfully processed, False otherwise.
        """
        if not objects:
            logger.info(f"Storage Manager: No objects provided for table '{table_name}'.")
            return True # Nothing to save, so consider it successful

        objects_data_for_db = []
        object_ids = []
        for obj in objects:
            try:
                obj_id = getattr(obj, 'id')
                obj_data = obj.to_dict()
                objects_data_for_db.append(obj_data)
                object_ids.append(obj_id)
            except AttributeError as e:
                logger.error(f"Storage Manager: Object in list is missing 'id' attribute or 'to_dict()' method: {e}")
                return False # Indicate failure if any object is malformed

        try:
            # Perform a single batch upsert operation
            rows_affected = self.db.batch_upsert_data(
                table_name=table_name,
                unique_columns=unique_columns,
                data=objects_data_for_db
            )

            if rows_affected > 0:
                logger.debug(f"Storage Manager: {rows_affected} records for table '{table_name}' upserted. IDs: {object_ids}")
                
                # Cache each object individually if cache_key_prefix is provided
                if cache_key_prefix:
                    for obj, obj_data in zip(objects, objects_data_for_db):
                        individual_cache_key = f"{cache_key_prefix}:{getattr(obj, 'id')}"
                        await self.cache._set_to_cache(individual_cache_key, obj_data, self.cache_ttl)
                    logger.debug(f"Storage Manager: {len(objects)} objects cached for table '{table_name}'.")
                return True
            else:
                logger.warning(f"Storage Manager: No records affected for table '{table_name}' during batch upsert. IDs: {object_ids}")
                return False
        except Exception as e: # Catch a more general Exception for database errors
            logger.error(f"Storage Manager: Batch upsert for table '{table_name}' failed for IDs {object_ids}: {e}", exc_info=True)
            return False


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

    async def get_user_pokemon_by_recent(self, user):
        try:
            sql_query = f"select * from user_pokemon where user_id = {user.id} ORDER BY created_at DESC LIMIT 1"
            pokemon_data = self.db.fetch_one(sql_query)
            if pokemon_data:
                return Pokemon.from_dict(pokemon_data)
            return None
        except psycopg2.Error as e:
            return None # Return None or re-raise based on desired error handling

    async def filter_user_pokemon(self, user_id, filter_string, order_by_string):
        try:
            sql_query = "SELECT * from user_pokemon WHERE user_id = %(user_id)s " + filter_string + order_by_string
            print(sql_query)
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

    async def get_missing_shiny_pokedex(self, user, page, pagesize):
        offset = (page) * pagesize

        sql_query = f"""
        SELECT pm.*
        FROM pokemon_master AS pm
        LEFT JOIN user_pokemon AS up ON
            pm.id = up.pokedex_id AND up.user_id = {user.id} AND up.is_shiny = TRUE
        WHERE up.pokedex_id IS NULL
        ORDER BY pm.id ASC
        LIMIT {pagesize} OFFSET {offset};
        """

        count_query = f"""
        SELECT COUNT(pm.id)
        FROM pokemon_master AS pm
        LEFT JOIN user_pokemon AS up ON
            pm.id = up.pokedex_id AND up.user_id = {user.id} AND up.is_shiny = TRUE
        WHERE up.pokedex_id IS NULL
        """

        # Execute the count query first
        total_count_result = self.db.fetch_one(count_query)['count']
        total_pages = math.ceil(total_count_result / pagesize) if pagesize > 0 else 0

        # Execute the main query
        records = await self.db.fetch_all(sql_query)
        return records, total_pages, total_count_result 

    async def get_missing_raid_pokedex(self, user, page, pagesize):
        offset = (page) * pagesize

        sql_query = f"""
        SELECT pm.*
        FROM raid_pokemon_master AS pm
        LEFT JOIN user_pokemon AS up
            ON pm.id = up.pokedex_id
            AND up.user_id = {user.id}
        WHERE up.pokedex_id IS NULL
        ORDER BY pm.id ASC
        LIMIT {pagesize} OFFSET {offset};
        """

        # You might also want to get the total count for pagination UI (e.g., "Page 1 of X")
        count_query = f"""
        SELECT COUNT(pm.id)
        FROM raid_pokemon_master AS pm
        LEFT JOIN user_pokemon AS up
            ON pm.id = up.pokedex_id
            AND up.user_id = {user.id}
        WHERE up.pokedex_id IS NULL;
        """

        # Execute the count query first
        total_count_result = self.db.fetch_one(count_query)['count']
        total_pages = math.ceil(total_count_result / pagesize) if pagesize > 0 else 0

        # Execute the main query
        records = await self.db.fetch_all(sql_query)
        return records, total_pages, total_count_result 

    async def list_pokemon(self, user, page=0, page_size=10):
        default_filter = {
            'shiny': False,
            'type': [],
            'name': '',
            'tier': 0,
            'level': 0,
            'nature': '',
            'region': '',
            'held_item': False
        }
        default_order = {
            'pokedex': {'value': False, 'order': "ASC"},
            'tier': {'value': False, 'order': "ASC"},
            'level': {'value': False, 'order': "ASC"},
            'recent': {'value': False, 'order': "DESC"},
            'created_at': {'value': False, 'order': "DESC"}
        }

        current_filter = user.filter if isinstance(user.filter, dict) else default_filter
        current_order = user.order_by if isinstance(user.order_by, dict) else default_order

        filter_conditions = []
        params = {"user_id": user.id}

        if current_filter.get('shiny') is True:
            filter_conditions.append("is_shiny = TRUE")

        name_value = current_filter.get('name')
        if name_value:
            filter_conditions.append("name ILIKE %(name)s")
            params['name'] = f"%{name_value.lower()}%"

        type_values = current_filter.get('type')
        if type_values:
            type_sub = []
            for idx, t in enumerate(type_values):
                pname = f"type_{idx}"
                type_sub.append(f"%({pname})s = ANY(types)")
                params[pname] = t.lower()
            filter_conditions.append(f"({' OR '.join(type_sub)})")

        for field in ['nature', 'region']:
            val = current_filter.get(field)
            if val:
                filter_conditions.append(f"{field} ILIKE %({field})s")
                params[field] = val.lower()

        for field in ['tier', 'level']:
            val = current_filter.get(field)
            if val and val > 0:
                filter_conditions.append(f"{field} = %({field})s")
                params[field] = val

        if current_filter.get('held_item') is True:
            filter_conditions.append("held_item_id IS NOT NULL")

        where_clause = " WHERE user_id = %(user_id)s"
        if filter_conditions:
            where_clause += " AND " + " AND ".join(filter_conditions)

        count_query = f"SELECT COUNT(*) as total FROM user_pokemon{where_clause}"
        total_records = int(self.db.fetch_one(count_query, params)['total'])
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        if page < 0:
            page = 0
        elif page >= total_pages and total_pages > 0:
            page = total_pages - 1

        order_clauses = []
        order_preference = ['pokedex', 'tier', 'level', 'created_at']  # only real DB columns
        for key in order_preference:
            od = current_order.get(key)
            if od and od['value'] is True:
                col = 'pokedex_id' if key == 'pokedex' else key
                direction = od['order'].upper() if od['order'] in ['ASC', 'DESC'] else "ASC"
                order_clauses.append(f"{col} {direction}")

        order_string = " ORDER BY " + ", ".join(order_clauses) if order_clauses else ""
        offset_string = f" OFFSET {page * page_size}"
        limit_string = f" LIMIT {page_size}"

        sql = f"SELECT * FROM user_pokemon{where_clause}{order_string}{offset_string}{limit_string}"
        print(sql)

        pokemon_data = await self.db.fetch_all(sql, params)
        result = [Pokemon.from_dict(p) for p in pokemon_data]

        return total_pages, result
    
    async def get_expired_battles(self):
        battles = await self.db.fetch_all("SELECT * FROM battles where status in ('active', 'joined') and end_time <= NOW()")
        result = []
        for battle in battles:
            result.append(Battle.from_dict(battle))
        return result
    
    async def get_expired_lottery(self):
        result = self.db.fetch_one("SELECT * FROM lottery where end_time <= NOW()")
        if result:
            return Lottery.from_dict(result)
        return None
    
    async def get_active_lottery(self):
        result = self.db.fetch_one("SELECT * FROM lottery where end_time >= NOW()")
        if result:
            return Lottery.from_dict(result)
        return None

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
    
    async def delete_lottery_by_id(self, lottery_id):
        self.db.delete('lottery', {'id': str(lottery_id)})
        await self.redis.delete(f"{REDIS_PREFIX}lottery_id:{lottery_id}")

    async def delete_battle_by_id(self, battle_id):
        self.db.delete('battles', {'id': str(battle_id)})
        await self.redis.delete(f"{REDIS_PREFIX}battle_id:{battle_id}")
    
    async def delete_battle_pokemon_by_id(self, pokemon_id):
        self.db.delete('battle_pokemon', {'id': str(pokemon_id)})
        await self.redis.delete(f"{REDIS_PREFIX}battle_pokemon_id:{pokemon_id}")
    
    async def delete_user_pokemon_by_id(self, pokemon_id):
        self.db.delete('user_pokemon', {'id': str(pokemon_id)})
        await self.redis.delete(f"{REDIS_PREFIX}pokemon_id:{pokemon_id}")
    
    async def delete_quest_by_id(self, quest_id):
        self.db.delete('quests', {'id': str(quest_id)})
        await self.redis.delete(f"{REDIS_PREFIX}quest_id:{quest_id}")

    async def delete_challenge_by_id(self, challenge_id):
        self.db.delete('professor_challenges', {'id': str(challenge_id)})
        await self.redis.delete(f"{REDIS_PREFIX}challenge_id:{challenge_id}")
    
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

    async def get_pokemon_master_by_name(self, name):
        cache_key = f"{REDIS_PREFIX}pokemon_master_data:{name}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {name} from cache.")
            return PokemonMaster.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Master Pokemon Data {name}. Fetching from DB.")
        try:
            sql_query = "SELECT * from pokemon_master WHERE name = %(pokemon_name)s ORDER BY ID"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_name": f"{name}"})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {name} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return PokemonMaster.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Master Pokemon Data for {name} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Master Pokemon Data {name}: {e}")
            return None # Return None or re-raise based on desired error handling

    async def get_raid_pokemon_master_by_name(self, name):
        cache_key = f"{REDIS_PREFIX}pokemon_master_data:{name}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {name} from cache.")
            return PokemonMaster.from_dict(pokemon_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Master Pokemon Data {name}. Fetching from DB.")
        try:
            sql_query = "SELECT * from raid_pokemon_master WHERE name = %(pokemon_name)s ORDER BY ID"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_name": f"{name}"})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Master Pokemon Data for {name} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, pokemon_data, ttl=self.cache_ttl)
                return PokemonMaster.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Master Pokemon Data for {name} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Master Pokemon Data {name}: {e}")
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
    
        
#===========================================TRADE FUNCTIONS===========================================        
    async def get_trade_by_id(self, trade_id):
        cache_key = f"{REDIS_PREFIX}trade_id:{trade_id}"
        # 1. Try cache
        trade_data = await self._get_from_cache(cache_key)
        if trade_data:
            logger.debug(f"StorageManager: Retrieved Trade for {trade_id} from cache.")
            return Trade.from_dict(trade_data)
        # 2. Cache miss, try database
        logger.debug(f"StorageManager: Cache miss for Trade {trade_id}. Fetching from DB.")
        try:
            sql_query = "SELECT * from trades WHERE id = %(trade_id)s"
            trade_data = self.db.fetch_one(sql_query, {"trade_id": trade_id})
            if trade_data:
                logger.debug(f"StorageManager: Retrieved Trade for {trade_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                await self._set_to_cache(cache_key, trade_data, ttl=self.cache_ttl)
                return Trade.from_dict(trade_data)
            logger.debug(f"StorageManager: Trade for {trade_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Master Raid Pokemon Data {trade_id}: {e}")
            return None # Return None or re-raise based on desired error handling
            
    async def get_trade_by_user_id(self, user_id: str): # Renamed 'user' to 'user_id' for clarity
        try:
            sql_query = f"""
                SELECT * FROM trades 
                WHERE (user1->>'user_id')::bigint = %(user_id)s OR (user2->>'user_id')::bigint = %(user_id)s and status = 'active'
            """
            trade_data = self.db.fetch_one(sql_query, {"user_id": user_id})
            
            if trade_data:
                logger.debug(f"StorageManager: Retrieved Trade for user {user_id} from DB.")
                return Trade.from_dict(trade_data)
            
            logger.debug(f"StorageManager: Trade for user {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Trade Data for user {user_id}: {e}")
            return None

    async def get_trade_by_user_id_local_id(self, user_id: str, local_id): # Renamed 'user' to 'user_id' for clarity
        try:
            sql_query = """
                SELECT * FROM trades 
                WHERE (user2->>'user_id')::bigint = %(user_id)s and local_id = %(local_id)s and status = 'started'
            """
            trade_data = self.db.fetch_one(sql_query, {"user_id": user_id, "local_id": local_id})
            
            if trade_data:
                logger.debug(f"StorageManager: Retrieved Trade for user {user_id} from DB.")
                return Trade.from_dict(trade_data)
            
            logger.debug(f"StorageManager: Trade for user {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Trade Data for user {user_id}: {e}")
            return None
        
    async def get_trade_by_user_id_active(self, user_id: str): # Renamed 'user' to 'user_id' for clarity
        try:
            sql_query = f"""
                SELECT * FROM trades 
                WHERE ((user1->>'user_id')::bigint = %(user_id)s OR (user2->>'user_id')::bigint = %(user_id)s ) and status = 'active'
            """
            trade_data = self.db.fetch_one(sql_query, {"user_id": user_id})
            
            if trade_data:
                logger.debug(f"StorageManager: Retrieved Trade for user {user_id} from DB.")
                return Trade.from_dict(trade_data)
            
            logger.debug(f"StorageManager: Trade for user {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Trade Data for user {user_id}: {e}")
            return None

    async def delete_trade_id(self, trade_id):
        self.db.delete('trades', {'id': str(trade_id)})
        await self.redis.delete(f"{REDIS_PREFIX}trade_id:{trade_id}")


#===================================================================================================
    async def get_active_professor(self, professor_id):
        try:
            sql_query = f"""
                Select * from professor_challenges where completed_by = 0
            """
            professor_data = self.db.fetch_one(sql_query)
            
            if professor_data:
                logger.debug(f"StorageManager: Retrieved professor for user {professor_id} from DB.")
                return Professor.from_dict(professor_data)
            
            logger.debug(f"StorageManager: professor for user {professor_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting professor Data for user {professor_id}: {e}")
            return None

    async def get_recent_challenge_full_reward(self, user_id):
        try:
            sql_query = f"""
                Select * from professor_challenges where completed_by = {user_id} and full_reward = true order by completed_time desc
            """
            professor_data = self.db.fetch_one(sql_query)
            if professor_data:
                logger.debug(f"StorageManager: Retrieved professor for user from DB.")
                return Professor.from_dict(professor_data)
            return None
        except psycopg2.Error as e:
            return None
                      
    async def get_recent_challenge(self, user_id, timestamp):
        try:
            sql_query = f"""
                Select * from professor_challenges where completed_by = {user_id} and completed_time >= %(completed_time)s order by completed_time desc
            """
            professor_data = self.db.fetch_one(sql_query, {"completed_time": timestamp})
            result = []
            if professor_data:
                logger.debug(f"StorageManager: Retrieved professor for user from DB.")
                return Professor.from_dict(professor_data)
            return None
        except psycopg2.Error as e:
            return None   
#==================================================================================================== 
    async def get_active_quest(self, user_id):
        try:
            sql_query = f"""
                Select * from quests where user_id = %(user_id)s and end_time >= now()
            """
            quest_data = self.db.fetch_one(sql_query, {"user_id": user_id})
            
            if quest_data:
                logger.debug(f"StorageManager: Retrieved Quest for user {user_id} from DB.")
                return Quest.from_dict(quest_data)
            
            logger.debug(f"StorageManager: Quest for user {user_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Quest Data for user {user_id}: {e}")
            return None        

    async def get_quest_complete(self, user_id, quest): # Changed to sync if fetch_one is sync
        try:
            pokedex_id = quest.condition.get('pokedex_id')
            if pokedex_id is None:
                logger.error("StorageManager: Quest condition missing 'pokedex_id'.")
                return False

            start_time = quest.start_time
            end_time = quest.end_time

            sql_query = """
                SELECT COUNT(*)
                FROM user_pokemon
                WHERE user_id = %s
                  AND pokedex_id = %s
                  AND created_at >= %s
                  AND created_at <= %s
                  AND original_user_id = %s;
            """
            params = (user_id, pokedex_id, start_time, end_time, user_id)
            
            logger.debug(f"Executing query with params: {params}") # More detailed logging
            result = self.db.fetch_one(sql_query, params)
            logger.debug(f"DB fetch_one result: {result}") # Log the exact result

            actual_count = result.get('count', 0) if isinstance(result, dict) else 0

            if actual_count > 0:
                logger.debug(f"StorageManager: Quest completed by user {user_id} for Pokedex ID {pokedex_id}. Pokemon found: {actual_count}.")
                return True
            
            logger.debug(f"StorageManager: Quest not yet completed by user {user_id} for Pokedex ID {pokedex_id}. No matching Pokemon found.")
            return False

        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error checking quest completion for user {user_id}: {e}")
            return False
        except Exception as e:
            # Be more specific with this catch, or remove it after debugging
            # If you still get this, it means something else entirely is going wrong
            logger.error(f"StorageManager: An unexpected error occurred in get_quest_complete for user {user_id}: {e}", exc_info=True) # exc_info to print traceback
            return False
        
    async def get_learnset(self, pokemon_id, page, page_size):
        offset = (page) * page_size
        sql_query = f"""
        select * from moves as m 
        inner join move_learned_by as l 
        on m.id = l.move_id 
        where l.pokemon_id = {pokemon_id} order by m.name
        LIMIT {page_size} OFFSET {offset};
        """
        count_query = f"SELECT COUNT(*) as total FROM move_learned_by where pokemon_id = {pokemon_id}"
        total_records = int(self.db.fetch_one(count_query)['total'])
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        result = await self.db.fetch_all(sql_query)
        if result:
            return total_pages, result 
        else:
            return None

    async def get_who_learns(self, move_name, page, page_size):
        offset = (page) * page_size
        sql_query = f"""
        select pokemon_name from move_learned_by where move_name = %(move_name)s
        ORDER BY pokemon_id
        LIMIT {page_size} OFFSET {offset};
        """
        count_query = f"SELECT COUNT(*) as total FROM move_learned_by where move_name = %(move_name)s"
        total_records = int(self.db.fetch_one(count_query, {'move_name': move_name})['total'])
        total_pages = math.ceil(total_records / page_size) if page_size > 0 else 0
        result = await self.db.fetch_all(sql_query, {'move_name': move_name})
        if result:
            return total_pages, result 
        else:
            return None

    async def get_moves_by_type(self, types):
        sql_query = f"""
        SELECT * from moves where type_name in %(types)s
        """
        result = await self.db.fetch_all(sql_query, params={'types': types})
        moves = []
        if result:
            for move in result:
                moves.append(Move.from_dict(move))
            return moves
        else:
            return None

    async def get_move_by_name(self, name):
        sql_query = f"""
        SELECT * from moves where name = %(name)s
        """
        result = self.db.fetch_one(sql_query, params={'name': name})
        if result:
            return Move.from_dict(result)
        else:
            return None 

    async def get_active_trainer_battle(self, user_id):
        cache_key = f"{REDIS_PREFIX}trainer_battle:{user_id}"
        # 1. Try cache
        battle_data = await self._get_from_cache(cache_key)
        if battle_data:
            logger.debug(f"StorageManager: Retrieved trainer Battle Data for {user_id} from cache.")
            return TrainerBattle.from_dict(battle_data)
        # 2. Cache miss, try database
        sql_query = f"""
        SELECT * from trainer_battles where user_id = {user_id}
        """
        result = self.db.fetch_one(sql_query)
        if result:
            return TrainerBattle.from_dict(result)
        else:
            return None

    async def get_trainer_battle_pokemon(self, pokemon_id):
        cache_key = f"{REDIS_PREFIX}trainer_pokemon_data:{pokemon_id}"
        # 1. Try cache
        pokemon_data = await self._get_from_cache(cache_key)
        if pokemon_data:
            logger.debug(f"StorageManager: Retrieved Trainer Battle Pokemon Data for {pokemon_id} from cache.")
            return Pokemon.from_dict(pokemon_data)
        try:
            sql_query = "SELECT * from trainer_battle_pokemon WHERE id = %(pokemon_id)s"
            pokemon_data = self.db.fetch_one(sql_query, {"pokemon_id": str(pokemon_id)})
            if pokemon_data:
                logger.debug(f"StorageManager: Retrieved Trainer Battle Pokemon Data for {pokemon_id} from DB.")
                # 3. Cache the result for next time (e.g., cache for 5 minutes)
                return Pokemon.from_dict(pokemon_data)
            logger.debug(f"StorageManager: Trainer Battle Pokemon Data for {pokemon_id} not found in DB.")
            return None
        except psycopg2.Error as e:
            logger.error(f"StorageManager: DB error getting Trainer Battle Pokemon Data {pokemon_id}: {e}")
            return None # Return None or re-raise based on desired error handling         

    async def delete_trainer_battle(self, user_id):
        sql_query = f"""
DELETE FROM trainer_battles
WHERE user_id = '{user_id}'
        """
        rows = await self.db.execute_delete_query(sql_query)
        await self.redis.delete(f"{REDIS_PREFIX}trainer_battle:{user_id}")
        return rows

    async def delete_trainer_battle_pokemon(self, pokemon_id):
        sql_query = f"""
DELETE FROM trainer_battle_pokemon
WHERE id = '{pokemon_id}'
        """
        rows = await self.db.execute_delete_query(sql_query)
        await self.redis.delete(f"{REDIS_PREFIX}trainer_pokemon_data:{pokemon_id}")
        return rows

#==================================================================================================== 
    async def get_leaderboard_stats(self):
        sql_query = """
WITH ShinyCounts AS (
    SELECT
        user_id,
        COUNT(*) AS shiny_count
    FROM
        user_pokemon
    WHERE
        is_shiny = TRUE
    GROUP BY
        user_id
),
PokemonCounts AS (
    SELECT
        user_id,
        COUNT(*) AS pokemon_count
    FROM
        user_pokemon
    GROUP BY
        user_id
),
FlexCounts AS (
    SELECT
        user_id,
        COUNT(*) AS flex_count
    FROM
        public.flex_log
    GROUP BY
        user_id
),
ItemUseCounts AS (
    SELECT
        user_id,
        SUM(uses) AS use_count
    FROM
        public.user_items
    GROUP BY
        user_id
)
SELECT
    u.name AS user_name,
    u.total_spent, 
    COALESCE(sc.shiny_count, 0) AS total_shiny_pokemon,
    COALESCE(pc.pokemon_count, 0) AS total_pokemon,
    COALESCE(fc.flex_count, 0) AS total_flex_entries,
    COALESCE(ic.use_count, 0) AS total_items_used
FROM
    users u
LEFT JOIN
    ShinyCounts sc ON u.id = sc.user_id
LEFT JOIN
    PokemonCounts pc ON u.id = pc.user_id
LEFT JOIN
    FlexCounts fc ON u.id = fc.user_id
LEFT JOIN
    ItemUseCounts ic ON u.id = ic.user_id;
    """
        result = await self.db.fetch_all(sql_query)

        # Convert the list of Row objects to a list of dictionaries for easier processing
        data = [dict(row) for row in result]

        leaderboard_results = []

        # Define the categories and their corresponding keys in the result dictionaries
        categories = {
            "Shiny Maniac": "total_shiny_pokemon",
            "Pokemon Hoarder": "total_pokemon",
            "Biggest Muscles": "total_flex_entries",
            "Loot Goblin": "total_items_used",
            "Big Spender": "total_spent"
        }

        for category_name, key in categories.items():
            if not data:
                # Handle the case where no data is returned
                leaderboard_results.append({
                    "category": category_name,
                    "user_name": "N/A",
                    "count": 0 # For monetary values, you might want 0.0 or a specific default
                })
                continue

            # Find the user with the maximum count for the current category
            # For 'total_spent', make sure it's treated as a numeric type (e.g., float or int)
            # Assuming total_spent is numeric (e.g., float or integer)
            top_user = max(data, key=lambda x: x[key] if x[key] is not None else 0)

            leaderboard_results.append({
                "category": category_name,
                "user_name": top_user["user_name"],
                "count": top_user[key]
            })

        return leaderboard_results
    
    async def delete_old_challenges(self):
        sql_query = f"""
DELETE FROM professor_challenges
WHERE completed_time < (NOW() - INTERVAL '4 hours');
        """
        rows = await self.db.execute_delete_query(sql_query)
        return rows
    

    async def delete_duplicates(self, user_id, buddy_id):
        sql_query = f"""
DELETE FROM public.user_pokemon
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            user_id,
            ROW_NUMBER() OVER (
                PARTITION BY user_id, pokedex_id, name
                ORDER BY (SELECT SUM(CAST(value AS INTEGER)) FROM jsonb_each_text(up_inner.iv)) DESC, id DESC -- Added id to ORDER BY for deterministic tie-breaking
            ) as rn
        FROM
            public.user_pokemon up_inner
        WHERE
            user_id = {int(user_id)}
            AND id <> '{buddy_id}'
            AND is_shiny = FALSE
            AND tier <> 4
            AND safe = FALSE
    ) AS subquery
    WHERE rn > 1
);
        """
        print(sql_query)
        rows = await self.db.execute_delete_query(sql_query)
        print(f"Rows affected: {rows}")
        return rows