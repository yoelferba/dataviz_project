"""
Código del caso práctico de Yoel Fernández Ballega.
Objetivos principales:
- Analizar la expansión del virus Covid-19, directamente relacionado con las conexiones entre los aeropuertos que 
  encontramos entre el foco (Wuhan) y el resto  del mundo.
- Analizar particularmente los efectos del virus en cada país.

"""

# Importamos los paquetes necesarios (principalmente: dash, plotly y pandas)
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import numpy as np
import os
import arrow
import requests
import functools
import pandas as pd
from dash_table import DataTable
import plotly.graph_objs as go
import chart_studio.plotly as py
from flask import Flask, json
from dotenv import load_dotenv
import plotly.express as px

"""
Vamos a crear la aplicación desde cero, por lo tanto lo primero es definir el estilo que tendrá la página.
Como veremos al ejecutar este código, he creado aplicación tal que existe una barra lateral a modo de índice 
que nos permita seleccionar qué queremos analizar. Por lo tanto, hay que definir el estilo de la barra lateral
así como del resto de la página. 

Invertí mucho tiempo en la elección del estilo, puesto que es crucial que la interfaz sea intuitiva para 
despertar desde el primer momento el interés del consumidor y atraer su atención.
"""

#
# Definimos estilo: colores de la págima, del menú, tamaños de cada marco, estilo de las tablas, detalles del fondo, etc.
#

external_js = [
    'https://code.jquery.com/jquery-3.2.1.slim.min.js',
    'https://codepen.io/jackdbd/pen/bROVgV.js',
]


# Como dijimos, el stylesheet es muy importante, seleccionamso el css de página externa que nos interesa
external_css = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',   # este fue el stylesheet de dash que más se adecua a lo que busco
    #'https://fonts.googleapis.com/css?family=Raleway',
    #'https://fonts.googleapis.com/css?family=Lobster',
]

# Es necesario emplear: debug=True, para solventar un error que me aparecía
debug = True
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)


"""
Para poder llevar a cabo el objetivo de la visualización, la mejor herramienta que podemos usar es un mapa
interactivo que permita al usuario, con total libertad, analizar y estudiar lo que le interese.

Para generar el mapa me he decantado por "mapbox" en lugar de Google Maps por ejemplo. Me parecen unos mapas 
mucho más claros y sencillos. Como hemos estudiado, para explotar los atributos de la percepción visual
humana es fundamental que la visualización sea tal que no se necesite (idealmente) pensar en cómo interpretarla.
Los mapas de Google Maps tienen muchos detalles que, para este estudio, distraerían y perjudicarían a la
interpretación. Además, también es gratis!
"""

#
# Para usar mapbox debemos ingresar el nombre de usuario y las contraseñas: API y el token (es gratis)
#
py.sign_in('sanmi5', 'SshEke0gEyWcCstw1XKn')  # user_name + api_key
mapbox_access_token = 'pk.eyJ1Ijoic2FudGkyNXMiLCJhIjoiY2s3b2pxbGxwMDBnazNmcnJzNzc5MHhtZSJ9.f90j1aww3IgBarWu9G3PFw' #token


# Cuestión de estilo: arrancamos la aplicación de dash indicándole el estilo que venimos definiendo
external_stylesheets =['https://codepen.io/chriddyp/pen/bWLwgP.css', dbc.themes.BOOTSTRAP]
app = dash.Dash(external_stylesheets=external_stylesheets)


#
# Como creamos la app desde cero, debemos especificar todos los parámetros: 
# la posición de la barra lateral, el ancho, etc. 
# 

SIDEBAR_STYLE = {
    "position": "absolute",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "24rem",
    "padding": "2rem 1rem",
    "background-color": "#454545",
}

#
# Lo mismo para el contenido del resto de la página
#

CONTENT_STYLE = {
    "position": "relative",
    "margin-left": "12rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "width": "auto",
}

#
# Diseño ahora el contenido de la barra de la izquierda: títulos, opciones etc. Creo un menú que nos 
# lleva a distintas páginas (parte de: dbc.NavLink(...) ) para no sobrecargar de información al consumidor
# y para que la visualización esté más ordenada.
# 

