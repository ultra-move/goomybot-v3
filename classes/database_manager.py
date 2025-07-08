import psycopg2
from psycopg2 import pool
from psycopg2 import sql
from psycopg2 import extras
from psycopg2.extras import DictCursor # Useful for getting dicts instead of tuples
import logging
from typing import Optional, List, Dict, Any, Union, Tuple

# Configure logging for the database manager
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages connections and operations with the PostgreSQL database.
    This class is database-specific and cache-agnostic.
    """
    def __init__(self, db_url: str, min_conn: int = 1, max_conn: int = 10):
        """
        Initializes the database manager with a connection pool.

        Args:
            db_url (str): The PostgreSQL connection string (e.g., "postgresql://user:pass@host:port/dbname").
            min_conn (int): Minimum number of connections in the pool.
            max_conn (int): Maximum number of connections in the pool.
        """
        self.db_url = db_url
        self.min_conn = min_conn
        self.max_conn = max_conn
        self._connection_pool = None
        self._initialize_connection_pool()

    def _initialize_connection_pool(self):
        """Initializes the psycopg2 connection pool."""
        try:
            self._connection_pool = pool.SimpleConnectionPool(
                self.min_conn,
                self.max_conn,
                self.db_url
            )
            logger.debug(f"DatabaseManager: Connection pool initialized with {self.min_conn}-{self.max_conn} connections.")
        except psycopg2.Error as e:
            logger.critical(f"DatabaseManager: Failed to initialize connection pool: {e}")
            raise

    def _get_connection(self):
        """Gets a connection from the pool."""
        try:
            return self._connection_pool.getconn() # type: ignore
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Failed to get connection from pool: {e}")
            raise

    def _release_connection(self, conn, rollback: bool = False):
        """Releases a connection back to the pool."""
        if conn:
            try:
                if rollback:
                    conn.rollback()
                else:
                    conn.commit() # Ensure commits on success, rollbacks on error
            except psycopg2.Error as e:
                logger.error(f"DatabaseManager: Error during commit/rollback on release: {e}")
            finally:
                self._connection_pool.putconn(conn) # type: ignore

    def close_pool(self):
        """Closes all connections in the pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.debug("DatabaseManager: Connection pool closed.")

    def fetch_one(self, sql_query: str, params: Optional[Union[Dict, Tuple]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes a SELECT query and fetches a single row.

        Args:
            sql_query (str): The SQL query string.
            params (Optional[Union[Dict, Tuple]]): Parameters for the query.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the row, or None if no row found.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql_query, params)
                result = cur.fetchone()
                return dict(result) if result else None # Convert Row object to dict
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error fetching one row: {e} | Query: {sql_query} | Params: {params}")
            self._release_connection(conn, rollback=True) # Rollback on error
            raise # Re-raise for higher layers to handle
        finally:
            self._release_connection(conn) # Release connection (commits if no error)

    async def fetch_all(self, sql_query: str, params: Optional[Union[Dict, Tuple]] = None) -> List[Dict[str, Any]]:
        """
        Executes a SELECT query and fetches all rows.

        Args:
            sql_query (str): The SQL query string.
            params (Optional[Union[Dict, Tuple]]): Parameters for the query.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a row.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql_query, params)
                results = cur.fetchall()
                return [dict(row) for row in results] # Convert Row objects to dicts
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error fetching all rows: {e} | Query: {sql_query} | Params: {params}")
            self._release_connection(conn, rollback=True)
            raise
        finally:
            self._release_connection(conn)

    def execute(self, sql_statement: str, params: Optional[Union[Dict, Tuple]] = None) -> int:
        """
        Executes an INSERT, UPDATE, or DELETE statement.

        Args:
            sql_statement (str): The SQL statement string.
            params (Optional[Union[Dict, Tuple]]): Parameters for the statement.

        Returns:
            int: The number of rows affected.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(sql_statement, params)
                return cur.rowcount
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error executing statement: {e} | Statement: {sql_statement} | Params: {params}")
            self._release_connection(conn, rollback=True)
            raise
        finally:
            self._release_connection(conn)

    def upsert_data(self, table_name: str, unique_columns: List[str], data: Dict[str, Any]) -> int:
        """
        Performs an UPSERT (INSERT or UPDATE) operation using PostgreSQL's ON CONFLICT.

        Args:
            table_name (str): The name of the table to upsert into.
            unique_columns (List[str]): A list of column names that define uniqueness
                                         (e.g., ['id'] for primary key, or ['user_id', 'item_id']).
            data (Dict[str, Any]): A dictionary where keys are column names and values are data to insert/update.

        Returns:
            int: The number of rows affected (1 for insert/update).
        """
        if not data:
            logger.warning(f"DatabaseManager: No data provided for upsert into {table_name}.")
            return 0

        # Prepare column names and values
        all_columns = list(data.keys())
        values_placeholder = sql.SQL(', ').join(sql.Placeholder() * len(all_columns))
        columns_sql = sql.SQL(', ').join(map(sql.Identifier, all_columns))

        # Prepare update clause for ON CONFLICT
        update_set_parts = []
        for col in all_columns:
            if col not in unique_columns: # Don't try to update unique columns themselves
                update_set_parts.append(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(col), sql.Identifier(col)))
        
        # If no non-unique columns to update, ensure something is done to trigger rowcount
        if not update_set_parts:
             # If only unique columns are provided, still want to update the row if it exists
             # A common pattern is to just update one of the unique columns with itself,
             # or use WHERE TRUE to ensure the ON CONFLICT clause updates the row
             # even if no non-unique columns are provided.
             # For this example, we'll assume there's always at least one non-unique column,
             # or we can add a dummy update.
             # Simpler: just use the data.items() for the update set, as ON CONFLICT UPDATE will handle it.
             update_set_parts = [sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(col), sql.Identifier(col)) for col in all_columns if col not in unique_columns]
             if not update_set_parts: # Fallback if only unique columns or no updatable columns
                update_set_parts.append(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(unique_columns[0]), sql.Identifier(unique_columns[0])))


        upsert_query = sql.SQL(
            "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}"
        ).format(
            sql.Identifier(table_name),
            columns_sql,
            values_placeholder,
            sql.SQL(', ').join(map(sql.Identifier, unique_columns)),
            sql.SQL(', ').join(update_set_parts)
        )
        
        # Correctly pass parameters as a tuple matching the order of all_columns
        params_tuple = tuple(data[col] for col in all_columns)

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(upsert_query, params_tuple)
                return cur.rowcount
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error upserting data: {e} | Table: {table_name} | Data: {data}")
            self._release_connection(conn, rollback=True)
            raise
        finally:
            self._release_connection(conn)
    
    def batch_upsert_data(self, table_name: str, unique_columns: List[str], data: List[Dict[str, Any]]) -> int:
        """
        Performs a batch UPSERT (INSERT or UPDATE) operation using PostgreSQL's ON CONFLICT
        and psycopg2.extras.execute_values for efficiency.

        Args:
            table_name (str): The name of the table to upsert into.
            unique_columns (List[str]): A list of column names that define uniqueness
                                        (e.g., ['id'] for primary key, or ['user_id', 'item_id']).
            data (List[Dict[str, Any]]): A list of dictionaries, where each dictionary
                                         represents a row to insert/update. All dictionaries
                                         are assumed to have the same keys.

        Returns:
            int: The total number of rows affected by the batch operation.

        Raises:
            ValueError: If the data list is empty or malformed.
            psycopg2.Error: If a database error occurs during the operation.
        """
        if not data:
            logger.info(f"DatabaseManager: No data provided for batch upsert into {table_name}.")
            return 0
        
        # Ensure all items in data are dictionaries
        if not all(isinstance(item, dict) for item in data):
            raise ValueError("DatabaseManager: All items in 'data' must be dictionaries.")

        # Get all column names from the first dictionary (assuming all dicts have same keys)
        all_columns = list(data[0].keys())
        columns_sql = sql.SQL(', ').join(map(sql.Identifier, all_columns))

        # Prepare update clause for ON CONFLICT
        update_set_parts = []
        for col in all_columns:
            if col not in unique_columns:
                update_set_parts.append(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(col), sql.Identifier(col)))

        # If no non-unique columns to update, use a dummy update to ensure rowcount is returned
        if not update_set_parts:
            if not unique_columns:
                raise ValueError("DatabaseManager: Cannot perform upsert without unique columns defined.")
            update_set_parts.append(sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(unique_columns[0]), sql.Identifier(unique_columns[0])))

        # Construct the SQL UPSERT statement using psycopg2.sql components
        upsert_query = sql.SQL(
            "INSERT INTO {} ({}) VALUES %s ON CONFLICT ({}) DO UPDATE SET {}"
        ).format(
            sql.Identifier(table_name),
            columns_sql,
            sql.SQL(', ').join(map(sql.Identifier, unique_columns)),
            sql.SQL(', ').join(update_set_parts)
        )
        
        # Prepare the values as a list of tuples, matching the order of 'all_columns'
        # This is the format required by execute_values
        values_to_insert = [[item[col] for col in all_columns] for item in data]

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Use execute_values for efficient batch insertion/upsertion
                # The 'page_size' parameter can be adjusted for performance
                extras.execute_values(cur, upsert_query, values_to_insert, page_size=1000)
                return cur.rowcount # Returns the number of rows actually inserted/updated
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error batch upserting data: {e} | Table: {table_name} | First Data Item: {data[0] if data else 'N/A'}")
            self._release_connection(conn, rollback=True)
            raise # Re-raise the exception after rollback
        finally:
            self._release_connection(conn)

