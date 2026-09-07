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
    CodeConversionRequest,
    CodeGenerationRequest
)


from backend.models.user_schemas import (
    UserRegister,
    UserLogin,
    UserUpdate,
    PasswordReset
)


from backend.services.code_converter import (
    convert_code,
    generate_code,
    GeminiRateLimitError,
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


def require_token(authorization: str = Header(None)):
    """Read a Bearer token and return its verified payload."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Login required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    payload = verify_access_token(token.strip())
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


# ==========================
# FRONTEND
# ==========================

@app.get("/")
def home():

    return FileResponse(
        "frontend/index.html"
    )


@app.get("/favicon.ico")
def favicon():
    return FileResponse(
        "backend/static/favicon.svg",
        media_type="image/svg+xml",
    )


@app.get("/converter")
def converter_page():
    return FileResponse("frontend/converter.html")


@app.get("/generate")
def generate_page():
    return FileResponse("frontend/generate.html")


@app.get("/profile")
def profile_page():
    return FileResponse("frontend/profile.html")


@app.get("/profile/forgot-password")
def forgot_password_page():
    return FileResponse("frontend/forgot-password.html")


@app.get("/api/profile")
def profile_api(authorization: str = Header(None)):
    payload = require_token(authorization)
    user = users_collection.find_one({"_id": payload.get("user_id")})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
    }


@app.put("/api/profile")
def update_profile(user_update: UserUpdate, authorization: str = Header(None)):
    payload = require_token(authorization)
    user = users_collection.find_one({"_id": payload.get("user_id")})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.new_password and not user_update.current_password:
        raise HTTPException(status_code=400, detail="Current password is required to set a new password")
    if user_update.new_password and not verify_password(user_update.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if user_update.new_password and len(user_update.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    duplicate = users_collection.find_one({"email": user_update.email})
    if duplicate and str(duplicate["_id"]) != str(user["_id"]):
        raise HTTPException(status_code=400, detail="Email is already registered")

    updates = {"name": user_update.name, "email": user_update.email}
    if user_update.new_password:
        updates["password"] = hash_password(user_update.new_password)
    try:
        users_collection.update_one({"_id": user["_id"]}, {"$set": updates})
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not update profile: {error}")

    return {"message": "Profile updated successfully", "name": user_update.name, "email": user_update.email}


@app.post("/api/forgot-password")
def forgot_password(reset: PasswordReset):
    if len(reset.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user = users_collection.find_one({"email": reset.email})
    if not user:
        raise HTTPException(status_code=404, detail="No account exists with that email address")

    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hash_password(reset.new_password)}},
    )
    return {"message": "Password changed successfully. You can now sign in."}


@app.get("/history-page")
def history_page():
    return FileResponse("frontend/history.html")


# ==========================
# REGISTER
# ==========================

@app.post("/register")
def register(user: UserRegister):
    try:
        existing_user = users_collection.find_one({"email": user.email})
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


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


    try:
        result = users_collection.insert_one(user_data)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


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
    try:
        existing_user = users_collection.find_one({"email": user.email})
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))


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

    payload = require_token(authorization)


    user_id = payload.get(
        "user_id"
    )


    try:
        conversion_result = convert_code(
            source_language=request.source_language,
            target_language=request.target_language,
            code=request.code,
        )
    except GeminiRateLimitError as error:
        raise HTTPException(
            status_code=429,
            detail=f"{error} Try again in about {error.retry_after_seconds} seconds.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error
    if isinstance(conversion_result, dict):
        converted_code = conversion_result.get("converted_code", "")
        explanation = conversion_result.get("explanation", "")
    else:
        converted_code = str(conversion_result)
        explanation = (
            f"The code was converted from {request.source_language} to "
            f"{request.target_language}."
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

        "explanation":
            explanation,

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
            converted_code,

        "explanation":
            explanation

    }


# ==========================
# HISTORY
# ==========================

@app.get("/history")
def history(

    authorization:
        str = Header(None)

):

    payload = require_token(authorization)


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

    payload = require_token(authorization)


    user_id = payload.get(
        "user_id"
    )


    result = (
        conversions_collection.delete_one(

            {

                "_id": conversion_id,

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

    payload = require_token(authorization)


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


# ==========================
# GENERATE CODE FROM PROMPT
# ==========================

@app.post("/generate")
def generate(
    request: CodeGenerationRequest,
    authorization: str = Header(None),
):
    payload = require_token(authorization)
    user_id = payload.get("user_id")

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Please describe the code you want to generate")
    try:
        generation_result = generate_code(prompt=request.prompt)
    except GeminiRateLimitError as error:
        raise HTTPException(
            status_code=429,
            detail=f"{error} Try again in about {error.retry_after_seconds} seconds.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error
    detected_language = generation_result.get("detected_language", "Unknown")
    generated_code = generation_result.get("converted_code", "")
    explanation = generation_result.get("explanation", "")

    result = conversions_collection.insert_one({
        "user_id": user_id,
        "source_language": "Prompt",
        "target_language": detected_language,
        "input_code": request.prompt,
        "converted_code": generated_code,
        "explanation": explanation,
        "created_at": datetime.utcnow(),
    })

    return {
        "message": "Code generated successfully",
        "conversion_id": str(result.inserted_id),
        "detected_language": detected_language,
        "converted_code": generated_code,
        "explanation": explanation,
    }