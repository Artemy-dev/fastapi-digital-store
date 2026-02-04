from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db_session import get_db
from app.cache_session import get_cache
import redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/postgres")
async def postgres_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL service is unavailable"
        )
    return {"service": "postgres", "status": "ok"}

@router.get("/redis")
async def redis_check(cache=Depends(get_cache)):
    try:
        cache.ping()
    except redis.exceptions.RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service is unavailable"
        )
    return {"service": "redis", "status": "ok"}
