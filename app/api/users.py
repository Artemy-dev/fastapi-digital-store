from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.db_session import get_db
from app.cache_session import get_cache
from app.schemas.users import CreateUser, LoginUser, UserInfo, GetUser, UpdateUser
from app.models import User, BlockedEmailDomain
from app.auth.jwt import create_access_token, hash_password
from app.auth.dependencies import get_current_user
import bcrypt
import time
from app.auth.oauth_google import generate_google_oauth_redirect_url, verify_google_id_token
from fastapi.responses import RedirectResponse
import aiohttp
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from jose import jwt

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
    if not db_user.password_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Этот аккаунт доступен только через Google")

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

@router.get("/login/google")  # редирект на Google OAuth
async def login_google(request: Request):
    uri = generate_google_oauth_redirect_url()
    return RedirectResponse(url=uri, status_code=status.HTTP_302_FOUND)

@router.get("/login/google/callback")  # приём code, обмен на токены, получение профиля, создание/поиск пользователя, установка JWT в cookie
async def login_google_callback(code: str, response: Response, db: Session = Depends(get_db)):
    google_token_url = "https://oauth2.googleapis.com/token"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=google_token_url,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": "http://127.0.0.1:8000/users/login/google/callback",
                "code": code,
            }
        ) as token_response:
            response_json = await token_response.json()
            # print(response_json)
            # Пример ответа: {'access_token': 'ya29.a0A...206', 'expires_in': 3599, 'scope': 'https://www.googleapis.com/auth/userinfo.email openid', 'token_type': 'Bearer', 'id_token': 'eyJ...-0Q'}
            id_token = response_json.get("id_token")
            if not id_token:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось получить id_token от Google")
            # Декодируем id_token для получения email
            payload = await verify_google_id_token(id_token)
            email = payload.get("email")
            email_verified = payload.get("email_verified", False)
            if not email or not email_verified:
                raise HTTPException(status_code=400, detail="Email не подтверждён Google")
            domain = str(email).split("@")[1]  # Получаем домен из email пользователя
            r = get_cache()  # Подключаемся к Redis
            cached_domains = r.smembers("blocked_email_domains")  # множество доменов
            if cached_domains:
                blocked_domains = {d.decode("utf-8") for d in cached_domains}
            else:
                # Сохраняем в Redis как множество
                blocked_domains = {d.domain.lower() for d in db.query(BlockedEmailDomain).all()}
                r.sadd("blocked_email_domains", *blocked_domains)
                r.expire("blocked_email_domains", 3600)
            if domain in blocked_domains:  # Проверяем email в кэше
                raise HTTPException(status_code=400, detail="Регистрация с временными email запрещена")
            db_user = db.query(User).filter(User.email == email).first()
            if not db_user:
                db_user = User(
                    email=str(email),
                    password_hash=""
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            token = create_access_token({"user_id": db_user.id})
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax"
            )
            return {"detail": "Успешный вход через Google", "user": {"id": db_user.id, "email": db_user.email}}

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
    if not current_user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="Этот аккаунт создан через Google, изменение email и пароля недоступно"
        )
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
        if not current_user.password_hash and len(user_update.password) < 6:
            raise HTTPException(status_code=400, detail="Пароль должен быть минимум 6 символов")
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
