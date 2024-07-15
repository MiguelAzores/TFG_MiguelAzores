import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from sqlmodel import create_engine, Session, select
import pandas as pd
from clean_db import OrganoContratacion, Expediente, Adjudicatario  # Asegúrate de importar tus modelos

# Función para obtener los X expedientes más caros de un órgano de contratación específico
def get_top_expedientes_mas_caros(session, organo_id, limit):
    statement = (
        select(Expediente)
        .where(Expediente.id_organo == organo_id)
        .order_by(Expediente.importe_adjudicacion.desc())
        .limit(limit)
    )
    expedientes = session.exec(statement).all()
    data = [exp.model_dump() for exp in expedientes]
    return pd.DataFrame(data)


# Función para obtener los detalles de un expediente específico
def get_expediente_details(session, expediente_id):
    statement = select(Expediente).where(Expediente.internal_id == expediente_id)
    expediente = session.exec(statement).first()
    if expediente:
        return expediente.model_dump()
    return None

# Función para obtener los últimos contratos, opcionalmente filtrados por órgano de contratación y estado del expediente
def get_ultimos_contratos(session, organo_id=None, estado_lic=None, limit=10):
    statement = select(Expediente).order_by(Expediente.fecha_fin_oferta.desc()).limit(limit)
    if organo_id:
        statement = statement.where(Expediente.id_organo == organo_id)
    if estado_lic:
        statement = statement.where(Expediente.estado_lic == estado_lic)

    expedientes = session.exec(statement).all()
    data = [exp.model_dump() for exp in expedientes]
    return pd.DataFrame(data)

# Función para obtener una lista de adjudicatarios
def get_adjudicatarios():
    with Session(engine) as session:
        statement = select(Adjudicatario.nombre).order_by(Adjudicatario.nombre)
        adjudicatarios = session.exec(statement).all()
    return [{"label": adj, "value": adj} for adj in adjudicatarios if adj]

# Función para obtener todos los expedientes de un adjudicatario específico
def get_expedientes_por_adjudicatario(session, adjudicatario):
    statement = select(Expediente).where(Expediente.adjudicatario == adjudicatario)
    expedientes = session.exec(statement).all()
    data = [exp.model_dump() for exp in expedientes]
    return pd.DataFrame(data)

def get_total_por_adjudicatario(session: Session, organo_id: int):
    # Seleccionar todos los expedientes para un órgano de contratación específico
    statement = select(Expediente).where(Expediente.id_organo == organo_id)
    expedientes = session.exec(statement).all()

    # Crear un DataFrame a partir de los expedientes
    data = [exp.dict() for exp in expedientes]
    df = pd.DataFrame(data)

    if df.empty:
        return []

    # Agrupar por adjudicatario y sumar los importes adjudicados
    total_por_adjudicatario = df.groupby('adjudicatario')['importe_adjudicacion'].sum().reset_index()

    # Ordenar de mayor a menor
    total_por_adjudicatario = total_por_adjudicatario.sort_values(by='importe_adjudicacion', ascending=False)

    return total_por_adjudicatario

# Crear el motor de base de datos y la sesión
engine = create_engine("sqlite:///cleandata.db")

# Función para obtener todos los órganos de contratación
def fetch_organos():
    with Session(engine) as session:
        statement = select(OrganoContratacion)
        organos = session.exec(statement).all()
    return organos

organos = fetch_organos()
organo_options = [{"label": organo.nombre, "value": organo.id} for organo in organos]
adjudicatarios_options = get_adjudicatarios()

# Lista de estados del expediente
estados_expediente = [
    "Resuelta", "Evaluación", "Adjudicada", "Anulada", "Publicada",
    "Evaluación Previa", "Parcialmente Resuelta", "Parcialmente Adjudicada", "Anuncio Previo"
]
estado_options = [{"label": estado, "value": estado} for estado in estados_expediente]

# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Visualización de Expedientes"

