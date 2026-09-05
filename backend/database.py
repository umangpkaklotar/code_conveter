import os

from dotenv import load_dotenv

from pymongo import MongoClient


load_dotenv()


MONGODB_URL = os.getenv(
    "MONGODB_URL"
)


client = MongoClient(
    MONGODB_URL
)


db = client[
    "ai_code_converter"
]


# Users Collection

users_collection = db[
    "users"
]


# Conversions Collection

conversions_collection = db[
    "conversions"
]