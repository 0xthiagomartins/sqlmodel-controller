import os, logging
from dotenv import load_dotenv
from sqlmodel import create_engine
import mysql.connector
import sqlite3
from pg8000.native import Connection as PgConnection
from pg8000.exceptions import DatabaseError, InterfaceError
from ssl import create_default_context


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
        db_uri = f"postgresql+pg8000://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['name']}"
    else:
        raise ValueError(f"Unsupported database type: {config['type']}")
    return create_engine(db_uri)


def test_conn():
    config = get_db_config()
    try:
        if config["type"] == "mysql":
            conn = mysql.connector.connect(
                host=config["host"],
                user=config["user"],
                password=config["password"],
                database=config["name"],
            )
        elif config["type"] == "sqlite":
            conn = sqlite3.connect(f"{config['name']}.db")
        elif config["type"] == "postgres":
            ssl_context = create_default_context()
            conn = PgConnection(
                user=config["user"],
                password=config["password"],
                host=config["host"],
                port=int(config["port"]),
                database=config["name"],
                ssl_context=ssl_context,
            )
        else:
            raise ValueError(f"Unsupported database type: {config['type']}")

        conn.close()
        return True
    except (DatabaseError, InterfaceError) as e:
        logging.error(f"PostgreSQL connection error: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Connection test failed: {str(e)}")
        return False
