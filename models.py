from pydantic import BaseModel
from datetime import date


class TipoHurto(BaseModel):
    nombre: str


class Hurto(BaseModel):
    idTipoHurto: int
    denunciante: str
    direccion: str
    fechaHurto: date