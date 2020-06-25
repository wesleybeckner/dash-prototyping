# -*- coding: utf-8 -*-
import dash
import io
import base64
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import dash_table
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px
import json
from utils import *
import scipy

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


production_df = pd.read_csv('data/films_products_and_lines.csv')
metric = margin_column = 'EBITDA (€)'
volume_column = 'Net Sales Quantity in KG'
descriptors = list(production_df.columns[:12]) #8 for old 12 for new
stat_df = pd.read_csv('data/category_stats.csv')


PLOTLY_LOGO = "https://images.plot.ly/logo/new-branding/plotly-logomark.png"
def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return df
search_bar = dbc.Row(
    [
        dbc.Col(html.Img(src='assets/mfg_logo.png', height="30px")),
    ],
    no_gutters=True,
    className="ml-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

navbar = dbc.Navbar(
    [
            dbc.Row(
                [
                    dbc.Col(html.Img(src='assets/caravel_logo.png', height="30px")),

                ],
                align="center",
                # no_gutters=True,
            ),
        #     href="https://plot.ly",
        # ),

        # dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
    ],
    color="light",
    dark=False,
)

CONTROLS = html.Div([
    html.P('Filter'),
    dcc.Dropdown(id='filter_dropdown_1',
                 options=[{'label': i, 'value': i} for i in
                            descriptors],
                 value=descriptors[1],
                 multi=False,
                 className="dcc_control"),
    dcc.Dropdown(id='filter_dropdown_2',
                 multi=True),
])

UPLOAD = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '95%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    html.P('Margin Column'),
    html.P(id='bleh'),
    dcc.Dropdown(id='upload-margin',
                 multi=False,
                 options=[],
                 className="dcc_control",
                 style={'textAlign': 'center',
                        'margin-bottom': '10px'}),
    html.P('Descriptor-Attribute Columns'),
    dcc.Dropdown(id='upload-descriptors',
                 multi=True,
                 options=[],
                 className="dcc_control",
                 style={'textAlign': 'center',
                        'margin-bottom': '10px'}),
    html.Button('Proccess data file',
                id='datafile-button',
                style={'textAlign': 'center',
                       'margin-bottom': '10px'}),
    html.Div(id='production-df-upload',
             style={'display': 'none'}),
    html.Div(id='stats-df-upload',
             style={'display': 'none'}),
    html.Div(id='descriptors-upload',
             style={'display': 'none'}),
    html.Div(id='metric-upload',
             style={'display': 'none'})
],)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')
app.layout = html.Div([navbar,
html.Div([
html.Div([
html.Div([
    dcc.Tabs([
        dcc.Tab(label='Tab one', value='tab-1', children=[UPLOAD]),
        dcc.Tab(label='Tab two', value='tab-2', children=[
            dcc.Graph(id='tab2fig',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [1, 4, 1],
                            'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [1, 2, 3],
                         'type': 'bar', 'name': u'Montréal'},
                    ]
                }
            )
        ]),
        dcc.Tab(label='Tab three', value='tab-3', children=[CONTROLS]),
        ], value='tab-3'),
    ], className='mini_container', id='explain1a'),
    html.Div([
    html.P(''),
    dcc.Loading(id='loading-1',
                type='default',
                children=dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df.columns],
    data=df.to_dict("rows"),
),),
    ], className='mini_container',
       id='ebit-family-block',
       style={'overflow': 'scroll',
              'max-height': '800px'}),
    ], className='row container-display'),
], className='pretty_container'),
],)

#updates production_df dependent variables
@app.callback(
    [Output('filter_dropdown_2', 'options'),
     Output('filter_dropdown_2', 'value')],
    [Input('filter_dropdown_1', 'value')]
)
def update_filter(category):
    return [{'label': i, 'value': i} for i in production_df[category].unique()],\
        list(production_df[category].unique())

@app.callback(
    [Output('stats-df-upload', 'children'),
    Output('descriptors-upload', 'children'),
    Output('metric-upload', 'children'),],
    [Input('production-df-upload', 'children'),
    Input('upload-margin', 'value'),
    Input('upload-descriptors', 'value'),
    Input('datafile-button', 'n_clicks'),]
)
def update_variables(df, metric, descriptors, button):
    ctx = dash.callback_context
    df = pd.read_json(df)

    if ctx.triggered[0]['prop_id'] == 'datafile-button.n_clicks':
        category_stats = my_median_test(df, metric=metric,
            descriptors=descriptors, stat_cut_off=0.01)
        return category_stats.to_json(), descriptors, metric
#updates production_df
@app.callback(
    [Output('upload-margin', 'options'),
   Output('upload-descriptors', 'options'),
   Output('table', 'data'),
   Output('table', 'columns'),
   Output('production-df-upload', 'children'),],
  [Input('upload-data', 'contents'),],
  [State('upload-data', 'filename'),
   State('upload-data', 'last_modified')])
def update_production_df_and_table(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        df = [parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        df = df[0]
        columns = [{'label': i, 'value': i} for i in df.columns]
        columns_table = [{"name": i, "id": i} for i in df.columns]
        return columns, columns, df.to_dict('rows'), columns_table,\
            df.to_json()

@app.callback(
    Output('tab2fig', 'figure'),
    [Input('production-df-upload', 'children')]
)
def update_tab2fig(js):

    if js is not None:
        df = pd.read_json(js)
        return px.scatter(df, 'Adjusted EBITDA', 'EBIT')
    else:
        return {
            'data': [
                {'x': [1, 2, 3], 'y': [1, 4, 1],
                    'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [1, 2, 3],
                 'type': 'bar', 'name': u'Montréal'},
            ]
        }


if __name__ == '__main__':
    app.run_server(debug=True)
