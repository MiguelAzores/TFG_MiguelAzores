from sqlmodel import Field, SQLModel, create_engine, Session, select, Relationship, Column
from pydantic.v1 import AnyUrl, validator
from typing import Optional, List
from datetime import datetime
import unidecode

DATABASE_URL = "sqlite:///clean_database.db"

class OrganoContratacion(SQLModel, table=True):
    __tablename__ = "OrganoContratacion"
    nombre: str|None = Field(default= None)
    id: int|None = Field(default= None, primary_key=True)
    nif: str|None = Field(default=None)
    url: str|None = Field(default=None)
    
    expedientes: list["Expediente"] = Relationship(back_populates="organo_struct")

    def __repr__(self) -> str:
        return f"<Organo de contratación = {self.nombre}, ID= {self.id}"

class Adjudicatario(SQLModel, table=True):
    __tablename__ = "Adjudicatario"
    internal_id: int|None = Field(default=None, primary_key=True)
    nombre: str|None = Field(default= None)
    nif: str|None = Field(default=None)
    url: str|None = Field(default=None)
    nombres_similares: Optional[str] = Field(default=None)  # Nuevo campo para nombres similares
    num_nombres_similares: int | None = Field(default=0)  # Nuevo campo para número de nombres similares
    
    lista_adjudicaciones: list["Expediente"] = Relationship(back_populates="adjudicatario_final")

    def __repr__(self) -> str:
        return f"<Adjudicatario = {self.nombre}, ID= {self.internal_id}"

class Expediente(SQLModel, table=True):
    __tablename__ = "Expediente"
    internal_id: int|None = Field(default=None, primary_key=True)
    timetrack: datetime = Field(default= datetime.now())
    fecha_anuncio: datetime|None = Field(default= None)
    nombre_exp: str|None = Field(default= None)
    route: str|None = Field(default= None)
    id_organo: int|None = Field(default= None, foreign_key="OrganoContratacion.id")
    organo_contratacion: str|None = Field(default= None)
    estado_lic: str|None = Field(default= None)
    objeto_contrato: str|None = Field(default= None)
    financiacion_UE: str|None = Field(default= None)
    presupuesto_sin_impuestos: float|None = Field(default= None)
    valor_estimado: float|None = Field(default= None)
    tipo_contrato: str|None = Field(default= None) # Ver qué opciones hay de hacerlo categorico
    codigo_CPV: str|None = Field(default= None)
    lugar_ejecucion: str|None = Field(default= None)
    sistema_contratacion: str|None = Field(default= None)
    procedimiento: str|None = Field(default= None) # Puede ser categorical
    tipo_tramitacion: str|None = Field(default= None) # Puede ser categorical
    metodo_presentacion: str|None = Field(default= None) # Puede ser categorical
    fecha_fin_oferta: datetime|None = Field(default= None)
    resultado: str|None = Field(default= None) # Puede ser categorical
    adjudicatario: str|None = Field(default= None, foreign_key="Adjudicatario.nombre")
    n_licitadores: int|None = Field(default= None)
    importe_adjudicacion: float|None = Field(default= None)
    fecha_fin_solicitud: datetime|None = Field(default= None)
    url: str|None = Field(default= None)

    organo_struct: Optional["OrganoContratacion"] = Relationship(back_populates="expedientes")
    adjudicatario_final: Optional["Adjudicatario"] = Relationship(back_populates="lista_adjudicaciones")

    @validator("*", pre=True, always=True)
    def convert_to_none(cls, value):
        if value == "" or value == "Ver detalle de la adjudicación":
            return None
        return value
    
    def __repr__(self) -> str:
        return f"<ID del expediente = {self.nombre_exp}, Estado de la licitación = {self.estado_lic}"
    
def connect_db(): 
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    return engine


if __name__ == "__main__":
    connect_db()