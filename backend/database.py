import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


DATABASE_PATH = Path(os.getenv("SQLITE_DB_PATH", "backend/ai_code_converter.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = Path.cwd() / DATABASE_PATH
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

_connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
_connection.row_factory = sqlite3.Row
_lock = threading.RLock()


def _initialize_database():
    with _lock:
        _connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                input_code TEXT NOT NULL,
                converted_code TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        _connection.commit()


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class SQLiteCursor(list):
    def sort(self, key, direction):
        reverse = direction < 0
        return SQLiteCursor(sorted(self, key=lambda item: item.get(key), reverse=reverse))


class SQLiteCollection:
    def __init__(self, table_name):
        self.table_name = table_name

    @staticmethod
    def _value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _where(self, query):
        clauses = []
        values = []
        for key, value in query.items():
            column = "id" if key == "_id" else key
            if column == "id" and isinstance(value, str) and value.isdigit():
                value = int(value)
            clauses.append(f"{column} = ?")
            values.append(self._value(value))
        return (" AND ".join(clauses) or "1 = 1"), values

    @staticmethod
    def _row_to_dict(row):
        item = dict(row)
        item["_id"] = item.pop("id")
        return item

    def find_one(self, query):
        where, values = self._where(query)
        with _lock:
            row = _connection.execute(
                f"SELECT * FROM {self.table_name} WHERE {where} LIMIT 1",
                values,
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def insert_one(self, document):
        data = {
            key: self._value(value)
            for key, value in document.items()
            if key != "_id"
        }
        columns = ", ".join(data)
        placeholders = ", ".join("?" for _ in data)
        with _lock:
            cursor = _connection.execute(
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
                list(data.values()),
            )
            _connection.commit()
        return InsertOneResult(cursor.lastrowid)

    def find(self, query):
        where, values = self._where(query)
        with _lock:
            rows = _connection.execute(
                f"SELECT * FROM {self.table_name} WHERE {where}",
                values,
            ).fetchall()
        return SQLiteCursor(self._row_to_dict(row) for row in rows)

    def delete_one(self, query):
        where, values = self._where(query)
        with _lock:
            cursor = _connection.execute(
                f"DELETE FROM {self.table_name} WHERE {where} LIMIT 1",
                values,
            )
            _connection.commit()
        return DeleteResult(cursor.rowcount)

    def delete_many(self, query):
        where, values = self._where(query)
        with _lock:
            cursor = _connection.execute(
                f"DELETE FROM {self.table_name} WHERE {where}",
                values,
            )
            _connection.commit()
        return DeleteResult(cursor.rowcount)


_initialize_database()

users_collection = SQLiteCollection("users")
conversions_collection = SQLiteCollection("conversions")
history_collection = conversions_collection
