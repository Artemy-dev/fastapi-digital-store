from pydantic import BaseModel, ConfigDict, HttpUrl
from typing import Optional

class CreateProduct(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    file_url: HttpUrl

class GetProduct(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    file_url: HttpUrl

    model_config = ConfigDict(from_attributes=True)

class UpdateProduct(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    file_url: Optional[HttpUrl] = None