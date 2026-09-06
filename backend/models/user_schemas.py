from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):

    name: str

    email: EmailStr

    password: str


class UserLogin(BaseModel):

    email: EmailStr

    password: str


class UserUpdate(BaseModel):

    name: str

    email: EmailStr

    current_password: str = ""

    new_password: str = ""


class PasswordReset(BaseModel):

    email: EmailStr

    new_password: str