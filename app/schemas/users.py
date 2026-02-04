from pydantic import BaseModel, EmailStr, StringConstraints, ConfigDict
from typing import Optional, Annotated

class CreateUser(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=6)]

class LoginUser(BaseModel):
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=6)]

class UserInfo(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class GetUser(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)

class UpdateUser(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[Annotated[str, StringConstraints(min_length=6)]] = None

