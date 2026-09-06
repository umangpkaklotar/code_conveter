from backend.database import DATABASE_PATH, users_collection


print(f"SQLite database: {DATABASE_PATH}")
print(f"Users stored: {len(users_collection.find({}))}")