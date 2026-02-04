from pydantic import BaseModel, ConfigDict

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str

    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    id: int
    total_amount: float
    status: str

    model_config = ConfigDict(from_attributes=True)