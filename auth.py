"""
auth.py — Lógica de autenticación con JWT
Actividad Unidad IV — Lenguaje de Programación (LPR07304)

Contiene:
    - hash_password / verify_password  -> manejo seguro de contraseñas (passlib + bcrypt)
    - create_token                     -> generación de JWT firmados (python-jose)
    - get_current_user                 -> dependencia que valida el token y devuelve el usuario
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
# En un proyecto real, SECRET_KEY debe venir de una variable de entorno,
# nunca quedar escrita en el código fuente.
SECRET_KEY = "clave-secreta-super-dificil-de-adivinar-123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Le dice a Swagger dónde está el endpoint de login para el botón "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ---------------------------------------------------------------------------
# Hashing de contraseñas
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña en texto plano contra su hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# "Base de datos" de usuarios en memoria (solo para esta actividad)
# ---------------------------------------------------------------------------
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
    },
    "estudiante1": {
        "username": "estudiante1",
        "hashed_password": hash_password("estudiante123"),
        "role": "estudiante",
    },
}


def get_user(username: str) -> Optional[dict]:
    return fake_users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Verifica usuario y contraseña. Devuelve el usuario o None si falla."""
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user


# ---------------------------------------------------------------------------
# Creación del token
# ---------------------------------------------------------------------------
def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT firmado con SECRET_KEY. Incluye 'exp' (expiración)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Obtener el usuario actual a partir del token (dependencia de FastAPI)
# ---------------------------------------------------------------------------
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodifica y valida el JWT recibido en el header Authorization.
    Lanza 401 si el token es inválido, expiró o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user
