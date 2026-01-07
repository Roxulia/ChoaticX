import mysql.connector
from mysql.connector.connection_cext import CMySQLConnection as connection
from mysql.connector.cursor_cext import CMySQLCursorDict as cursor
import os
import logging
from mysql.connector import Error
from dotenv import load_dotenv

class MySQLDB():
    _connection:connection|None = None
    _cursor:cursor|None = None
    _logger = None

    @staticmethod
    def init_logger(log_file="db.log"):
        load_dotenv()
        log_dir = os.getenv("LOG_PATH")
        file_path = os.path.join(log_dir, log_file)
    
        # ensure the log directory exists, not the file itself
        os.makedirs(log_dir, exist_ok=True)
        if MySQLDB._logger is None:
            MySQLDB._logger = logging.getLogger("DBLogger")
            MySQLDB._logger.setLevel(logging.DEBUG)

            # Create handlers
            c_handler = logging.StreamHandler()
            f_handler = logging.FileHandler(file_path,encoding="utf-8")

            c_handler.setLevel(logging.INFO)
            f_handler.setLevel(logging.DEBUG)

            # Format
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            c_handler.setFormatter(formatter)
            f_handler.setFormatter(formatter)

            # Add handlers
            MySQLDB._logger.addHandler(c_handler)
            MySQLDB._logger.addHandler(f_handler)

    @staticmethod
    def connect() -> tuple[connection,cursor]:
        if MySQLDB._connection is None or  not MySQLDB._connection.is_connected():
            load_dotenv()
            try:
                MySQLDB._connection = mysql.connector.connect(
                    host=os.getenv(key='DB_HOST'),
                    user=os.getenv(key='DB_USER'),
                    password=os.getenv(key='DB_PASSWORD'),
                    database=os.getenv(key='DB_NAME')
                )
                MySQLDB._cursor = MySQLDB._connection.cursor(dictionary=True)
                MySQLDB._logger.info("✅ Database connected")
            except Error as e:
                MySQLDB._logger.error(f"❌ Error: {e}")
        else:
        # make sure the connection didn't silently die
            try:
                MySQLDB._connection.ping(reconnect=True, attempts=3, delay=5)
            except Error as e:
                MySQLDB._logger.error(f"❌ Ping failed: {e}")
        return MySQLDB._connection, MySQLDB._cursor
    
    @staticmethod
    def execute(query, params=None, fetchone=False, fetchall=False, commit=False):
        conn, cur = MySQLDB.connect()
        try:
            MySQLDB._logger.debug(f"Executing: {query} | Params: {params}")
            cur.execute(query, params or [])
            
            if commit:
                conn.commit()
                MySQLDB._logger.info(f"✅ Query committed: {query}")
            
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
        except Exception as e:
            MySQLDB._logger.error(f"❌ Query Error: {e} | SQL: {query} | Params: {params}")
            return None
        finally:
            cur.close()
            conn.close()
