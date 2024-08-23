import logging
import os
from sqlmodel import create_engine
import mysql.connector
import sqlite3
import psycopg2
from dotenv import load_dotenv


def get_db_config():
    load_dotenv()
    return {
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASS"),
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
        "name": os.environ.get("DB_NAME"),
        "type": os.environ.get("DB_TYPE", "mysql"),
    }


def get_engine():
    config = get_db_config()
    if config["type"] == "mysql":
        db_uri = f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}"
    elif config["type"] == "sqlite":
        db_uri = f"sqlite:///{config['name']}.db"
    elif config["type"] == "postgres":
        db_uri = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}"
    else:
        raise ValueError(f"Unsupported database type: {config['type']}")
    return create_engine(db_uri)


def test_conn():
    config = get_db_config()
    connection = None
    cursor = None

    try:
        if config["type"] == "mysql":
            connection = mysql.connector.connect(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                database=config["name"],
            )
            if connection.is_connected():
                db_info = connection.get_server_info()
                logging.info(
                    f"Successfully connected to MySQL Server version {db_info}"
                )
        elif config["type"] == "sqlite":
            connection = sqlite3.connect(f"{config['name']}.db")
            logging.info("Successfully connected to SQLite database")
        elif config["type"] == "postgres":
            connection = psycopg2.connect(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                dbname=config["name"],
                port=config["port"],
            )
            if connection.status == psycopg2.extensions.STATUS_READY:
                logging.info("Successfully connected to PostgreSQL database")
        else:
            raise ValueError(f"Unsupported database type: {config['type']}")

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        record = cursor.fetchone()
        logging.info(f"Test query result: {record}")

    except (mysql.connector.Error, sqlite3.Error, psycopg2.Error) as e:
        logging.error(f"Error while connecting to database: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            if config["type"] == "mysql" and connection.is_connected():
                connection.close()
            elif config["type"] in ["sqlite", "postgres"]:
                connection.close()
            logging.info(f"{config['type'].capitalize()} connection is closed")
