import mysql.connector
import os
import logging
from mysql.connector import Error
from dotenv import load_dotenv

class MySQLDB():
    _connection = None
    _cursor = None
    _logger = None

    @staticmethod
    def init_logger(log_file="db.log"):
        if MySQLDB._logger is None:
            MySQLDB._logger = logging.getLogger("DBLogger")
            MySQLDB._logger.setLevel(logging.DEBUG)

            # Create handlers
            c_handler = logging.StreamHandler()
            f_handler = logging.FileHandler(log_file)

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
    def connect():
        if MySQLDB._connection is None:
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