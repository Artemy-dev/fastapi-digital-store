from pydantic import BaseModel, ConfigDict
from typing import Optional

class GetCart(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    price: float            # цена за 1 штуку
    total_price: float      # итог = цена (price) * количество (quantity)

    model_config = ConfigDict(from_attributes=True)

class AddCart(BaseModel):
    product_id: int
    quantity: Optional[int] = 1

