import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(DATABASE_URL)


def crear_tablas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tipo_hurto (
            idTipo SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hurto (
            id SERIAL PRIMARY KEY,
            idTipoHurto INTEGER NOT NULL,
            denunciante VARCHAR(150) NOT NULL,
            direccion VARCHAR(200) NOT NULL,
            fechaHurto DATE NOT NULL,
            fechaRegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (idTipoHurto) REFERENCES tipo_hurto(idTipo)
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()