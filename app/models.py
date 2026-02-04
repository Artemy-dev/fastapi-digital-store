from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"     # Пользователи
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)        # почта
    password_hash = Column(String(255), nullable=False)                         # хэш пароля для аутентификации
    is_admin = Column(Boolean, default=False)                                   # права админа (True/False), по умолчанию False
    cart_items = relationship("Cart", back_populates="user")
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"  # Каталог товаров
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)          # название
    description = Column(Text)                          # описание
    price = Column(Float, nullable=False)               # цена
    file_url = Column(String(1024), nullable=False)     # ссылка на скачивание
    cart_items = relationship("Cart", back_populates="product")

class Cart(Base):
    __tablename__ = "cart"      # Корзина
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)   # ID пользователя
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)         # ID товара
    quantity = Column(Integer, default=1)                                           # количество, по умолчанию 1
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"    # Заказы
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)   # ID пользователя
    total_amount = Column(Float, nullable=False)                        # сумма всех позиций из корзины
    status = Column(String(50), default="pending")                      # pending/paid/completed
    user = relationship("User", back_populates="orders")

class BlockedEmailDomain(Base):
    __tablename__ = "blocked_email_domains"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
