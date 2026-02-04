from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db_session import get_db
from app.schemas.orders import OrderResponse, OrderListResponse
from app.models import Cart, User, Order
from typing import List

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Корзина пуста")
    total_amount = sum(item.quantity * item.product.price for item in cart_items)
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status="pending"
    )
    db.add(order)

    # очищаем корзину
    for item in cart_items:
        db.delete(item)
    db.commit()
    db.refresh(order)

    return order

@router.get("/", response_model=List[OrderListResponse])
async def get_order(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order_items = db.query(Order).filter(Order.user_id == current_user.id).all()
    if not order_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказов нет")
    return order_items