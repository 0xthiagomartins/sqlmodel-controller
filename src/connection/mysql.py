import logging, os
from sqlmodel import create_engine
import mysql.connector


def get_engine():
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASS")
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")
    name = os.environ.get("DB_NAME")
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{name}"
    return create_engine(db_uri)


def test_conn():
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASS")
    host = os.environ.get("DB_HOST")
    port = os.environ.get("DB_PORT")
    name = os.environ.get("DB_NAME")
    try:
        # Attempt to establish a connection to the database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=name,
        )

        if connection.is_connected():
            db_Info = connection.get_server_info()
            logging.info(f"Successfully connected to MySQL Server version {db_Info}")
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            logging.info(f"You're connected to database: {record}")

    except mysql.connector.Error as e:
        logging.info(f"Error while connecting to MySQL: {e}")

    finally:
        if (
            "connection" in locals()
            or "connection" in globals()
            and connection.is_connected()
        ):
            cursor.close()
            connection.close()
            logging.info("MySQL connection is closed")
