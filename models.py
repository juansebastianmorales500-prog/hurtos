from pydantic import BaseModel
from datetime import date


class TipoHurto(BaseModel):

    nombre: str


class Hurto(BaseModel):

    idTipoHurto: int
    denunciante: str
    direccion: str
    fechaHurto: date


class UsuarioRegistro(BaseModel):

    username: str
    password: str


class Token(BaseModel):

    access_token: str
    token_type: str