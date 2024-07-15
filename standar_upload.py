from sqlmodel import Field, SQLModel, create_engine, Session, select, Relationship, Column, distinct
from pydantic.v1 import AnyUrl, validator
from typing import Optional
from datetime import datetime
import clean_db
import raw_db
import unidecode

# Transforma en un formato de fecha válido
def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip()
    print(date_str)
    # Prueba distintos formatos de fecha
    for date_format in ('%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            print("ERROR")
            return None
            continue
    raise ValueError(f"El formato '{date_str}' no es válido")

# Convierte el str en int
def parse_int(value: str, default: int = None) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# Convierte el str en float
def parse_float(value: str, default: float = None) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# Normaliza el nombre del adjudicatario
def normalize_string(input_string: str) -> str:
    if not input_string:
        return ""
    normalized_string = input_string.upper()
    #normalized_string = normalized_string.replace(',', ' ').replace('.', ' ')
    #normalized_string = unidecode.unidecode(normalized_string)
    #normalized_string = ' '.join(normalized_string.split())
    
    return normalized_string

# Añade los nuevos organos de contratación
def add_organos(session_clean: Session, session_raw: Session):
    statement = select(distinct(raw_db.ExpedienteRaw.id_organo))
    raw_organos = session_raw.exec(statement).all() # Lista de organos de la base de datos cruda
    statement = select(distinct(clean_db.OrganoContratacion.id))
    clean_organos = session_clean.exec(statement).all() # Lista de organos de la base de datos limpia

    int_raw_organos = []
    for i in raw_organos:
        int_raw_organos.append(parse_int(i))

    missing_organos = set(int_raw_organos) - set(clean_organos) # Lista de organos que faltan en la base limpia

    for m in missing_organos:
        statement = select(raw_db.ExpedienteRaw.organo_contratacion,raw_db.ExpedienteRaw.id_organo).where(raw_db.ExpedienteRaw.id_organo == m)
        organos_data = session_raw.exec(statement).first()
    
        miss_org = clean_db.OrganoContratacion(
                id=parse_int(organos_data.id_organo),
                nombre=organos_data.organo_contratacion
            )
        session_clean.add(miss_org)
    session_clean.commit()

# Añade los nuevos adjudicatarios
def add_adjudicatarios(session_clean: Session, session_raw: Session):
    statement = select(distinct(raw_db.ExpedienteRaw.Adjudicatario))
    raw_adj = session_raw.exec(statement).all() # Lista de Adjudicatarios en la base de datos cruda
    statement = select(distinct(clean_db.Adjudicatario.nombre))
    clean_adj = session_clean.exec(statement).all() # Lista de adjudicatarios en la base de datos limpia

    missing_adj = set(raw_adj) - set(clean_adj)

    for m in missing_adj:
        statement = select(raw_db.ExpedienteRaw.Adjudicatario).where(raw_db.ExpedienteRaw.Adjudicatario == m)
        adj_data = session_raw.exec(statement).first()
    
        miss_adj = clean_db.Adjudicatario(
                nombre = adj_data
            )
        session_clean.add(miss_adj)
    session_clean.commit()


# Función para transformar y guardar expedientes en la nueva base de datos
def transform_and_save_expedientes(session_clean: Session, session_raw: Session):
    # Selecciona los expedientes actualizados de la base de datos original
    statement = select(raw_db.ExpedienteRaw).where(raw_db.ExpedienteRaw.reciente == True)
    expedientes_actualizados = session_raw.exec(statement).all()
    
    for exp in expedientes_actualizados:
        # Comprobar si el expediente ya existe en la base de datos estandarizada
        statement = select(clean_db.Expediente).where(clean_db.Expediente.nombre_exp == exp.nombre)
        existing_exp = session_clean.exec(statement).first()
        
        # Transformar los datos al formato de la nueva base de datos
        try:
            tipo_contrato = exp.Tipo_de_Contrato if exp.Tipo_de_Contrato else None
        except ValueError:
            tipo_contrato = "nule"

        if existing_exp:
            # Comparar las fechas de "timetrack" para ver cuál es más reciente
            if existing_exp.timetrack < exp.timetrack:
                # Actualizar la entrada existente
                existing_exp.route = exp.url
                existing_exp.estado_lic = exp.estado
                existing_exp.organo_contratacion = exp.organo_contratacion
                existing_exp.fecha_anuncio = parse_date(exp.fecha_anuncio)
                existing_exp.id_organo = parse_int(exp.id_organo)
                existing_exp.objeto_contrato = exp.Objeto_del_contrato
                existing_exp.financiacion_UE = exp.Financiacion_UE
                existing_exp.presupuesto_sin_impuestos = parse_float(exp.Presupuesto_base_sin_impuestos)
                existing_exp.valor_estimado = parse_float(exp.Valor_estimado)
                existing_exp.tipo_contrato = tipo_contrato
                existing_exp.codigo_CPV = exp.Codigo_CPV
                existing_exp.lugar_ejecucion = exp.Lugar_de_Ejecucion
                existing_exp.sistema_contratacion = exp.Sistema_de_contratacion
                existing_exp.procedimiento = exp.Procedimiento_de_contratacion
                existing_exp.tipo_tramitacion = exp.Tipo_de_tramitacion
                existing_exp.metodo_presentacion = exp.Metodo_de_presentacion
                existing_exp.fecha_fin_oferta = parse_date(exp.Fecha_fin_de_presentacion)
                existing_exp.resultado = exp.Resultado
                existing_exp.adjudicatario = exp.Adjudicatario
                existing_exp.n_licitadores = parse_int(exp.Num_de_Licitadores)
                existing_exp.importe_adjudicacion = parse_float(exp.Importe_de_Adjudicacion)
                existing_exp.fecha_fin_solicitud = parse_date(exp.Fecha_fin_de_solicitud)
                existing_exp.url = exp.url

                print("-- ACTUALIZA UN EXPEDIENTE")
                session_clean.add(existing_exp)  # Añadir el expediente actualizado a la sesión
                session_clean.commit()
        else:
            # Insertar un nuevo expediente
            print("-- INSERTA NUEVO EXPEDIENTE")
            nuevo_expediente = clean_db.Expediente(
                nombre_exp=exp.nombre,
                route=exp.url,
                estado_lic=exp.estado,
                fecha_anuncio=parse_date(exp.fecha_anuncio),
                organo_contratacion = exp.organo_contratacion,
                id_organo = parse_int(exp.id_organo),
                objeto_contrato=exp.Objeto_del_contrato,
                financiacion_UE=exp.Financiacion_UE,
                presupuesto_sin_impuestos=parse_float(exp.Presupuesto_base_sin_impuestos),
                valor_estimado=parse_float(exp.Valor_estimado),
                tipo_contrato=tipo_contrato,
                codigo_CPV=exp.Codigo_CPV,
                lugar_ejecucion=exp.Lugar_de_Ejecucion,
                sistema_contratacion=exp.Sistema_de_contratacion,
                procedimiento=exp.Procedimiento_de_contratacion,
                tipo_tramitacion=exp.Tipo_de_tramitacion,
                metodo_presentacion=exp.Metodo_de_presentacion,
                fecha_fin_oferta=parse_date(exp.Fecha_fin_de_presentacion),
                resultado=exp.Resultado,
                adjudicatario=exp.Adjudicatario,
                n_licitadores=parse_int(exp.Num_de_Licitadores),
                importe_adjudicacion=parse_float(exp.Importe_de_Adjudicacion),
                fecha_fin_solicitud=parse_date(exp.Fecha_fin_de_solicitud),
                url=exp.url
            )
            session_clean.add(nuevo_expediente)  # Añadir el nuevo expediente a la sesión
    session_clean.commit()  # Confirmar los cambios en la base de datos


def main():
    # Crear el motor de base de datos y la sesión
    engine_clean = create_engine("sqlite:///clean_database.db")
    engine_raw = create_engine("sqlite:///raw_database.db")

    session_clean = Session(engine_clean)
    session_raw = Session(engine_raw)

    add_organos(session_clean, session_raw)
    add_adjudicatarios(session_clean,session_raw)
    transform_and_save_expedientes(session_clean, session_raw)

    session_clean.close()
    session_raw.close()


if __name__ == "__main__":
    main()

