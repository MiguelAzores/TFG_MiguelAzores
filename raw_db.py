from sqlmodel import SQLModel, Field, create_engine, Session, select
import datetime
from typing import List, Dict, Any, Optional
import scraping_params
import time
DATABASE_URL = "sqlite:///raw_database.db"

Municipio_Jerez = [
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=xO%2BVWYM1HLcQK2TEfXGy%2BA%3D%3D", # Aena. Dirección del Aeropuerto de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=AWzudWVfdurnSoTX3z%2F7wA%3D%3D", # C. Administración COMUJESA
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=uZeB9RW2UzkBPRBxZ4nJ%2Fg%3D%3D", # C. Administración MERCAJEREZ
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=isSUZ3Wb6qguf4aBO%2BvQlQ%3D%3D", # C.Administración Empresa Municipal de vivienda
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=mqwnEBYK3SoQK2TEfXGy%2BA%3D%3D", # C.Administración Parque Tecnológico Agroindustrial
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=7OhhaoN%2FfAWXQV0WE7lYPw%3D%3D", # Gerencia COMUJESA
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=RbpYQD4ZOZs%3D", # Gerencia Parque tecnológico Agroindustrial
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=8KXIej0TvMWXQV0WE7lYPw%3D%3D", # Gerencia MERCAJEREZ
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=XWw4npqzY9USugstABGr5A%3D%3D", # Gerencia Empresa Minucipal Vivienda
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=kL4JRvSx8lhvYnTkQN0%2FZA%3D%3D", # Gerencia FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=rah94wmkSOY%3D", # Junta Gobierno Local Ayuntamiento de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=Kl19yCF%2FEFOrz3GQd5r6SQ%3D%3D", # Patronato FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=6vcXcT%2BkwNerz3GQd5r6SQ%3D%3D", # Presidencia Asociación Desarrollo Rural de la Campiña
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=%2Fht1J5NkW8kuf4aBO%2BvQlQ%3D%3D", # Presidencia FUNDARTE
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=6EG3tH2QThurz3GQd5r6SQ%3D%3D", # Presidencia circuito de Jerez
        "https://contrataciondelestado.es/wps/poc?uri=deeplink:perfilContratante&idBp=67eFk%2FswtPUBPRBxZ4nJ%2Fg%3D%3D" # Presidencia COMUJESA
    ]

