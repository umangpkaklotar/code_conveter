import os

from datetime import datetime, timedelta

from dotenv import load_dotenv

from passlib.context import CryptContext

from jose import jwt, JWTError


load_dotenv()


JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)

JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        1440
    )
)


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):

    return pwd_context.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(data: dict):

    data_to_encode = data.copy()

    expire = (
        datetime.utcnow()
        +
        timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    data_to_encode.update(
        {
            "exp": expire
        }
    )

    token = jwt.encode(
        data_to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


def verify_access_token(token: str):

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ]
        )

        return payload

    except JWTError:

        return None