from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db_session import get_db
from app.schemas.products import CreateProduct, GetProduct, UpdateProduct
from app.models import Product
from typing import List

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[GetProduct])
async def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товары не найдены")
    return products

@router.post("/", response_model=GetProduct)
async def create_product(products: CreateProduct,db: Session = Depends(get_db)):
    db_product = Product(
        name=products.name,
        description=products.description,
        price=products.price,
        file_url=str(products.file_url)  # конвертируем в str
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/{product_id}", response_model=GetProduct)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    db.delete(product)
    db.commit()

@router.patch("/{product_id}", response_model=GetProduct)
async def update_product(
    product_id: int,
    data: UpdateProduct,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "file_url":
            value = str(value)
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product