from fastapi import FastAPI, HTTPException, Depends

from fastapi.security import OAuth2PasswordRequestForm

import psycopg

from database import crear_tablas, get_connection

from models import (
    TipoHurto,
    Hurto,
    UsuarioRegistro,
    Token
)

from auth import (
    hash_password,
    verify_password,
    crear_token,
    verificar_token,
    oauth2_scheme
)


app = FastAPI(
    title="API de Hurtos",
    description="API para gestionar tipos de hurto y denuncias de hurtos",
    version="1.0.0"
)


crear_tablas()


# =========================================================
# INICIO
# =========================================================

@app.get("/")
def inicio():

    return {
        "mensaje": "API de Hurtos funcionando"
    }


# =========================================================
# REGISTRO DE USUARIO
# =========================================================

@app.post("/registro")
def registrar_usuario(usuario: UsuarioRegistro):

    conn = get_connection()

    cursor = conn.cursor()

    password_hash = hash_password(
        usuario.password
    )

    try:

        cursor.execute(
            """
            INSERT INTO usuarios
            (username, password_hash)

            VALUES (%s, %s)

            RETURNING id
            """,
            (
                usuario.username,
                password_hash
            )
        )

        nuevo_id = cursor.fetchone()[0]

        conn.commit()

    except psycopg.errors.UniqueViolation:

        conn.rollback()

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="Ese nombre de usuario ya existe"
        )

    cursor.close()

    conn.close()

    return {
        "mensaje": "Usuario registrado",
        "id": nuevo_id
    }


# =========================================================
# LOGIN
# =========================================================

@app.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, password_hash

        FROM usuarios

        WHERE username = %s
        """,
        (
            form_data.username,
        )
    )

    user = cursor.fetchone()

    if not user:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas"
        )

    if not verify_password(
        form_data.password,
        user[2]
    ):

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas"
        )

    token = crear_token(
        data={
            "sub": user[1]
        }
    )

    cursor.close()

    conn.close()

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =========================================================
# TIPOS DE HURTO
# =========================================================

@app.post("/tipos-hurto")
def crear_tipo_hurto(
    tipo: TipoHurto,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tipo_hurto (nombre)

        VALUES (%s)

        RETURNING idTipo, nombre
        """,
        (
            tipo.nombre,
        )
    )

    resultado = cursor.fetchone()

    conn.commit()

    cursor.close()

    conn.close()

    return {
        "idTipo": resultado[0],
        "nombre": resultado[1]
    }


@app.get("/tipos-hurto")
def obtener_tipos_hurto(
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT idTipo, nombre

        FROM tipo_hurto

        ORDER BY idTipo
        """
    )

    resultados = cursor.fetchall()

    cursor.close()

    conn.close()

    return [
        {
            "idTipo": fila[0],
            "nombre": fila[1]
        }

        for fila in resultados
    ]


@app.get("/tipos-hurto/{idTipo}")
def obtener_tipo_hurto(
    idTipo: int,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT idTipo, nombre

        FROM tipo_hurto

        WHERE idTipo = %s
        """,
        (
            idTipo,
        )
    )

    resultado = cursor.fetchone()

    cursor.close()

    conn.close()

    if not resultado:

        raise HTTPException(
            status_code=404,
            detail="Tipo de hurto no encontrado"
        )

    return {
        "idTipo": resultado[0],
        "nombre": resultado[1]
    }


@app.put("/tipos-hurto/{idTipo}")
def actualizar_tipo_hurto(
    idTipo: int,
    tipo: TipoHurto,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tipo_hurto

        SET nombre = %s

        WHERE idTipo = %s

        RETURNING idTipo, nombre
        """,
        (
            tipo.nombre,
            idTipo
        )
    )

    resultado = cursor.fetchone()

    conn.commit()

    cursor.close()

    conn.close()

    if not resultado:

        raise HTTPException(
            status_code=404,
            detail="Tipo de hurto no encontrado"
        )

    return {
        "mensaje": "Tipo de hurto actualizado correctamente",
        "idTipo": resultado[0],
        "nombre": resultado[1]
    }


@app.delete("/tipos-hurto/{idTipo}")
def eliminar_tipo_hurto(
    idTipo: int,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT idTipo

        FROM tipo_hurto

        WHERE idTipo = %s
        """,
        (
            idTipo,
        )
    )

    resultado = cursor.fetchone()

    if not resultado:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Tipo de hurto no encontrado"
        )

    cursor.execute(
        """
        SELECT id

        FROM hurto

        WHERE idTipoHurto = %s

        LIMIT 1
        """,
        (
            idTipo,
        )
    )

    utilizado = cursor.fetchone()

    if utilizado:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el tipo de hurto porque tiene hurtos registrados"
        )

    cursor.execute(
        """
        DELETE FROM tipo_hurto

        WHERE idTipo = %s
        """,
        (
            idTipo,
        )
    )

    conn.commit()

    cursor.close()

    conn.close()

    return {
        "mensaje": "Tipo de hurto eliminado correctamente"
    }


