from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db_session import get_db
from app.cache_session import get_cache
from app.schemas.users import CreateUser, LoginUser, UserInfo, GetUser, UpdateUser
from app.models import User, BlockedEmailDomain
from app.auth.jwt import create_access_token, hash_password
from app.auth.dependencies import get_current_user
import bcrypt
import time

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserInfo)
async def create_user(user: CreateUser, db: Session = Depends(get_db)):

    # start = time.perf_counter()  # старт таймера

    user_exists = db.query(User).filter(User.email == user.email).first()  # Проверка на существующего пользователя
    if user_exists:
        raise HTTPException(status_code=400, detail=f"Пользователь с e-mail: {user.email} уже зарегистрирован")
    domain = str(user.email).split("@")[1]  # Получаем домен из email пользователя
    r = get_cache()  # Подключаемся к Redis
    cached_domains = r.smembers("blocked_email_domains")  # множество доменов
    if cached_domains:
        blocked_domains = {d.decode("utf-8") for d in cached_domains}
    else:
        # Сохраняем в Redis как множество
        blocked_domains = {d.domain.lower() for d in db.query(BlockedEmailDomain).all()}
        r.sadd("blocked_email_domains", *blocked_domains)
        r.expire("blocked_email_domains", 3600)

    # end = time.perf_counter()  # конец таймера
    # elapsed_ms = (end - start) * 1000
    # print(f"Register endpoint execution time: {elapsed_ms:.2f} ms")

    if domain in blocked_domains:  # Проверяем email в кэше
        raise HTTPException(status_code=400, detail="Регистрация с временными email запрещена")
    db_user = User(
        email=str(user.email),
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=UserInfo)
async def login_user(user: LoginUser, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Пользователь с e-mail: {user.email} не зарегистрирован")
    password = user.password.encode('utf-8')
    hashed_bytes_from_db = db_user.password_hash.encode('utf-8')
    if not bcrypt.checkpw(password, hashed_bytes_from_db):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный пароль")
    token = create_access_token({"user_id": db_user.id})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return db_user

@router.get("/me", response_model=GetUser)
async def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.delete("/me")
async def delete_me(response: Response, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.orders:
        raise HTTPException(400, "Нельзя удалить пользователя с заказами")
    db.delete(current_user)
    db.commit()
    response.delete_cookie("access_token")
    return {"detail": "Аккаунт успешно удалён"}

@router.patch("/me", response_model=GetUser)
async def update_me(user_update: UpdateUser, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    updated = False
    # Изменение email
    if user_update.email:
        email_exists = db.query(User).filter(User.email == user_update.email).first()
        if email_exists and email_exists.id != current_user.id:
            raise HTTPException(status_code=400, detail=f"Пользователь с e-mail {user_update.email} уже зарегистрирован")
        current_user.email = user_update.email
        updated = True
    # Изменение пароля
    if user_update.password:
        current_user.password_hash = hash_password(user_update.password)
        updated = True
    if updated:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return current_user

@router.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Вы вышли из системы"}
