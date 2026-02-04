from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.db_session import get_db
from app.schemas.cart import GetCart, AddCart
from app.models import Cart, User, Product
from typing import List

router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=List[GetCart])
async def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_items = db.query(Cart).filter(Cart.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Корзина пуста")
    response = [
        GetCart(
            id=item.id,
            user_id=item.user_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price,
            total_price=item.quantity * item.product.price
        )
        for item in cart_items
    ]
    return response

@router.post("/", response_model=GetCart)
async def add_cart(cart_item: AddCart, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    # Проверяем, есть ли уже такой товар в корзине
    existing_item = db.query(Cart).filter(Cart.user_id == current_user.id, Cart.product_id == cart_item.product_id).first()

    if existing_item:
        existing_item.quantity += cart_item.quantity
        db.commit()
        db.refresh(existing_item)
        return GetCart(
            id=existing_item.id,
            user_id=existing_item.user_id,
            product_id=existing_item.product_id,
            quantity=existing_item.quantity,
            price=product.price
        )

    # Создаём новый элемент корзины
    new_item = Cart(
        user_id=current_user.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return GetCart(
        id=new_item.id,
        user_id=new_item.user_id,
        product_id=new_item.product_id,
        quantity=new_item.quantity,
        price=product.price,
        total_price=new_item.quantity * product.price
    )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart_item = db.query(Cart).filter(
        Cart.user_id == current_user.id,
        Cart.product_id == product_id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет товара в корзине")
    if cart_item.quantity > 1:   # если quantity > 1
        cart_item.quantity -= 1  # уменьшаем на 1
        db.commit()              # сохраняем
    else:                        # если quantity == 1
        db.delete(cart_item)     # полностью удаляем запись из таблицы
        db.commit()
