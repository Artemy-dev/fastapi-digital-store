from app.config import GOOGLE_CLIENT_ID
import urllib.parse
import aiohttp
from jose import jwt


# Функция generate_google_oauth_redirect_ur() создаёт URL для начала Google OAuth авторизации
# Пользователь переходит по этому URL, видит страницу входа в Google и подтверждения разрешений
# После успешного входа Google редиректит пользователя на redirect_uri с параметром 'code'

def generate_google_oauth_redirect_url():
    query_params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": "http://127.0.0.1:8000/users/login/google/callback",
        "response_type": "code",
        "scope": "openid email",
        # state:
    }
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    base_url = "https://accounts.google.com/o/oauth2/auth"
    return f"{base_url}?{query_string}"

async def verify_google_id_token(id_token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.googleapis.com/oauth2/v3/certs") as r:
            certs = await r.json()
    header = jwt.get_unverified_header(id_token)
    kid = header["kid"]
    key = next(k for k in certs["keys"] if k["kid"] == kid)
    payload = jwt.decode(
        id_token,
        key,
        algorithms=["RS256"],
        audience=GOOGLE_CLIENT_ID,
        issuer="https://accounts.google.com",
        options={
            "verify_exp": True,
            "verify_at_hash": False
        }
    )
    return payload