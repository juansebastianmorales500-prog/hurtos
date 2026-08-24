import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

# Si no encuentra la variable en Render, usa la clave por defecto
SECRET_KEY = os.getenv("SECRET_KEY", "mi_clave_super_secreta_sena_12345")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

# Corregido con el slash inicial para el Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def crear_token(data: dict) -> str:
    datos_a_modificar = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    datos_a_modificar.update({"exp": expire})
    
    token = jwt.encode(
        datos_a_modificar,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return token

def verificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )