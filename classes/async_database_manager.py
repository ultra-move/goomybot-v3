import asyncpg
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncDatabaseManager:
    """
    Manages async connections and operations with the PostgreSQL database using asyncpg.
    Fully async and safe for asyncio applications.
    """

    def __init__(self, db_url: str, min_conn: int = 1, max_conn: int = 10):
        """
        Initializes the async database manager with a connection pool.

        Args:
            db_url (str): The PostgreSQL connection string.
            min_conn (int): Minimum number of connections in the pool.
            max_conn (int): Maximum number of connections in the pool.
        """
        self.db_url = db_url
        self.min_conn = min_conn
        self.max_conn = max_conn
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initializes the asyncpg connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.db_url,
                min_size=self.min_conn,
                max_size=self.max_conn
            )
            logger.debug(f"AsyncDatabaseManager: Connection pool initialized with {self.min_conn}-{self.max_conn} connections.")
        except Exception as e:
            logger.critical(f"AsyncDatabaseManager: Failed to initialize connection pool: {e}")
            raise

    async def close_pool(self):
        """Closes the asyncpg connection pool."""
        if self._pool:
            await self._pool.close()
            logger.debug("AsyncDatabaseManager: Connection pool closed.")

    async def fetch_one(self, sql_query: str, params: Optional[Union[Dict, tuple]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes a SELECT query and fetches a single row.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        async with self._pool.acquire() as conn:
            try:
                row = await conn.fetchrow(sql_query, *params) if params else await conn.fetchrow(sql_query)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error fetching one row: {e} | Query: {sql_query} | Params: {params}")
                raise

    async def fetch_all(self, sql_query: str, params: Optional[Union[Dict, tuple]] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and fetches all rows.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        async with self._pool.acquire() as conn:
            try:
                rows = await conn.fetch(sql_query, *params) if params else await conn.fetch(sql_query)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error fetching all rows: {e} | Query: {sql_query} | Params: {params}")
                raise

    async def execute(self, sql_statement: str, params: Optional[Union[Dict, tuple]] = None) -> int:
        """
        Executes an INSERT, UPDATE, or DELETE statement.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(sql_statement, *params) if params else await conn.execute(sql_statement)
                # asyncpg returns command tag like 'UPDATE 1', so extract affected rows
                rowcount = int(result.split()[-1])
                return rowcount
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error executing statement: {e} | Statement: {sql_statement} | Params: {params}")
                raise

    async def upsert_data(self, table_name: str, unique_columns: List[str], data: Dict[str, Any]) -> int:
        """
        Performs an UPSERT (INSERT or UPDATE) using ON CONFLICT.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        if not data:
            logger.warning(f"AsyncDatabaseManager: No data provided for upsert into {table_name}.")
            return 0

        all_columns = list(data.keys())
        placeholders = ', '.join(f"${i+1}" for i in range(len(all_columns)))
        columns_sql = ', '.join(all_columns)

        conflict_columns = ', '.join(unique_columns)
        update_set = ', '.join(f"{col} = EXCLUDED.{col}" for col in all_columns if col not in unique_columns)

        if not update_set:
            # Fallback to updating the first unique column to itself
            update_set = f"{unique_columns[0]} = EXCLUDED.{unique_columns[0]}"

        upsert_sql = f"""
            INSERT INTO {table_name} ({columns_sql})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_columns})
            DO UPDATE SET {update_set}
        """

        values = tuple(data[col] for col in all_columns)

        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(upsert_sql, *values)
                rowcount = int(result.split()[-1])
                return rowcount
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error upserting data: {e} | Table: {table_name} | Data: {data}")
                raise

    async def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        Deletes rows based on conditions.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        if not conditions:
            logger.warning("AsyncDatabaseManager: Delete operation attempted without conditions. Aborting to prevent full table deletion.")
            return 0

        where_clauses = []
        values = []
        for i, (col, val) in enumerate(conditions.items()):
            where_clauses.append(f"{col} = ${i+1}")
            values.append(val)

        delete_sql = f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)}"

        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(delete_sql, *values)
                rowcount = int(result.split()[-1])
                return rowcount
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error deleting data: {e} | Table: {table_name} | Conditions: {conditions}")
                raise

    async def execute_delete_query(self, query: str, params: Optional[Union[Dict, tuple]] = None) -> int:
        """
        Executes a raw DELETE SQL query.
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized.")

        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(query, *params) if params else await conn.execute(query)
                rowcount = int(result.split()[-1])
                return rowcount
            except Exception as e:
                logger.error(f"AsyncDatabaseManager: Error executing custom DELETE query: {e} | Query: {query} | Params: {params}")
                raise