# Clase para almacenar todos los expedientes en crudo, tipo de datos SRT
class ExpedienteRaw(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    nombre: str
    url: str
    estado: str
    timetrack: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    fecha_anuncio: Optional[str] = None
    reciente: bool = Field(default=True)

    organo_contratacion: Optional[str] = None
    id_organo: Optional[str] = None
    Objeto_del_contrato: Optional[str] = None
    Financiacion_UE: Optional[str] = None
    Presupuesto_base_sin_impuestos: Optional[str] = None
    Valor_estimado: Optional[str] = None
    Tipo_de_Contrato: Optional[str] = None
    Codigo_CPV: Optional[str] = None
    Lugar_de_Ejecucion: Optional[str] = None
    Sistema_de_contratacion: Optional[str] = None
    Procedimiento_de_contratacion: Optional[str] = None
    Tipo_de_tramitacion: Optional[str] = None
    Metodo_de_presentacion: Optional[str] = None
    Fecha_fin_de_presentacion: Optional[str] = None
    Resultado: Optional[str] = None
    Adjudicatario: Optional[str] = None
    Num_de_Licitadores: Optional[str] = None
    Importe_de_Adjudicacion: Optional[str] = None
    Fecha_fin_de_solicitud: Optional[str] = None
    Html_page: Optional[bytes] = None

#Guarda nuevos expedientes en la base de datos.
def save_expedientes(db: Session, expedientes: List[Dict[str, Any]]):
    for exp in expedientes:
        expediente = ExpedienteRaw(
            nombre=exp["Nombre del expediente"],
            url=exp["url de descarga"],
            estado=exp["Estado de la Licitación"],
            timetrack=exp["Timetrack"],
            fecha_anuncio=exp["fecha_anuncio"],
            reciente=True,
            organo_contratacion = exp.get("Órgano de Contratación"),
            id_organo = exp.get("ID del Órgano de Contratación"),
            Objeto_del_contrato=exp.get("Objeto del contrato"),
            Financiacion_UE=exp.get("Financiación UE"),
            Presupuesto_base_sin_impuestos=exp.get("Presupuesto base de licitación sin impuestos"),
            Valor_estimado=exp.get("Valor estimado del contrato:"),
            Tipo_de_Contrato=exp.get("Tipo de Contrato:"),
            Codigo_CPV=exp.get("Código CPV"),
            Lugar_de_Ejecucion=exp.get("Lugar de Ejecución"),
            Sistema_de_contratacion=exp.get("Sistema de contratación"),
            Procedimiento_de_contratacion=exp.get("Procedimiento de contratación"),
            Tipo_de_tramitacion=exp.get("Tipo de tramitación"),
            Metodo_de_presentacion=exp.get("Método de presentación de la oferta"),
            Fecha_fin_de_presentacion=exp.get("Fecha fin de presentación de oferta"),
            Resultado=exp.get("Resultado"),
            Adjudicatario=exp.get("Adjudicatario"),
            Num_de_Licitadores=exp.get("Nº de Licitadores Presentados"),
            Importe_de_Adjudicacion=exp.get("Importe de Adjudicación"),
            Fecha_fin_de_solicitud=exp.get("Fecha fin de solicitud"),
            Html_page=exp.get("Página HTML")
        )
        db.add(expediente)  
    db.commit()  

# Marca el expediente con el mismo nombre como antiguo (reciente = False)
def mark_as_old(db: Session, nombre: str):
    statement = select(ExpedienteRaw).where(ExpedienteRaw.nombre == nombre, ExpedienteRaw.reciente == True)
    results = db.exec(statement)
    for expediente in results:
        expediente.reciente = False
    db.commit()  


#Verifica y actualiza la base de datos con nuevas cabeceras y descarga los datos completos de expedientes desactualizados
def check_and_update_db(args: Any, db: Session):    
    cabeceras_por_organo = scraping_params.collect_cabeceras(args)  # Recolecta cabeceras
    for org in cabeceras_por_organo:
        link = org[0]
        new_cabeceras = org[1]

        statement = select(ExpedienteRaw).where(ExpedienteRaw.reciente == True)
        stored_cabeceras = db.exec(statement).all()
        stored_dict = {exp.nombre: exp for exp in stored_cabeceras}

        non_updated_cabeceras = []
        for cab in new_cabeceras:
            nombre = cab["Nombre del expediente"]
            estado = cab["Estado de la Licitación"]
            timetrack = cab["Timetrack"]
            
            if nombre in stored_dict:
                stored_estado = stored_dict[nombre].estado
                if stored_estado != estado:
                    mark_as_old(db, nombre)  # Marca como antiguos los expedientes previos
                    non_updated_cabeceras.append(cab)  # Añade cabeceras no actualizadas a la lista
            else:
                non_updated_cabeceras.append(cab)  # Añade nuevas cabeceras a la lista

        if non_updated_cabeceras:
            driver = scraping_params.abrir_navegador(link, args)  # Abre el navegador para recopilar expedientes
            # Descarga todos los datos del expediente para cada cabecera no actualizada
            for cab in non_updated_cabeceras:
                time.sleep(1)
                exp_data = scraping_params.recopila_expedientes(driver, args, [cab])
                save_expedientes(db, exp_data)  # Guarda los datos del expediente en la base de datos
            driver.quit()


if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)
    args = scraping_params.read_params()  # Lee los argumentos de entrada
    if not args.links:
        args.links = Municipio_Jerez
        print(args.links)
    
    # Abre una sesión con la base de datos
    with Session(engine) as db:
        # Verifica y actualiza la base de datos
        check_and_update_db(args, db)
