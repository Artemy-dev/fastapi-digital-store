from  fastapi import FastAPI
from app.api.products import router as product_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.cart import router as cart_router
from app.api.orders import router as orders_router

app = FastAPI()

app.include_router(health_router)
app.include_router(product_router)
app.include_router(users_router)
app.include_router(cart_router)
app.include_router(orders_router)