# =========================================================
# HURTOS
# =========================================================

@app.post("/hurtos")
def crear_hurto(
    hurto: Hurto,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT idTipo

        FROM tipo_hurto

        WHERE idTipo = %s
        """,
        (
            hurto.idTipoHurto,
        )
    )

    tipo = cursor.fetchone()

    if not tipo:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="El tipo de hurto no existe"
        )

    cursor.execute(
        """
        INSERT INTO hurto (
            idTipoHurto,
            denunciante,
            direccion,
            fechaHurto
        )

        VALUES (%s, %s, %s, %s)

        RETURNING
            id,
            idTipoHurto,
            denunciante,
            direccion,
            fechaHurto,
            fechaRegistro
        """,
        (
            hurto.idTipoHurto,
            hurto.denunciante,
            hurto.direccion,
            hurto.fechaHurto
        )
    )

    resultado = cursor.fetchone()

    conn.commit()

    cursor.close()

    conn.close()

    return {
        "id": resultado[0],
        "idTipoHurto": resultado[1],
        "denunciante": resultado[2],
        "direccion": resultado[3],
        "fechaHurto": resultado[4],
        "fechaRegistro": resultado[5]
    }


@app.get("/hurtos")
def obtener_hurtos(
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            h.id,
            h.idTipoHurto,
            t.nombre,
            h.denunciante,
            h.direccion,
            h.fechaHurto,
            h.fechaRegistro

        FROM hurto h

        INNER JOIN tipo_hurto t
            ON h.idTipoHurto = t.idTipo

        ORDER BY h.id
        """
    )

    resultados = cursor.fetchall()

    cursor.close()

    conn.close()

    return [
        {
            "id": fila[0],
            "idTipoHurto": fila[1],
            "tipoHurto": fila[2],
            "denunciante": fila[3],
            "direccion": fila[4],
            "fechaHurto": fila[5],
            "fechaRegistro": fila[6]
        }

        for fila in resultados
    ]


@app.get("/hurtos/{id}")
def obtener_hurto(
    id: int,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            h.id,
            h.idTipoHurto,
            t.nombre,
            h.denunciante,
            h.direccion,
            h.fechaHurto,
            h.fechaRegistro

        FROM hurto h

        INNER JOIN tipo_hurto t
            ON h.idTipoHurto = t.idTipo

        WHERE h.id = %s
        """,
        (
            id,
        )
    )

    resultado = cursor.fetchone()

    cursor.close()

    conn.close()

    if not resultado:

        raise HTTPException(
            status_code=404,
            detail="Hurto no encontrado"
        )

    return {
        "id": resultado[0],
        "idTipoHurto": resultado[1],
        "tipoHurto": resultado[2],
        "denunciante": resultado[3],
        "direccion": resultado[4],
        "fechaHurto": resultado[5],
        "fechaRegistro": resultado[6]
    }


@app.put("/hurtos/{id}")
def actualizar_hurto(
    id: int,
    hurto: Hurto,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id

        FROM hurto

        WHERE id = %s
        """,
        (
            id,
        )
    )

    existe = cursor.fetchone()

    if not existe:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Hurto no encontrado"
        )

    cursor.execute(
        """
        SELECT idTipo

        FROM tipo_hurto

        WHERE idTipo = %s
        """,
        (
            hurto.idTipoHurto,
        )
    )

    tipo = cursor.fetchone()

    if not tipo:

        cursor.close()

        conn.close()

        raise HTTPException(
            status_code=404,
            detail="El tipo de hurto no existe"
        )

    cursor.execute(
        """
        UPDATE hurto

        SET
            idTipoHurto = %s,
            denunciante = %s,
            direccion = %s,
            fechaHurto = %s

        WHERE id = %s

        RETURNING
            id,
            idTipoHurto,
            denunciante,
            direccion,
            fechaHurto,
            fechaRegistro
        """,
        (
            hurto.idTipoHurto,
            hurto.denunciante,
            hurto.direccion,
            hurto.fechaHurto,
            id
        )
    )

    resultado = cursor.fetchone()

    conn.commit()

    cursor.close()

    conn.close()

    return {
        "mensaje": "Hurto actualizado correctamente",
        "id": resultado[0],
        "idTipoHurto": resultado[1],
        "denunciante": resultado[2],
        "direccion": resultado[3],
        "fechaHurto": resultado[4],
        "fechaRegistro": resultado[5]
    }


@app.delete("/hurtos/{id}")
def eliminar_hurto(
    id: int,
    token: str = Depends(oauth2_scheme)
):

    verificar_token(token)

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM hurto

        WHERE id = %s

        RETURNING id
        """,
        (
            id,
        )
    )

    resultado = cursor.fetchone()

    conn.commit()

    cursor.close()

    conn.close()

    if not resultado:

        raise HTTPException(
            status_code=404,
            detail="Hurto no encontrado"
        )

    return {
        "mensaje": "Hurto eliminado correctamente"
    }