# --- Deletion specific methods ---
    def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        Deletes rows from a table based on conditions.

        Args:
            table_name (str): The name of the table to delete from.
            conditions (Dict[str, Any]): A dictionary of column-value pairs for WHERE clause.
                                          e.g., {'user_id': 123, 'item_id': 'abc'}

        Returns:
            int: The number of rows deleted.
        """
        if not conditions:
            logger.warning("DatabaseManager: Delete operation attempted without conditions. This would delete ALL rows. Aborting.")
            return 0 # Or raise an error to prevent accidental full table delete

        where_clauses = []
        params = {}
        for i, (col, val) in enumerate(conditions.items()):
            param_name = f"cond_{i}" # Generate unique parameter names
            
            # --- FIX STARTS HERE ---
            # Correctly construct the named parameter placeholder:
            # 1. Use sql.Identifier(col) for the column name (which might need quoting).
            # 2. Use sql.SQL(f"%({param_name})s") to create a SQL fragment that contains
            #    the *literal* named parameter placeholder. This ensures psycopg2 looks
            #    for 'cond_0' in params, not '"cond_0"'.
            where_clauses.append(sql.SQL("{} = {}").format(
                sql.Identifier(col),
                sql.SQL(f"%({param_name})s")
            ))
            # --- FIX ENDS HERE ---
            
            params[param_name] = val
        
        delete_query = sql.SQL("DELETE FROM {} WHERE {}").format(
            sql.Identifier(table_name),
            sql.SQL(" AND ").join(where_clauses)
        )

        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(delete_query, params)
                return cur.rowcount
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error deleting data: {e} | Table: {table_name} | Conditions: {conditions}")
            self._release_connection(conn, rollback=True)
            raise # Re-raise the exception after logging and rollback
        finally:
            self._release_connection(conn)

     # --- New method for executing raw DELETE queries ---
    async def execute_delete_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Executes a raw DELETE SQL query. Use with caution for complex deletions.

        Args:
            query (str): The full DELETE SQL query string.
            params (Optional[Dict[str, Any]]): A dictionary of parameters for the query.
                                               (e.g., {'user_id_param': 123, 'buddy_id_param': 'uuid-value'})

        Returns:
            int: The number of rows deleted.
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                return cur.rowcount
        except psycopg2.Error as e:
            logger.error(f"DatabaseManager: Error executing custom DELETE query: {e} | Query: {query} | Params: {params}")
            self._release_connection(conn, rollback=True)
            raise # Re-raise the exception after logging and rollback
        finally:
            self._release_connection(conn)