# Diseñar el layout de la aplicación
app.layout = html.Div(style={'backgroundColor': '#f9f9f9', 'font-family': 'Ruda, Ruda'}, children=[
    html.H1(
        children='Portal de Visualización de Datos',
        style={
            'textAlign': 'center',
            'color': '#333333',
            'padding': '20px',
            'backgroundColor': '#75B2B4',
            'borderRadius': '5px',
            'color': 'white'
        }
    ),



    dcc.Tabs(id='tabs', value='tab-0', children=[
        # Pestaña de introducción
        dcc.Tab(label='Introducción', value='tab-0', children=[
            html.Div(style={'padding': '20px', 'maxWidth': '800px', 'margin': '0 auto', 'backgroundColor': '#ffffff', 'borderRadius': '10px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}, children=[
                html.H2('Guía de Uso', style={'textAlign': 'center', 'color': '#4CAF50'}),
                html.P("Este Portal de Visualización le permite explorar y analizar los datos de contratación pública relacionados con Jerez de la frontera de manera interactiva. A continuación, se presentan algunas definiciones clave y una guía rápida sobre cómo utilizar las diferentes funcionalidades de esta herramienta.", style={'fontSize': '18px', 'lineHeight': '1.6'}),

                html.H3('Diccionario de términos', style={'marginTop': '20px','color': '#4CAF50'}),
                html.H4('Órgano de Contratación', style={}),
                html.P("El órgano de contratación es la entidad pública responsable de llevar a cabo el proceso de contratación. Puede ser una institución gubernamental, una agencia o cualquier otra entidad autorizada para adjudicar contratos.", style={'fontSize': '16px'}),

                html.H4('Expediente', style={}),
                html.P("El expediente es el conjunto de documentos y registros asociados a un proceso de contratación. Incluye la información sobre el contrato, las ofertas recibidas, las evaluaciones realizadas y las decisiones tomadas.", style={'fontSize': '16px'}),

                html.H4('Estado del Expediente', style={}),
                html.P("El estado del expediente indica la fase en la que se encuentra el proceso de contratación. Algunos estados comunes son 'Resuelta', 'Evaluación', 'Adjudicada', 'Anulada' y 'Publicada'.", style={'fontSize': '16px'}),

                html.H4('Adjudicatario', style={}),
                html.P("El adjudicatario es la persona o entidad que participa en el proceso de licitación presentando una oferta para un contrato específico y consigue que se le adjudique este proyecto.", style={'fontSize': '16px'}),

                html.H3('Guía Rápida', style={'marginTop': '20px','color': '#4CAF50'}),
                html.P("Utilice las pestañas en la parte superior para navegar entre las diferentes funcionalidades de la herramienta:", style={'fontSize': '16px'}),
                html.Ul([
                    html.Li("Top Expedientes Más Caros: Visualice los expedientes con mayor importe de adjudicación para un órgano de contratación específico.", style={'fontSize': '16px'}),
                    html.Li("Últimos Contratos: Consulte los contratos más recientes y filtre por órgano de contratación y estado del expediente.", style={'fontSize': '16px'}),
                    html.Li("Buscar por Adjudicatario: Encuentre todos los expedientes asociados a un adjudicatario específico.", style={'fontSize': '16px'}),
                    html.Li("Total Recibido por Adjudicatario: Vea el importe total recibido por cada adjudicatario para un órgano de contratación específico.", style={'fontSize': '16px'})
                ])
            ])
        ]),
        # Top 10 expedientes más caros
        dcc.Tab(label='Top Expedientes Más Caros', value='tab-1', children=[
            html.Div(style={'textAlign': 'center', 'margin': '20px'}, children=[
                html.Label('Selecciona un Órgano de Contratación:', style={'fontSize': '20px', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='organo-dropdown',
                    options=organo_options,
                    value=organos[0].id if organos else None,
                    style={'width': '50%', 'margin': '0 auto'}
                ),
                html.Label('Número de Expedientes:', style={'fontSize': '20px', 'marginTop': '10px'}),
                dcc.Input(
                    id='num-expedientes-input',
                    type='number',
                    value=10,  # Valor por defecto
                    min=1,
                    step=1,
                    style={'width': '20%', 'margin': '0 auto'}
                ),
            ]),

            dcc.Graph(
                id='top-ten-graph',
                style={'width': '80%', 'margin': '0 auto', 'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}
            ),

            html.Div(id='expediente-details', style={'width': '80%', 'margin': '20px auto', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ]),
        # Ultimos contratos
        dcc.Tab(label='Últimos Contratos', value='tab-2', children=[
        html.Div(style={'textAlign': 'center', 'margin': '20px'}, children=[
            html.Label('Selecciona un Órgano de Contratación:', style={'fontSize': '20px', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='ultimos-organo-dropdown',
                options=organo_options,
                style={'width': '50%', 'margin': '0 auto'}
            ),
        ]),
        html.Div(style={'textAlign': 'center', 'margin': '20px'}, children=[
            html.Label('Selecciona el Estado del Expediente:', style={'fontSize': '20px', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='estado-dropdown',
                options=estado_options,
                style={'width': '50%', 'margin': '0 auto'}
            ),
        ]),
        dash_table.DataTable(
            id='ultimos-contratos-table',
            columns=[
                {'name': 'Nombre', 'id': 'nombre_exp'},
                {'name': 'Objeto del contrato', 'id': 'objeto_contrato'},
                {'name': 'Importe de Adjudicación', 'id': 'importe_adjudicacion'},
                {'name': 'Fecha fin de oferta', 'id': 'fecha_fin_oferta'},
                {'name': 'Adjudicatario', 'id': 'adjudicatario'},
                {'name': 'Estado', 'id': 'estado_lic'}
            ],
            style_table={'width': '80%', 'margin': '0 auto', 'padding': '20px', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'wordBreak': 'break-word'},
            row_selectable='single',  # Permitir selección de una fila
            selected_rows=[],
            page_size=10
        ),

            html.Div(id='ultimos-contratos-details', style={'width': '80%', 'margin': '20px auto', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ]),
        # Buscar por adjudicatarios

        dcc.Tab(label='Buscar por Adjudicatario', value='tab-3', children=[
        html.Div(style={'textAlign': 'center', 'margin': '20px'}, children=[
            html.Label('Selecciona el Adjudicatario:', style={'fontSize': '20px', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='adjudicatario-dropdown',
                options=adjudicatarios_options,
                multi=True,  # Permitir selección múltiple
                style={'width': '50%', 'margin': '0 auto'}
            ),
            html.Button('Buscar', id='buscar-button', n_clicks=0, style={'margin': '10px'})
        ]),
        dash_table.DataTable(
            id='adjudicatario-table',
            columns=[
                {'name': 'Nombre', 'id': 'nombre_exp'},
                {'name': 'Objeto del contrato', 'id': 'objeto_contrato'},
                {'name': 'Órgano de Contratación', 'id': 'organo_contratacion'},
                {'name': 'Importe de Adjudicación', 'id': 'importe_adjudicacion'},
                {'name': 'Adjudicatario', 'id': 'adjudicatario'},
                {'name': 'Estado', 'id': 'estado_lic'}
            ],
            style_table={'width': '80%', 'margin': '0 auto', 'padding': '20px', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_cell={'textAlign': 'left', 'padding': '5px', 'whiteSpace': 'normal', 'wordBreak': 'break-word'},
            row_selectable='single',  # Permitir selección de una fila
            selected_rows=[],
            page_size=10
        ),

            html.Div(id='adjudicatario-details', style={'width': '80%', 'margin': '20px auto', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ]),

        dcc.Tab(label='Total Recibido por Adjudicatario', value='tab-4', children=[
            html.Div(style={'textAlign': 'center', 'margin': '20px'}, children=[
                html.Label('Selecciona un Órgano de Contratación:', style={'fontSize': '20px', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='organo-total-dropdown',
                    options=organo_options,
                    value=None,
                    style={'width': '50%', 'margin': '0 auto'}
                ),
                html.Label('Número de Empresas a Visualizar:', style={'fontSize': '20px', 'marginBottom': '10px'}),
                dcc.Input(
                    id='num-empresas-input',
                    type='number',
                    value=10,  # Valor por defecto
                    min=1,
                    step=1,
                    style={'width': '10%', 'margin': '0 auto'}
                )
            ]),

            dcc.Graph(
                id='total-adjudicatarios-graph',
                style={'width': '80%', 'margin': '0 auto', 'backgroundColor': '#ffffff', 'padding': '20px', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'}
            ),

            #html.Div(id='total-adjudicatarios-details', style={'width': '80%', 'margin': '20px auto', 'padding': '20px', 'backgroundColor': '#ffffff', 'borderRadius': '5px', 'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'})
        ])

    ])
])

# ------------- CALLBACKS ------------------------------------
# Callback para actualizar el gráfico de los 10 expedientes más caros basado en el órgano de contratación seleccionado
@app.callback(
    Output('top-ten-graph', 'figure'),
    [Input('organo-dropdown', 'value'),
     Input('num-expedientes-input', 'value')]
)
def update_graph(organo_id, num_expedientes):
    if not organo_id:
        return go.Figure().update_layout(title='Selecciona un órgano de contratación para ver los datos.')

    if not num_expedientes or num_expedientes < 1:
        num_expedientes = 10  # Valor por defecto si no se especifica uno válido

    with Session(engine) as session:
        df = get_top_expedientes_mas_caros(session, organo_id, num_expedientes)

    if df.empty:
        fig = go.Figure().update_layout(title='No hay datos disponibles')
    else:
        fig = go.Figure(data=[go.Bar(x=df['importe_adjudicacion'], y=df['nombre_exp'], orientation='h', marker=dict(color='#4CAF50'))])
        fig.update_layout(
            title=f'Top {num_expedientes} Expedientes Más Caros',
            xaxis_title='Importe de Adjudicación',
            yaxis_title='Nombre del Expediente',
            yaxis=dict(categoryorder='total ascending'),
            plot_bgcolor='#ffffff',
            paper_bgcolor='#f9f9f9',
            font=dict(color='#333333', size=14)
        )
        fig.update_traces(hoverinfo='text', hovertemplate='Nombre del expediente: %{y}<br>Importe: %{x}')

    return fig

# Callback para mostrar los detalles del expediente seleccionado en el gráfico de los X expedientes más caros
@app.callback(
    Output('expediente-details', 'children'),
    Input('top-ten-graph', 'clickData')
)
def display_expediente_details(clickData):
    if clickData is None:
        return html.P("Selecciona un expediente en el gráfico para ver los detalles.")

    nombre_exp = clickData['points'][0]['y']

    with Session(engine) as session:
        statement = select(Expediente).where(Expediente.nombre_exp == nombre_exp)
        expediente = session.exec(statement).first()

    if expediente is None:
        return html.P("No se encontró el expediente seleccionado.")

    table_header = [
        html.Thead(html.Tr([html.Th("Campo"), html.Th("Valor")]))
    ]

    table_body = [
        html.Tbody([
            html.Tr([html.Td("Nombre del Expediente"), html.Td(expediente.nombre_exp)]),
            html.Tr([html.Td("Estado"), html.Td(expediente.estado_lic)]),
            html.Tr([html.Td("Importe de Adjudicación"), html.Td(f"{expediente.importe_adjudicacion:,.2f} €" if expediente.importe_adjudicacion else " ")]),
            html.Tr([html.Td("Adjudicatario"), html.Td(expediente.adjudicatario)]),
            html.Tr([html.Td("Fecha de Fin de Solicitud"), html.Td(expediente.fecha_fin_solicitud)]),
            html.Tr([html.Td("Órgano de Contratación"), html.Td(expediente.organo_contratacion if expediente.organo_contratacion else 'Desconocido')]),
            html.Tr([html.Td("Objeto del Contrato"), html.Td(expediente.objeto_contrato)]),
            html.Tr([html.Td("Financiación UE"), html.Td(expediente.financiacion_UE)]),
            html.Tr([html.Td("Presupuesto sin Impuestos"), html.Td(f"{expediente.presupuesto_sin_impuestos:,.2f} €" if expediente.presupuesto_sin_impuestos else " " )]),
            html.Tr([html.Td("Valor Estimado"), html.Td(f"{expediente.valor_estimado:,.2f} €" if expediente.valor_estimado else " ")]),
            html.Tr([html.Td("Tipo de Contrato"), html.Td(expediente.tipo_contrato)]),
            html.Tr([html.Td("Código CPV"), html.Td(expediente.codigo_CPV)]),
            html.Tr([html.Td("Lugar de Ejecución"), html.Td(expediente.lugar_ejecucion)]),
            html.Tr([html.Td("Sistema de Contratación"), html.Td(expediente.sistema_contratacion)]),
            html.Tr([html.Td("Procedimiento de Contratación"), html.Td(expediente.procedimiento)]),
            html.Tr([html.Td("Tipo de Tramitación"), html.Td(expediente.tipo_tramitacion)]),
            html.Tr([html.Td("Método de Presentación"), html.Td(expediente.metodo_presentacion)]),
            html.Tr([html.Td("Fecha Fin de Oferta"), html.Td(expediente.fecha_fin_oferta)]),
            html.Tr([html.Td("Número de Licitadores"), html.Td(expediente.n_licitadores)]),
            html.Tr([html.Td("Resultado"), html.Td(expediente.resultado)]),
            html.Tr([html.Td("Enlace:"), html.Td(html.A("Ver expediente en la Plataforma", href=expediente.url, target="_blank"))])
        ])
    ]

    table = dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)

    return html.Div([
        html.H2(f"Detalles del Expediente: {expediente.nombre_exp}"),
        table
    ])

# Callback para actualizar el gráfico de los últimos contratos basado en el órgano de contratación y el estado del expediente seleccionados
@app.callback(
    Output('ultimos-contratos-table', 'data'),
    [Input('ultimos-organo-dropdown', 'value'),
     Input('estado-dropdown', 'value')]
)
def update_ultimos_contratos(organo_id, estado_lic):
    if not organo_id or not estado_lic:
        return []

    with Session(engine) as session:
        df = get_ultimos_contratos(session, organo_id, estado_lic)

    if df.empty:
        return []
    else:
        df = df[['nombre_exp', 'objeto_contrato', 'importe_adjudicacion', 'adjudicatario', 'fecha_fin_oferta','estado_lic']]
        df['importe_adjudicacion'] = df['importe_adjudicacion'].apply(lambda x: f"{x:,.2f} €"if x is not None else " ")
        #df['fecha_fin_oferta'] = df['fecha_fin_oferta'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
        return df.to_dict('records')

# Callback para mostrar los detalles del contrato seleccionado en el gráfico de los últimos contratos
@app.callback(
    Output('ultimos-contratos-details', 'children'),
    Input('ultimos-contratos-table', 'selected_rows'),
    Input('ultimos-contratos-table', 'data')
)
def display_ultimos_contratos_details(selected_rows, rows):
    if not selected_rows or not rows:
        return html.P("Selecciona un contrato en la tabla para ver los detalles.")

    selected_row = rows[selected_rows[0]]
    nombre_exp = selected_row['nombre_exp']

    with Session(engine) as session:
        statement = select(Expediente).where(Expediente.nombre_exp == nombre_exp)
        expediente = session.exec(statement).first()

    if expediente is None:
        return html.P("No se encontró el contrato seleccionado.")

    table_header = [
        html.Thead(html.Tr([html.Th("Campo"), html.Th("Valor")]))
    ]

    table_body = [
        html.Tbody([
            html.Tr([html.Td("Nombre del Expediente"), html.Td(expediente.nombre_exp)]),
            html.Tr([html.Td("Estado"), html.Td(expediente.estado_lic)]),
            html.Tr([html.Td("Importe de Adjudicación"), html.Td(f"{expediente.importe_adjudicacion:,.2f} €" if expediente.importe_adjudicacion else " ")]),
            html.Tr([html.Td("Adjudicatario"), html.Td(expediente.adjudicatario)]),
            html.Tr([html.Td("Fecha de Fin de Solicitud"), html.Td(expediente.fecha_fin_solicitud)]),
            html.Tr([html.Td("Órgano de Contratación"), html.Td(expediente.organo_contratacion if expediente.organo_contratacion else 'Desconocido')]),
            html.Tr([html.Td("Objeto del Contrato"), html.Td(expediente.objeto_contrato)]),
            html.Tr([html.Td("Financiación UE"), html.Td(expediente.financiacion_UE)]),
            html.Tr([html.Td("Presupuesto sin Impuestos"), html.Td(f"{expediente.presupuesto_sin_impuestos:,.2f} €" if expediente.presupuesto_sin_impuestos else " ")]),
            html.Tr([html.Td("Valor Estimado"), html.Td(f"{expediente.valor_estimado:,.2f} €" if expediente.valor_estimado else " ")]),
            html.Tr([html.Td("Tipo de Contrato"), html.Td(expediente.tipo_contrato)]),
            html.Tr([html.Td("Código CPV"), html.Td(expediente.codigo_CPV)]),
            html.Tr([html.Td("Lugar de Ejecución"), html.Td(expediente.lugar_ejecucion)]),
            html.Tr([html.Td("Sistema de Contratación"), html.Td(expediente.sistema_contratacion)]),
            html.Tr([html.Td("Procedimiento de Contratación"), html.Td(expediente.procedimiento)]),
            html.Tr([html.Td("Tipo de Tramitación"), html.Td(expediente.tipo_tramitacion)]),
            html.Tr([html.Td("Método de Presentación"), html.Td(expediente.metodo_presentacion)]),
            html.Tr([html.Td("Fecha Fin de Oferta"), html.Td(expediente.fecha_fin_oferta)]),
            html.Tr([html.Td("Número de Licitadores"), html.Td(expediente.n_licitadores)]),
            html.Tr([html.Td("Resultado"), html.Td(expediente.resultado)]),
            html.Tr([html.Td("Enlace:"), html.Td(html.A("Ver expediente en la Plataforma", href=expediente.url, target="_blank"))])

        ])
    ]

    table = dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)

    return html.Div([
        html.H2(f"Detalles del Contrato: {expediente.nombre_exp}"),
        table
    ])

# Callback para la pestña "buscar expedientes por adjudicatario"
@app.callback(
    Output('adjudicatario-table', 'data'),
    Input('buscar-button', 'n_clicks'),
    Input('adjudicatario-dropdown', 'value')
)
def buscar_expedientes_por_adjudicatario(n_clicks, adjudicatarios):
    print(adjudicatarios)
    if not adjudicatarios:
        return []

    with Session(engine) as session:
        df =  pd.concat([get_expedientes_por_adjudicatario(session, adj) for adj in adjudicatarios])
        print(df)
    if df.empty:
        return []

    # Seleccionar las columnas necesarias
    df = df[['nombre_exp', 'objeto_contrato','organo_contratacion', 'importe_adjudicacion', 'adjudicatario', 'estado_lic']]
    df['importe_adjudicacion'] = df['importe_adjudicacion'].apply(lambda x: f"{x:,.2f} €")
    #df['fecha_fin_solicitud'] = df['fecha_fin_solicitud'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')

    return df.to_dict('records')

@app.callback(
    Output('adjudicatario-details', 'children'),
    Input('adjudicatario-table', 'selected_rows'),
    Input('adjudicatario-table', 'data')
)
def display_adjudicatario_expediente_details(selected_rows, rows):
    if not selected_rows or not rows:
        return html.P("Selecciona un expediente en la tabla para ver los detalles.")

    selected_row = rows[selected_rows[0]]
    nombre_exp = selected_row['nombre_exp']

    with Session(engine) as session:
        statement = select(Expediente).where(Expediente.nombre_exp == nombre_exp)
        expediente = session.exec(statement).first()

    if expediente is None:
        return html.P("No se encontró el expediente seleccionado.")

    table_header = [
        html.Thead(html.Tr([html.Th("Campo"), html.Th("Valor")]))
    ]

    table_body = [
        html.Tbody([
            html.Tr([html.Td("Nombre del Expediente"), html.Td(expediente.nombre_exp)]),
            html.Tr([html.Td("Estado"), html.Td(expediente.estado_lic)]),
            html.Tr([html.Td("Importe de Adjudicación"), html.Td(f"{expediente.importe_adjudicacion:,.2f} €" if expediente.importe_adjudicacion else " ")]),
            html.Tr([html.Td("Adjudicatario"), html.Td(expediente.adjudicatario)]),
            html.Tr([html.Td("Fecha de Fin de Solicitud"), html.Td(expediente.fecha_fin_solicitud)]),
            html.Tr([html.Td("Órgano de Contratación"), html.Td(expediente.organo_contratacion if expediente.organo_contratacion else 'Desconocido')]),
            html.Tr([html.Td("Objeto del Contrato"), html.Td(expediente.objeto_contrato)]),
            html.Tr([html.Td("Financiación UE"), html.Td(expediente.financiacion_UE)]),
            html.Tr([html.Td("Presupuesto sin Impuestos"), html.Td(f"{expediente.presupuesto_sin_impuestos:,.2f} €" if expediente.presupuesto_sin_impuestos else " ")]),
            html.Tr([html.Td("Valor Estimado"), html.Td(f"{expediente.valor_estimado:,.2f} €" if expediente.valor_estimado else " ")]),
            html.Tr([html.Td("Tipo de Contrato"), html.Td(expediente.tipo_contrato)]),
            html.Tr([html.Td("Código CPV"), html.Td(expediente.codigo_CPV)]),
            html.Tr([html.Td("Lugar de Ejecución"), html.Td(expediente.lugar_ejecucion)]),
            html.Tr([html.Td("Sistema de Contratación"), html.Td(expediente.sistema_contratacion)]),
            html.Tr([html.Td("Procedimiento de Contratación"), html.Td(expediente.procedimiento)]),
            html.Tr([html.Td("Tipo de Tramitación"), html.Td(expediente.tipo_tramitacion)]),
            html.Tr([html.Td("Método de Presentación"), html.Td(expediente.metodo_presentacion)]),
            html.Tr([html.Td("Fecha Fin de Oferta"), html.Td(expediente.fecha_fin_oferta)]),
            html.Tr([html.Td("Número de Licitadores"), html.Td(expediente.n_licitadores)]),
            html.Tr([html.Td("Resultado"), html.Td(expediente.resultado)]),
            html.Tr([html.Td("Enlace:"), html.Td(html.A("Ver expediente en la Plataforma", href=expediente.url, target="_blank"))])
        ])
    ]

    table = dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)

    return html.Div([
        html.H2(f"Detalles del Expediente: {expediente.nombre_exp}"),
        table
    ])

@app.callback(
    Output('total-adjudicatarios-graph', 'figure'),
    [Input('organo-total-dropdown', 'value'),
     Input('num-empresas-input', 'value')]
)
def update_total_adjudicatarios_graph(organo_id, num_empresas):
    if not organo_id:
        return go.Figure().update_layout(title='Selecciona un órgano de contratación para ver los datos.')

    if not num_empresas or num_empresas < 1:
        num_empresas = 10  # Valor por defecto si no se especifica uno válido

    with Session(engine) as session:
        df = get_total_por_adjudicatario(session, organo_id)

    if df.empty:
        fig = go.Figure().update_layout(title='No hay datos disponibles')
    else:
        df = df.head(num_empresas)
        fig = go.Figure(data=[go.Bar(x=df['importe_adjudicacion'], y=df['adjudicatario'], orientation='h', marker=dict(color='#4CAF50'))])
        fig.update_layout(
            title='Total Recibido por Adjudicatario',
            xaxis_title='Importe de Adjudicación',
            yaxis_title='Adjudicatario',
            yaxis=dict(categoryorder='total ascending'),
            plot_bgcolor='#ffffff',
            paper_bgcolor='#f9f9f9',
            font=dict(color='#333333', size=14)
        )
        fig.update_traces(hoverinfo='text', hovertemplate='Adjudicatario: %{y}<br>Importe: %{x}')

    return fig

server = app.server

if __name__ == '__main__':
    app.run_server(debug=False)
