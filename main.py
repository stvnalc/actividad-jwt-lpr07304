"""
main.py — Rutas de la API
Actividad Unidad IV — Lenguaje de Programación (LPR07304)

Endpoints:
    POST /login    -> autentica y devuelve un JWT
    GET  /publico  -> no requiere autenticación
    GET  /privado  -> requiere JWT válido (cualquier rol)
    GET  /admin    -> requiere JWT válido y rol == "admin"
"""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import authenticate_user, create_token, get_current_user

app = FastAPI(
    title="Actividad Unidad IV - Autenticación con JWT",
    description="POST /login, GET /publico, GET /privado, GET /admin",
)


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Recibe username y password (form-data, por eso funciona con el botón
    'Authorize' de Swagger) y devuelve un access_token si son correctos.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/publico")
def ruta_publica():
    """Ruta abierta: no pasa por get_current_user."""
    return {"mensaje": "Esta ruta es pública, no requiere autenticación."}


@app.get("/privado")
def ruta_privada(current_user: dict = Depends(get_current_user)):
    """Ruta protegida: cualquier usuario autenticado puede entrar."""
    return {
        "mensaje": f"Hola {current_user['username']}, estás autenticado.",
        "rol": current_user["role"],
    }


@app.get("/admin")
def ruta_admin(current_user: dict = Depends(get_current_user)):
    """Ruta protegida y restringida: solo usuarios con rol 'admin'."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador para acceder a esta ruta.",
        )
    return {"mensaje": f"Bienvenido admin {current_user['username']}."}
