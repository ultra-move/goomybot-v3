import logging
import json
import math
import os
from typing import Optional, Dict, Any, List, Union, Tuple
from classes.async_database_manager import AsyncDatabaseManager
from classes.battle import Battle
from classes.flex_log import FlexLog
from classes.item import Item
from classes.lottery import Lottery
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

    def __init__(self, redis_manager: RedisManager, database_manager: DatabaseManager, async_database_manager: AsyncDatabaseManager):
        """
        Initializes the StorageManager with instances of RedisManager and DatabaseManager.

        Args:
            redis_manager (RedisManager): An initialized RedisManager instance.
            db_manager (DatabaseManager): An initialized DatabaseManager instance.
        """
        self.redis = redis_manager
        self.db = database_manager
        self.async_db = async_database_manager
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

    async def get_missing_pokedex(self, user, page, pagesize):
        # Ensure page and pagesize are positive integers
        page = max(1, int(page))
        pagesize = max(1, int(pagesize))

        offset = (page - 1) * pagesize

        sql_query = f"""
        SELECT pm.*
        FROM pokemon_master AS pm
        LEFT JOIN user_pokemon AS up
            ON pm.id = up.pokedex_id
            AND up.user_id = {user.id}
        WHERE up.pokedex_id IS NULL
        ORDER BY pm.id ASC -- It's crucial to have an ORDER BY clause for consistent pagination
        LIMIT {pagesize} OFFSET {offset};
        """

        # You might also want to get the total count for pagination UI (e.g., "Page 1 of X")
        count_query = f"""
        SELECT COUNT(pm.id)
        FROM pokemon_master AS pm
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

    async def get_missing_raid_pokedex(self, user, page, pagesize):
        # Ensure page and pagesize are positive integers
        page = max(1, int(page))
        pagesize = max(1, int(pagesize))

        offset = (page - 1) * pagesize

        sql_query = f"""
        SELECT pm.*
        FROM raid_pokemon_master AS pm
        LEFT JOIN user_pokemon AS up
            ON pm.id = up.pokedex_id
            AND up.user_id = {user.id}
        WHERE up.pokedex_id IS NULL
        ORDER BY pm.id ASC -- It's crucial to have an ORDER BY clause for consistent pagination
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

    async def delete_duplicates(self, user_id, buddy_id):
        sql_query = f"""
DELETE FROM public.user_pokemon
WHERE id IN (
    SELECT id
    FROM (
        SELECT
            id,
            user_id,
            (SELECT SUM(CAST(value AS INTEGER)) FROM jsonb_each_text(up_inner.iv)) AS total_iv_sum,
            COUNT(*) OVER (PARTITION BY user_id, pokedex_id, name) AS duplicate_count,
            RANK() OVER (PARTITION BY user_id, pokedex_id, name ORDER BY (SELECT SUM(CAST(value AS INTEGER)) FROM jsonb_each_text(up_inner.iv)) DESC) AS iv_rank
        FROM
            public.user_pokemon up_inner
    ) AS subquery
    WHERE
        duplicate_count > 1
        AND iv_rank > 1
        AND user_id = {int(user_id)}
        AND id <> '{buddy_id}'
        AND is_shiny = FALSE
        AND tier <> 4
        AND safe = FALSE
);
        """
        print(sql_query)
        rows = await self.async_db.execute_delete_query(sql_query)
        print(f"Rows affected: {rows}")
        return rows