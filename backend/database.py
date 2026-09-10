import os
import re
import threading

from dotenv import load_dotenv
from psycopg import connect
from psycopg.rows import dict_row


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_code_converter",
)
_connection = None
_initialized = False
_lock = threading.RLock()


def _get_connection():
    global _connection
    if _connection is None or _connection.closed:
        _connection = connect(DATABASE_URL, row_factory=dict_row)
    return _connection


def _initialize_database():
    global _initialized
    if _initialized:
        return

    with _lock:
        if _initialized:
            return
        connection = _get_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversions (
                id BIGSERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                source_language TEXT NOT NULL,
                target_language TEXT NOT NULL,
                input_code TEXT NOT NULL,
                converted_code TEXT NOT NULL,
                explanation TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL
            );
                """
            )
            cursor.execute(
                "ALTER TABLE conversions ADD COLUMN IF NOT EXISTS explanation "
                "TEXT NOT NULL DEFAULT ''"
            )
        connection.commit()
        _initialized = True


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class DatabaseCursor(list):
    def sort(self, key, direction):
        reverse = direction < 0
        return DatabaseCursor(sorted(self, key=lambda item: item.get(key), reverse=reverse))


class PostgreSQLCollection:
    def __init__(self, table_name):
        self.table_name = table_name

    def _where(self, query):
        clauses = []
        values = []
        for key, value in query.items():
            column = "id" if key == "_id" else key
            if column == "id" and isinstance(value, str) and value.isdigit():
                value = int(value)
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", column):
                raise ValueError(f"Invalid database column: {column}")
            clauses.append(f'"{column}" = %s')
            values.append(value)
        return (" AND ".join(clauses) or "1 = 1"), values

    @staticmethod
    def _row_to_dict(row):
        item = dict(row)
        item["_id"] = item.pop("id")
        return item

    def find_one(self, query):
        _initialize_database()
        where, values = self._where(query)
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where} LIMIT 1", values)
                row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def insert_one(self, document):
        _initialize_database()
        data = {key: value for key, value in document.items() if key != "_id"}
        columns = ", ".join(data)
        placeholders = ", ".join("%s" for _ in data)
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(
                    f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING id",
                    list(data.values()),
                )
                inserted_id = cursor.fetchone()["id"]
            _get_connection().commit()
        return InsertOneResult(inserted_id)

    def find(self, query):
        _initialize_database()
        where, values = self._where(query)
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE {where}", values)
                rows = cursor.fetchall()
        return DatabaseCursor(self._row_to_dict(row) for row in rows)

    def delete_one(self, query):
        _initialize_database()
        where, values = self._where(query)
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(
                    f"DELETE FROM {self.table_name} WHERE id = "
                    f"(SELECT id FROM {self.table_name} WHERE {where} LIMIT 1)",
                    values,
                )
                deleted_count = cursor.rowcount
            _get_connection().commit()
        return DeleteResult(deleted_count)

    def delete_many(self, query):
        _initialize_database()
        where, values = self._where(query)
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(f"DELETE FROM {self.table_name} WHERE {where}", values)
                deleted_count = cursor.rowcount
            _get_connection().commit()
        return DeleteResult(deleted_count)

    def update_one(self, query, updates):
        _initialize_database()
        where, where_values = self._where(query)
        fields = updates.get("$set", updates)
        assignments = ", ".join(f'"{key}" = %s' for key in fields)
        values = list(fields.values())
        with _lock:
            with _get_connection().cursor() as cursor:
                cursor.execute(
                    f"UPDATE {self.table_name} SET {assignments} WHERE {where}",
                    values + where_values,
                )
                updated_count = cursor.rowcount
            _get_connection().commit()
        return DeleteResult(updated_count)


users_collection = PostgreSQLCollection("users")
conversions_collection = PostgreSQLCollection("conversions")
history_collection = conversions_collection