sidebar = html.Div(
    [
        html.H1("Covid-19", className="display-4", style={'color': 'white', 'fontSize': 45, 'font-family':'verdana'}),
        html.Hr(),
        html.P(
            "Menú: ", className="lead", style={'color': 'white', 'fontSize': 18}
        ),
        dbc.Nav(
            [
                dbc.NavLink("Conexiones aéreas de Wuhan", href="/conexiones_aereas_wuhan", id="page-1-link", style={'color': 'white', 'fontSize': 14}),
                dbc.NavLink("Impacto global del virus Covid-19", href="/impacto_global", id="page-2-link", style={'color': 'white', 'fontSize': 14}),
                dbc.NavLink("Información detallada Covid-19", href="/impacto_por_pais", id="page-3-link", style={'color': 'white', 'fontSize': 14}),
                dbc.NavLink("En desarrollo", href="/page-4", id="page-4-link", style={'color': 'white', 'fontSize': 14}),
                #dbc.NavLink("", href="/page-5", id="page-5-link", style={'color': 'white', 'fontSize': 14}),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,   # aplicamos el estilo que hemos definido anteriormente
)

#
# Creada ya la barra lateral, creamos el resto del contenido de la app de dash y terminamos de configurarla. 
# 
content = html.Div(id="page-content", style=CONTENT_STYLE)
app.layout = html.Div([dcc.Location(id="url"), sidebar, content])
app.config['suppress_callback_exceptions'] = True


#
#  Una vez configurada la app de dash, definimos algunas caraterísticas que utilizaremos posteriormente, por 
#  ejemplo acerca de los distintos colores que usamos a lo largo de la visualización.
# 


colorscale_magnitude = [
    [0, '#ffffb2'],
    [0.25, '#fecc5c'],
    [0.5, '#fd8d3c'],
    [0.75, '#f03b20'],
    [1, '#bd0026'],
]

colorscale_depth = [
    [0, '#f0f0f0'],
    [0.5, '#bdbdbd'],
    [0.1, '#636363'],
]

theme = {
    'font-family': 'Raleway',
    'background-color': '#787878',
}





#
# Estos son los datos que se emplean para todas las visualizaciones. Cargamos los datos desde archivos .csv
# una vez que ya han sido limpiados y ordenados.
#

# ruta dónde se encuentran los datos descargados
ruta = os.path.dirname(os.path.realpath(__file__))
os.chdir(ruta)

# leemos los datos 
df_covid = pd.read_csv(ruta + "covid_entrega.csv")
rutas = pd.read_csv(ruta + "rutas_def2.csv")


# realizamos unos cambios de útima hora (son inmediatos y cuesta menos que hacerlo manualmente en Excel)
df_covid.rename(columns={"Country/Region":"Country"}, inplace=True)
df_covid.rename(columns={"Lat":"Latitude"}, inplace=True)
df_covid.rename(columns={"Long":"Longitude"}, inplace=True)



# Creamos algunos DataFrames a partir de los datos cargados para usarlos posteriormente como la primera 
# opción que se ve antes de que el consumidor empiece a interaccionar con el mapa

df_covid_per = df_covid[['Confirmados diarios', 'Muertos diarios', 'Recuperados diarios','Porcentaje confirmados', 'Porcentaje muertos','Porcentaje recuperados']]
df_covid_esp = df_covid[df_covid["Country"]=="Spain"]
df_covid_fra = df_covid[df_covid["Country"]=="France"]   
df_covid_fra["Province/State"].fillna("Paris", inplace=True)
 # Al realizar la visualización detecté un fallo en Francia que corregí fácilmente




#
# Esto es el contenido de la primera página (page 1)
# 

# Definición necesaria para el dropdown que te permite escoger la región en la que quieres centrar 
# la visualización. 

regions = {
    'world': {'lat': 0, 'lon': 0, 'zoom': 1},
    'europe': {'lat': 45, 'lon': 0, 'zoom': 3},
    'north_america': {'lat': 40, 'lon': -100, 'zoom': 2},
    'south_america': {'lat': -15, 'lon': -60, 'zoom': 2},
    'africa': {'lat': 0, 'lon': 20, 'zoom': 2},
    'asia': {'lat': 30, 'lon': 100, 'zoom': 2},
    'oceania': {'lat': -10, 'lon': 130, 'zoom': 2},
}

# Creamos la función que crea el relleno de la página 1 del menú. Creamos una figura vacía que rellenaremos
# y actualizaremos cuando la función "_update_graph" de más abajo sea llamada.

def create_content():
    graph = dcc.Graph(id='graph-geo')  
    content = html.Div(graph, id='content')
    return content

"""
A continuación creamos los widgets, los dropdowns que nos permitirán escoger entre distintos valores 
de modo que la visualización sea interactiva y más agradable y atractiva para el consumidor. Permitimos
cambiar desde la región en la que se quieren ver los aeropuertos hasta el tipo de mapa (tema claro u oscuro
o un tema de vista satélite). Esto es así debido a la creciente demanda de apps con temas con temas oscuros 
o si, por ejemplo, el consumidor tiene inquietudes acerca de la posición y apariencia real del mapa.

De todos modos, he aplicado lo aprendido en la asignatura y he inicializado la visualización con la vista que
más fácil hace que se interpreten los datos que represento. 

NOTA: no ha sido nada fácil y ha requerido más horas de las que me gustaría reconocer, entender el 
funcionamiento de Dash. Busco que el usuario pueda interaccionar libremente con los gráficos y, para ello,
todo lo que defina ahora tengo que asignarle una identidad "id" para luego poder actualizar las visualizaciones
según lo escogido.
"""

def create_dropdowns():
    dropdowns = dbc.Row(
            [
                dbc.Col(
                    dbc.Col([dbc.Alert(html.P("Tipo de mapa: ", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        options=[
                            {'label': 'Claro', 'value': 'light'},
                            {'label': 'Oscuro', 'value': 'dark'},
                            {'label': 'Vista satélite', 'value': 'satellite'}
                        ],
                        value='light',
                        id='dropdown-map-style',
                    )]),
                    width=3
                ),
            ],
            id = 'main-left-col'
        )
    return dropdowns


#
# Estableclemos ahora qué contendrá la página uno y en qué orden (saldran los widgets primer y el mapa después).
# Como vemos, aplicamos el estilo que cuidadosamente definimos arriba.
#

body = dbc.Container(
    [
        create_dropdowns(),   # primeros los dropdowns
        create_content(),   # luego el mapa
        
    ],
    style=CONTENT_STYLE,
    fluid=True,
)




#
# Esto es el contenido de la segunda página (page 2) de impacto de la enfermedad Covid-19
#


def create_content4():
    graph4 = dcc.Graph(id='graph-geo4')
    content4 = html.Div(graph4, id='content4')
    return content4


# widgets de la page3
def create_dropdowns4(dataframe1, dataframe2):
    dropdowns4 = dbc.Row(
            [
                dbc.Col(
                    #html.P("Select the visualization type: ", className="lead", style={'color': 'white', 'fontSize': 18}),
                    dbc.Col([dbc.Alert(html.P("Tipo de mapa:", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        options=[
                            {'label': 'Claro', 'value': 'light'},
                            {'label': 'Oscuro', 'value': 'dark'},
                            {'label': 'Satélite', 'value': 'satellite'}
                        ],
                        value='light',
                        id='dropdown-map-style4',
                    )]),
                    width=3
                ),
                dbc.Col(
                    dbc.Col([dbc.Alert(html.P("Parámetro a estudiar:", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        options=[{'label': i, 'value': i} for i in dataframe2.columns],
                        value='Confirmados diarios',
                        id='dropdown-parameter4',
                        multi=False,
                    )]),
                    width=3
                ),

                dbc.Col(
                    dbc.Col([dbc.Alert(html.P("Amplie la región deseada: ", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        options=[
                            {'label': 'Mundo', 'value': 'world'},
                            {'label': 'Europa', 'value': 'europe'},
                            {'label': 'Norte América', 'value': 'north_america'},
                            {'label': 'Sud América', 'value': 'south_america'},
                            {'label': 'África', 'value': 'africa'},
                            {'label': 'Asia', 'value': 'asia'},
                            {'label': 'Oceanía', 'value': 'oceania'},
                        ],
                        value='world',
                        id='dropdown-region4',
                    )]),
                    width=3
                ),

            ],
            id = 'main-left-col'
        )
    return dropdowns4

#
# Nuevo widget para la página 3: deslizador que nos permite analizar el avance del virus según el día.
# Por ahora, no he conseguido que el widget de Dash lea una variable diccionario que esté definida fuera, me 
# daba errores que no he conseguido solucionar y la solución que he encontrado ha sido definir los días dentro.
#

def create_slider(dataframe):
    slider4 = dbc.FormGroup(
        [
            #dbc.Label("---", html_for="slider2", style={'fontSize': 14}),
            dbc.Label("Selecciona el día para ver los efectos del virus:", html_for="slider", style={'fontSize': 14}),
            dcc.Slider(id="slider", min=0, max=93, updatemode="drag", step=None, marks={
                0: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                1: {'label': '', 'style': {"font-size":"8px","transform": "rotate(0deg)"}},
                2: {'label': '', 'style': {"font-size":"8px","transform": "rotate(0deg)"}},
                3: {'label': '25-enero', 'style': {"font-size":"8px"}},
                4: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                5: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                6: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                7: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                8: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                9: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                10:{'label': '1-febrero', 'style': {"font-size":"8px"}},
                11:{'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                12: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                13: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                14: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                15: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                16: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                17: {'label': '8-febrero', 'style': {"font-size":"8px"}},
                18: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                19: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                20: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                21: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                22: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                23: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                24: {'label': '15-febrero', 'style': {"font-size":"8px"}},
                25: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                26: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                27: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                28: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                29: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                30: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                31: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                32: {'label': '23-febrero', 'style': {"font-size":"8px"}},
                33: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                34: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                35: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                36: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                37: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                38: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                39: {'label': '1-marzo', 'style': {"font-size":"8px"}},
                40: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                41: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                42: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                43: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                44: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                45: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                46: {'label': '8-marzo', 'style': {"font-size":"8px"}},
                47: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                48: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                49: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                50: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                51: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                52: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                53: {'label': '15-marzo', 'style': {"font-size":"8px"}},
                54: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                55: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                56: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                57: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                58: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                59: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                60: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                61: {'label': '23-marzo', 'style': {"font-size":"8px"}},
                62: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                63: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                64: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                65: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                66: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                67: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                68: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                69: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                70: {'label': '1-abril', 'style': {"font-size":"8px"}},
                71: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                72: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                73: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                74: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                75: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                76: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                77: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                78: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                79: {'label': '10-abril', 'style': {"font-size":"8px"}},
                80: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},  #}, value=0),
                81: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                82: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                83: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                84: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                85: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                86: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                87: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                88: {'label': '19-abril', 'style': {"font-size":"8px"}},
                89: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                90: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                91: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                92: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}},
                93: {'label': '', 'style': {"font-size":"8px","transform": "rotate(-90deg)"}}}, value=0),
 
        ]
    )
    return slider4



body4 = dbc.Container(
    [
        create_dropdowns4(df_covid, df_covid_per),   #primero los dropdowns
        create_slider(df_covid_esp),   # luego el slider
        create_content4(),    # luego el mapa
    ],
    style=CONTENT_STYLE,
    fluid=True,
)


#
# Esto es el contenido de la cuarta página (page 4)
#

# Widgets para la página 5: dropdowns que permiten seleccionar el parámetro a estudiar y el país que queremos ver.

def create_dropdowns5(dataframe):
    dropdowns5 = dbc.Row(
            [

                dbc.Col(
                    dbc.Col([dbc.Alert(html.P("Seleccione el parámetro a estudiar:", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        options=[
                            {'label': 'Casos diarios', 'value': 'diarios'},
                            {'label': 'Casos totales', 'value': 'totales'}
                        ],
                        value='totales',
                        id='dropdown-casos-style',
                    )]),
                    width=3
                ),

                dbc.Col(
                    dbc.Col([dbc.Alert(html.P("Seleccione el país: ", style={'fontSize': 14}), color="secondary"),
                    dcc.Dropdown(
                        id='select-country5',
                        options=[{'label': i, 'value': i} for i in dataframe.Country.unique()],
                        value= 'Spain',
                        multi=False,
                    )]),
                    width=3
                )
            ],
            id = 'main-left-col'
        )
    return dropdowns5



def create_graficos():  
    graph = dcc.Graph(id='grafos')
    content = html.Div(graph, id='content')
    return content


body5 = dbc.Container(
    [
        create_dropdowns5(df_covid),
        create_graficos(),
    ],
    style=CONTENT_STYLE,
    fluid=True,
)

#
# Arriba vimos que definimos diferentes páginas a las que nos lleva el menú. Esta llamada (callback) utiliza
# la ruta actual para establecer el enlace de navegación que queramos activar (correspondiente a True). De esta
# manera permitimos a los usuarios ver la página en la que se encuentran y que sea una interfaz agradable e 
# intuitiva.
# 


# Creamos la llamada para cambiar de páginas (las páginas que creamos arriba)
@app.callback(
    [Output(f"page-{i}-link", "active") for i in range(1, 4)],
    [Input("url", "pathname")],
)
def toggle_active_links(pathname):
    if pathname == "/":
        # Definimos la página 1 como la homepage
        return True, False, False
    return [pathname == f"/page-{i}" for i in range(1, 4)]

# defino qué contenido hay en cada pathname
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname in ["/", "/conexiones_aereas_wuhan"]:
        return body
    elif pathname == "/impacto_global":
        return body4
    elif pathname == "/impacto_por_pais":
        return body5
    #elif pathname == "/page-4":
    #    return body5


    # También contemplo la opción de que el usuario, por error, trate de llegar a una página que no he creado,
    #  entonces salta un error con un mensaje informativo
    return dbc.Jumbotron(
        [
            html.H1("404: Página no encontrada", className="text-danger"),
            html.Hr(),
            html.P(f"Lo sentimos, no hemos reconocido {pathname}. Seguramente sea un fallo nuestro, estamos tratando de solucionarlo. Ayúdenos asegurándose de que está bien."),
        ]
    )



#############################################################################################################################################################

"""
Esta es la madre del cordero. Hemos permitido que hayan interacciones entre el usuario y la app. Ahora 
estáblecemos qué ocurre cuando el usuario escoge distintos valores. Para actualizar correctamente los 
distintos tipos de visualización y que no haya posibilidad de error al, por ejemplo, no seleccionar el valor
de un campo.
"""





# Callback para el mapa de la página 1. 
# Realizamos lo mismo para el mapa de la página 1. Como inputs tiene los valores que el usuario escoge del 
# dropdown tipo de mapa y como output me da una figura que rellena el grafo vació que creé arriba.
# Como vemos: dash funciona mediante llamadas a las "ids" de cada objeto creado.

# de salida quiero el grafo, el grafo vacío que creamos arriba
@app.callback(
    output=Output('graph-geo', 'figure'),
    inputs=[Input('dropdown-map-style', 'value')])
            # si creo más dropdowns tengo que ponerlos aquí

# Según los valores para el estilo del mapa, la región o el país; se actualizará de forma distinta el mapa
def _update_graph(map_style):

    dff = rutas

    # Creamos un layout (una capa) para el mapa. Es decir, creo un marco con el estilo que definí arriba 
    # que será la base en la que se irán visualizando las opciones que escoge el consumidor. 
    
    layout = go.Layout(
        autosize=True,
        hovermode='closest',   # cuestión de estilo!
        height=750,
        #width=1600,
        font=dict(family=theme['font-family']),
        margin=go.Margin(l=2, r=0, t=45, b=10),
        mapbox=dict(
            accesstoken=mapbox_access_token,  # el token de arriba
            bearing=0,
            center=dict(
                lat=30,  # centrar el mapa en asia
                lon=100,
            ),
            pitch=0,
            zoom=2,  
            style="light",   # coge los valores del dropdown del estilo del mapa
        ),
    )

    # Parte de los datos: rellenamos el mapa

    data = go.Data([
        # Representamos los aeropuertos con círculos (distintos colores según si son aeropuertos o qué son)
        go.Scattermapbox(
            lat=dff['Start_Latitude'],
            lon=dff['Start_Longitude'],
            mode='markers',
            marker=go.Marker(
                colorscale=colorscale_depth,
                color="blue",
                opacity=1,
            ),
            text=dff[['Name',"Country"]],    
            hoverinfo='text', #la información que sale en cada punto, puedo elegir que me diga más información
            
        ),


    ])

    # junto todas las cosas que he creado y así voy actualizando el mapa!
    figure = go.Figure(data=data, layout=layout)

    #
    # A continuación represento las rutas, para ello trazo líneas entre las coordenadas iniciales calculadas
    # y las coordenadas finales calculadas.
    #

    for i in range(len(rutas)):
        figure.add_trace(
                go.Scattermapbox(
                    #locationmode = 'USA-states',
                    lon = [rutas['Start_Longitude'][i], rutas['Final_Longitude'][i]],
                    lat = [rutas['Start_Latitude'][i], rutas['Final_Latitude'][i]],
                    mode = 'lines',
                    line = dict(width = 1,color = 'red'),
                    text=dff["City"][i],
                    hoverinfo='text',
                )
            )


    return figure


# Callback página 3

@app.callback(
    output=Output('graph-geo4', 'figure'),
    inputs=[Input('dropdown-map-style4', 'value'),
            Input('dropdown-parameter4', 'value'),
            #Input('select-country4', 'value'),
            Input('dropdown-region4', 'value'),
            Input('slider', 'value')])


# Lo mismo, actualizo dependiendo de los valores que escoja el consumidor (introduzco el parámetro a estudiar
#  y el día de interés)

def _update_graph4(map_style, parameter, region, selected_day):
    
    dff = df_covid

    # Creamos un layout (una capa) para el mapa. Es decir, creo un marco con el estilo que definí arriba 
    # que será la base en la que se irán visualizando las opciones que escoge el consumidor. 
    
    layout4 = go.Layout(
        autosize=True,
        hovermode='closest',  
        height=750,
        #width=1600,
        font=dict(family=theme['font-family']),
        margin=go.Margin(l=2, r=0, t=45, b=10),
        mapbox=dict(
            accesstoken=mapbox_access_token,  
            bearing=0,
            center=dict(
                lat=regions[region]['lat'],  
                lon=regions[region]['lon'],
            ),
            pitch=0,
            zoom=regions[region]['zoom'], 
            style=map_style,  
        ),
    )

    # Parte del slider (para saber con qué datos relleno el mapa)
    filtered_df = dff[dff.Time == df_covid_esp.Time.unique()[selected_day]]


    if parameter in ['Confirmados diarios']:


        data4 = go.Data([
            go.Scattermapbox(
                lat=filtered_df['Latitude'],
                lon=filtered_df['Longitude'],
                mode='markers',
                marker=go.Marker(   
                    colorscale=colorscale_depth,
                    opacity=0.5,
                    size=(filtered_df[parameter]/80.0),
                ),
                text=filtered_df[["Country", "Province/State", parameter]],    
                hoverinfo='text', #la información que sale en cada punto
                # si pongo tupla me dice más cosas (lot, lan)
            ),
            ])
    
    elif parameter in ['Muertos diarios', 'Recuperados diarios']:

        if selected_day < 50:

            data4 = go.Data([
                # inner circles represent airports
                go.Scattermapbox(
                    lat=filtered_df['Latitude'],
                    lon=filtered_df['Longitude'],
                    mode='markers',
                    marker=go.Marker(
                        colorscale=colorscale_depth,
                        #color=dff.apply(lambda x: elegir_color(x['Type']), axis=1),
                        opacity=0.5,
                        size=(filtered_df[parameter]/1.0),
                    ),
                    text=filtered_df[["Country", "Province/State", parameter]],    
                    hoverinfo='text', #la información que sale en cada punto   
                ),
                ])

        else:
            data4 = go.Data([
                # inner circles represent airports
                go.Scattermapbox(
                    lat=filtered_df['Latitude'],
                    lon=filtered_df['Longitude'],
                    mode='markers',
                    marker=go.Marker(
                        colorscale=colorscale_depth,
                        #color=dff.apply(lambda x: elegir_color(x['Type']), axis=1),
                        opacity=0.5,
                        size=(filtered_df[parameter]/5.0),
                    ),
                    text=filtered_df[["Country", "Province/State", parameter]],    
                    hoverinfo='text', #la información que sale en cada punto
                ),
                ])


    else:
        data4 = go.Data([
            # inner circles represent airports
            go.Scattermapbox(
                lat=filtered_df['Latitude'],
                lon=filtered_df['Longitude'],
                mode='markers',
                marker=go.Marker(
                    colorscale=colorscale_depth,
                    #color=dff.apply(lambda x: elegir_color(x['Type']), axis=1),
                    opacity=0.5,
                    size=(filtered_df[parameter]/5.0),
                ),
                text=filtered_df[["Country", "Province/State", parameter]],    
                hoverinfo='text', #la información que sale en cada punto
                # si pongo tupla me dice más cosas (lot, lan)
            ),
            ])



    # junto todas las cosas que he creado
    figure = go.Figure(data=data4, layout=layout4)
    return figure

#
# Callback página 5
# 


@app.callback(
    output=Output('grafos', 'figure'),
    inputs=[Input('select-country5', 'value'),
    Input('dropdown-casos-style', 'value')])


def _update_graph5(country, parametro):

    # Para China y Francia, los datos recogidos se dividen en múltiples regiones. Para que la visualización sea
    # fácil de interpretar e intuitiva y además refleje la realidad; lo mejor es seleccionar las regiones de
    # París y Hubei puesto que tienen más del 99% de los casos de dichos países.

    if country=="China":
        dff = df_covid[df_covid["Province/State"] == "Hubei"] 
    
    elif country=="France":
        dff = df_covid_fra[df_covid_fra["Province/State"] == "Paris"] 
    elif country:
        dff = df_covid[df_covid.Country == country]
    else:
        dff = df_covid_esp

    if parametro in ["diarios"]:

        figure = go.Figure()
        figure.add_trace(go.Bar(x=dff['Time'], y=dff['Muertos diarios'], name='Muertos'))
        figure.add_trace(go.Bar(x=dff['Time'], y=dff['Confirmados diarios'], name='Confirmados'))
        figure.add_trace(go.Bar(x=dff['Time'], y=dff['Recuperados diarios'], name='Recuperados'))

        figure.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1 month", step="month", stepmode="backward"),
                    dict(count=7, label="1 week", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )

        figure.update_layout(
            autosize=False,
            width = 800,
            height = 500,
            title="Datos acerca del Covid-19",
            xaxis_title="Días",
            yaxis_title="Número de personas afectadas",

        )

        figure.update_layout(hovermode="x")


    else:

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=dff['Time'], y=dff['Suma muertos'], name='Muertos', mode="lines"))
        figure.add_trace(go.Scatter(x=dff['Time'], y=dff['Suma confirmados'], name='Confirmados', mode="lines"))
        figure.add_trace(go.Scatter(x=dff['Time'], y=dff['Suma recuperados'], name='Recuperados', mode="lines"))



        figure.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1 month", step="month", stepmode="backward"),
                    dict(count=7, label="1 week", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )

        figure.update_layout(
            #autosize=False,
            width = 800,
            height = 500,
            title="Datos acerca del Covid-19",
            xaxis_title="Días",
            yaxis_title="Número de personas afectadas",
            #hovermode="x",
        )

        figure.update_layout(hovermode="x")


    return figure



############################################################################################################################################################

if __name__ == "__main__":
    app.run_server()
