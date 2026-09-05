from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Header

from fastapi.responses import FileResponse

from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware


from datetime import datetime


from backend.database import (
    users_collection,
    conversions_collection
)


from backend.models.schemas import (
    CodeConversionRequest
)


from backend.models.user_schemas import (
    UserRegister,
    UserLogin
)


from backend.services.code_converter import (
    convert_code
)


from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token
)


app = FastAPI(
    title="AI Code Converter"
)


# ==========================
# STATIC FILES
# ==========================

app.mount(
    "/static",
    StaticFiles(
        directory="backend/static"
    ),
    name="static"
)


# ==========================
# CORS
# ==========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# HELPER FUNCTION
# ==========================

def get_current_user(
    authorization: str = Header(None)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Login required"
        )


    try:

        token = authorization.split(
            " "
        )[1]

    except:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


    user_id = payload.get(
        "user_id"
    )


    user = users_collection.find_one(
        {
            "_id": user_id
        }
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )


    return user


# ==========================
# FRONTEND
# ==========================

@app.get("/")
def home():

    return FileResponse(
        "frontend/index.html"
    )


# ==========================
# REGISTER
# ==========================

@app.post("/register")
def register(user: UserRegister):

    existing_user = (
        users_collection.find_one(
            {
                "email": user.email
            }
        )
    )


    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )


    hashed_password = (
        hash_password(
            user.password
        )
    )


    user_data = {

        "name":
            user.name,

        "email":
            user.email,

        "password":
            hashed_password,

        "created_at":
            datetime.utcnow()

    }


    result = (
        users_collection.insert_one(
            user_data
        )
    )


    return {

        "message":
            "User registered successfully",

        "user_id":
            str(
                result.inserted_id
            )

    }


# ==========================
# LOGIN
# ==========================

@app.post("/login")
def login(user: UserLogin):

    existing_user = (
        users_collection.find_one(
            {
                "email": user.email
            }
        )
    )


    if not existing_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    password_valid = (
        verify_password(
            user.password,
            existing_user["password"]
        )
    )


    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


    token = create_access_token(

        {

            "user_id":
                str(
                    existing_user["_id"]
                ),

            "email":
                existing_user["email"]

        }

    )


    return {

        "message":
            "Login successful",

        "token":
            token,

        "user": {

            "name":
                existing_user["name"],

            "email":
                existing_user["email"]

        }

    }


# ==========================
# PROFILE
# ==========================

@app.get("/profile")
def profile(

    authorization:
        str = Header(None)

):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Login required"
        )


    try:

        token = (
            authorization.split(
                " "
            )[1]
        )

    except:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get(
        "user_id"
    )


    from bson import ObjectId


    user = users_collection.find_one(

        {
            "_id":
                ObjectId(
                    user_id
                )
        }

    )


    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    return {

        "name":
            user["name"],

        "email":
            user["email"]

    }


# ==========================
# CONVERT CODE
# ==========================

@app.post("/convert")
def convert(

    request:
        CodeConversionRequest,

    authorization:
        str = Header(None)

):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Please login first"
        )


    token = authorization.split(
        " "
    )[1]


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get(
        "user_id"
    )


    converted_code = (
        convert_code(

            source_language=
                request.source_language,

            target_language=
                request.target_language,

            code=
                request.code

        )
    )


    conversion_data = {

        "user_id":
            user_id,

        "source_language":
            request.source_language,

        "target_language":
            request.target_language,

        "input_code":
            request.code,

        "converted_code":
            converted_code,

        "created_at":
            datetime.utcnow()

    }


    result = (
        conversions_collection.insert_one(
            conversion_data
        )
    )


    return {

        "message":
            "Code converted successfully",

        "conversion_id":
            str(
                result.inserted_id
            ),

        "converted_code":
            converted_code

    }


# ==========================
# HISTORY
# ==========================

@app.get("/history")
def history(

    authorization:
        str = Header(None)

):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Login required"
        )


    token = authorization.split(
        " "
    )[1]


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get(
        "user_id"
    )


    conversions = list(

        conversions_collection.find(

            {
                "user_id":
                    user_id
            }

        ).sort(
            "_id",
            -1
        )

    )


    history_data = []


    for item in conversions:

        item["_id"] = str(
            item["_id"]
        )


        if "created_at" in item:

            item["created_at"] = str(
                item["created_at"]
            )


        history_data.append(
            item
        )


    return {

        "data":
            history_data

    }


# ==========================
# DELETE ONE CONVERSION
# ==========================

@app.delete(
    "/history/{conversion_id}"
)
def delete_conversion(

    conversion_id:
        str,

    authorization:
        str = Header(None)

):

    from bson import ObjectId


    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Login required"
        )


    token = authorization.split(
        " "
    )[1]


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get(
        "user_id"
    )


    result = (
        conversions_collection.delete_one(

            {

                "_id":
                    ObjectId(
                        conversion_id
                    ),

                "user_id":
                    user_id

            }

        )
    )


    if result.deleted_count == 0:

        raise HTTPException(
            status_code=404,
            detail="Conversion not found"
        )


    return {

        "message":
            "Conversion deleted successfully"

    }


# ==========================
# CLEAR ALL HISTORY
# ==========================

@app.delete(
    "/history"
)
def clear_history(

    authorization:
        str = Header(None)

):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Login required"
        )


    token = authorization.split(
        " "
    )[1]


    payload = verify_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


    user_id = payload.get(
        "user_id"
    )


    result = (
        conversions_collection.delete_many(

            {
                "user_id":
                    user_id
            }

        )
    )


    return {

        "message":
            "History cleared successfully",

        "deleted_count":
            result.deleted_count

    }