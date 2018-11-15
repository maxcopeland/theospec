import ast
import itertools
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from scipy.interpolate import interp1d
from tmm.color import calc_reflectances

from app import app, db
from app.models import User, Post, Material, NKValues


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

simulator = dash.Dash(name='simulator', external_stylesheets=external_stylesheets, 
                      sharing=True, server=app, url_base_pathname='/data/')

simulator.config['suppress_callback_exceptions']=True

max_layers = 10

simulator.layout= html.Div(
    [
        html.Div([
            html.Span("theospec", 
                className='app-title',
                style={
                    "color": "white",
                    "fontSize": "42px",
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "marginBottom": "0",
                    "marginTop": "5",
                    "marginLeft": "10",
                }
                ),
            ],
            className="row header",
            style={
                'height':'80',
                'backgroundColor':'#506784',
                'border': '1px solid #C8D4E3',
            }
        ),
        html.Div([ # Input/Plot row
            html.Div(
                [ # Left side of page
                    html.Div( 
                        [ # Top input row, left side
                            html.Div( # Medium box
                                [
                                    html.P( # Medium box title
                                        'Medium',
                                        style={
                                            "color": "#506784",
                                            "fontSize": "16px",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "marginBottom": "0",
                                            "marginTop": "5"
                                        },
                                    ),
                                    html.Div( # Medium radio buttons
                                        dcc.RadioItems(
                                            id='medium',
                                            options=[
                                                {'label':'Air', 'value':1},
                                                {'label':'Water', 'value':1.3333}
                                            ]
                                        ), 
                                        style={"padding": "0px 5px 5px 5px", "marginBottom": "5"}, 
                                    )
                                ],  
                                className='four columns',
                                style={
                                    "backgroundColor": "white",
                                    "border": "1px solid #C8D4E3",
                                    "borderRadius": "3px",
                                    "height": "100%",
                                },
                            ),
                            html.Div( # Pattern density box
                                [
                                    html.P( # Pattern density title
                                        'Pattern Density',
                                        style={
                                            "color": "#506784",
                                            "fontSize": "16px",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "marginBottom": "0",
                                            "marginTop": "5"
                                        },
                                    ),
                                    dcc.Slider( # Pattern density slider
                                        id='pattern-density-slider',
                                        min=0,
                                        max=100,
                                        step=5,
                                        value=50,
                                    ),
                                    html.Div( # Output from slider
                                        id='slider-output', 
                                        style=
                                            {
                                                'textAlign':'center',
                                                "padding": "5px 13px 0px 13px",
                                                "marginTop": "5",
                                                "marginBottom": "0"
                                            }
                                    )
                                ],
                                className='four columns',
                                style={
                                        "backgroundColor": "white",
                                        "border": "1px solid #C8D4E3",
                                        "borderRadius": "3px",
                                        "height": "100%",
                                        # "overflowY": "scroll",
                                }
                            ),
                            html.Div( # Removal rate input box
                                [
                                    html.P( # Removal rate title
                                        'Removal Rate',
                                        style={
                                            "color": "#506784",
                                            "fontSize": "16px",
                                            "fontWeight": "bold",
                                            "textAlign": "center",
                                            "marginBottom": "5",
                                            "marginTop": "5"
                                        },
                                    ),
                                    html.Div( # Removal rate input
                                        [
                                            dcc.Input(
                                                id='removal-rate', 
                                                type='text', 
                                                placeholder='1000',
                                                value=1000,
                                                size=10,
                                            ),
                                            html.Span(' A/min')
                                        ],
                                        style=
                                            {
                                                "padding": "5px 13px 5px 13px", 
                                                "marginBottom": "5",
                                                "marginTop": "5",
                                                "textAlign": "center",
                                                "horizontalAlign": "middle",
                                                "verticalAlign": "middle"
                                            },
                                        className="row"
                                    ),
                                ],
                                className='four columns',
                                style={
                                    "backgroundColor": "white",
                                    "border": "1px solid #C8D4E3",
                                    "borderRadius": "3px",
                                    "height": "100%",
                                    },
                            ),
                            # html.Div(
                            #     html.H3('Plot'), 
                            #     className='six columns', 
                            #     style={'textAlign':'center'})
                        ], 
                        className='row',
                    ),
                    html.Div( # Stack layer input row, left side
                        [
                            html.Div([ # Active stack layer input
                                html.H3(
                                    "Active Stack",
                                    style={
                                        "color": "#506784",
                                        "fontWeight": "bold",
                                        "fontSize": "24",
                                    },
                                ),
                                html.Div(
                                    dcc.Dropdown(id='active_nlayers_dropdown', 
                                                options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                                                placeholder='Select Film Layers'),
                                    style={
                                        'width':'30%',
                                        'textAlign': 'center',
                                        'display':'table-cell'
                                    }),
                                html.Div(id='active-controls-container', className='row'),
                                dcc.Input(
                                    id='active-input-box', 
                                    type='text', 
                                    placeholder='Si Substrate',
                                    disabled=True,
                                    style={
                                        'textAlign':True
                                    }
                                ), 
                                ], 
                                className="six columns",
                                style={
                                    "backgroundColor": "white",
                                    # "border": "1px solid #C8D4E3",
                                    # "borderRadius": "3px",
                                    "height": "100%",
                                    "paddingTop": "15"
                                    },
                            ),
                            html.Div([ # Trench stack layer input 
                                html.H3(
                                    "Trench Stack",
                                    style={
                                        "color": "#506784",
                                        "fontWeight": "bold",
                                        "fontSize": "24",
                                    },
                                ),
                                html.Div(
                                    dcc.Dropdown(id='trench_nlayers_dropdown', 
                                                options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                                                placeholder='Select Film Layers'),
                                    style={
                                        'width':'30%',
                                        'textAlign': 'center',
                                        'display':'table-cell'
                                    }),
                                html.Div(id='trench-controls-container', className='row'),
                                dcc.Input( # Si placeholder
                                    id='trench-input-box', 
                                    type='text', 
                                    placeholder='Si Substrate',
                                    disabled=True,
                                    style={
                                        'textAlign':'center'
                                    }
                                ), 
                                ], 
                                className="six columns",
                                style={
                                    "backgroundColor": "white",
                                    # "border": "1px solid #C8D4E3",
                                    # "borderRadius": "3px",
                                    "height": "100%",
                                    "paddingTop": "15"
                                    },
                            )
                        ],
                        className='row'
                    ),
                ],
                className='six columns',
            ),
            html.Div([
                html.Div(id='data-output-active', style={'display':'none'}),
                html.Div(id='data-output-trench', style={'display':'none'}),
                html.Div(id='data-output')
                ], 
                className='six columns'
            )
        ],
        className='row',
        style={
            "margin":"2%"
        }
    ),
    html.Div( # Button row
        html.Button('Calculate', id='calculate'),
        className='eight columns',
        style={
            'float':'right'
        }
    ),
    ],
)


state_components = { # dict comp of all possible n_layers of active stack
i : [dash.dependencies.State('film-{}'.format(x), 'value') for x in range(i)] + 
    [dash.dependencies.State('thickness-{}'.format(x), 'value') for x in range(i)] for i in range(1, max_layers)
        }

input_components = { # dict comp of all possible n_layers of active stack
i : [dash.dependencies.Input('film-{}'.format(x), 'value') for x in range(i)] + 
    [dash.dependencies.Input('thickness-{}'.format(x), 'value') for x in range(i)] for i in range(1, max_layers)
        }

def create_possible_stacks(stack_type, film_options=[1,2,3,4], max_layers=max_layers):
    """ Function to generate components for stack layers
    
    inputs
    ------
    
    stack_type: str, assigned to prefix of each unique component id
    
    film_options: film possiblities for given layer (pull from db)
    
    max_layers: maximum number of layers that can be created
    
    output
    ------
    
    dict:
        key- int, n layers in stack
        value- n rows of layer html components
        
        """
    possible_stacks = {}
    for n in range(1, max_layers):
        rows = []
        for i in range(1, n+1):
            row = html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='{}-film-{}'.format(stack_type, i), 
                            placeholder='Film',
                            options=[{'label':mat.name, 'value':mat.name} for mat in Material.query.all()])
                        ], 
                        style= {
                            'width':'30%', 
                            'display':'table-cell'
                        }
                    ),
                    html.Div([
                        dcc.Input(id='{}-thickness-{}'.format(stack_type, i),placeholder="Layer {}".format(i), type='text')
                        ],
                        style={
                            'width':'30%',
                            'display':'table-cell'
                        }
                    )
                ], className="row")
            rows.append(row)
        possible_stacks[n] = list(reversed(rows))
    return possible_stacks

active_layers = create_possible_stacks('active')
trench_layers = create_possible_stacks('trench')

@simulator.callback(
    Output('slider-output', 'children'),
    [Input('pattern-density-slider', 'value')]
)
def pattern_density_div(value):
    return '{}%'.format(value)

@simulator.callback(
    dash.dependencies.Output('active-controls-container', 'children'),
    [dash.dependencies.Input('active_nlayers_dropdown', 'value')])
def render_active_components(n):
    # trigger page refresh?
    if n:
        return active_layers[n]

@simulator.callback(
    dash.dependencies.Output('trench-controls-container', 'children'),
    [dash.dependencies.Input('trench_nlayers_dropdown', 'value')])
def render_trench_components(n):
    # trigger page refresh?
    if n:
        return trench_layers[n]


def generate_output_id_active(n):
    return 'Active container {}'.format(n)

def generate_output_id_trench(n):
    return 'Trench container {}'.format(n)


@simulator.callback(
    Output('data-output-active', 'children'),
    [Input('active_nlayers_dropdown', 'value')]
)
def display_controls_active(n):
    return html.Div('Controls container for active {}'.format(n), id=generate_output_id_active(n))

@simulator.callback(
    Output('data-output-trench', 'children'),
    [Input('trench_nlayers_dropdown', 'value')]
)
def display_controls_trench(n):
    return html.Div('Controls container trench {}'.format(n), id=generate_output_id_trench(n))


# Func called to all stack data entry callbacks
def stack_calc(values):
    # TODO- cleaner parsing

    films = []
    for val in values[::2]:
        films.append(str(val))
    thks = []
    for val in values[1::2]:
        thks.append(int(val))
    return str(films) + '*' + str(thks) #data to be parsed from hidden div-- split on "*"







#### TRENCH STACK LAYER CALLBACKS
# Callback for one layer stack
@simulator.callback(
    Output(generate_output_id_trench(1), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value')])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for two layer stack
@simulator.callback(
    Output(generate_output_id_trench(2), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value')])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for three layer stack
@simulator.callback(
    Output(generate_output_id_trench(3), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for four layer stack
@simulator.callback(
    Output(generate_output_id_trench(4), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for five layer stack
@simulator.callback(
    Output(generate_output_id_trench(5), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value'),
    State('trench-film-{}'.format(5), 'value'),
    State('trench-thickness-{}'.format(5), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for six layer stack
@simulator.callback(
    Output(generate_output_id_trench(6), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value'),
    State('trench-film-{}'.format(5), 'value'),
    State('trench-thickness-{}'.format(5), 'value'),
    State('trench-film-{}'.format(6), 'value'),
    State('trench-thickness-{}'.format(6), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for seven layer stack
@simulator.callback(
    Output(generate_output_id_trench(7), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value'),
    State('trench-film-{}'.format(5), 'value'),
    State('trench-thickness-{}'.format(5), 'value'),
    State('trench-film-{}'.format(6), 'value'),
    State('trench-thickness-{}'.format(6), 'value'),
    State('trench-film-{}'.format(7), 'value'),
    State('trench-thickness-{}'.format(7), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for eight layer stack
@simulator.callback(
    Output(generate_output_id_trench(8), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value'),
    State('trench-film-{}'.format(5), 'value'),
    State('trench-thickness-{}'.format(5), 'value'),
    State('trench-film-{}'.format(6), 'value'),
    State('trench-thickness-{}'.format(6), 'value'),
    State('trench-film-{}'.format(7), 'value'),
    State('trench-thickness-{}'.format(7), 'value'),
    State('trench-film-{}'.format(8), 'value'),
    State('trench-thickness-{}'.format(8), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for nine layer stack
@simulator.callback(
    Output(generate_output_id_trench(9), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value'),
    State('trench-film-{}'.format(2), 'value'),
    State('trench-thickness-{}'.format(2), 'value'),
    State('trench-film-{}'.format(3), 'value'),
    State('trench-thickness-{}'.format(3), 'value'),
    State('trench-film-{}'.format(4), 'value'),
    State('trench-thickness-{}'.format(4), 'value'),
    State('trench-film-{}'.format(5), 'value'),
    State('trench-thickness-{}'.format(5), 'value'),
    State('trench-film-{}'.format(6), 'value'),
    State('trench-thickness-{}'.format(6), 'value'),
    State('trench-film-{}'.format(7), 'value'),
    State('trench-thickness-{}'.format(7), 'value'),
    State('trench-film-{}'.format(8), 'value'),
    State('trench-thickness-{}'.format(8), 'value'),
    State('trench-film-{}'.format(9), 'value'),
    State('trench-thickness-{}'.format(9), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)


#### ACTIVE STACK LAYER CALLBACKS
# Callback for one layer stack
@simulator.callback(
    Output(generate_output_id_active(1), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for two layer stack
@simulator.callback(
    Output(generate_output_id_active(2), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value')])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for three layer stack
@simulator.callback(
    Output(generate_output_id_active(3), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for four layer stack
@simulator.callback(
    Output(generate_output_id_active(4), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for five layer stack
@simulator.callback(
    Output(generate_output_id_active(5), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value'),
    State('active-film-{}'.format(5), 'value'),
    State('active-thickness-{}'.format(5), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for six layer stack
@simulator.callback(
    Output(generate_output_id_active(6), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value'),
    State('active-film-{}'.format(5), 'value'),
    State('active-thickness-{}'.format(5), 'value'),
    State('active-film-{}'.format(6), 'value'),
    State('active-thickness-{}'.format(6), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for seven layer stack
@simulator.callback(
    Output(generate_output_id_active(7), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value'),
    State('active-film-{}'.format(5), 'value'),
    State('active-thickness-{}'.format(5), 'value'),
    State('active-film-{}'.format(6), 'value'),
    State('active-thickness-{}'.format(6), 'value'),
    State('active-film-{}'.format(7), 'value'),
    State('active-thickness-{}'.format(7), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for eight layer stack
@simulator.callback(
    Output(generate_output_id_active(8), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value'),
    State('active-film-{}'.format(5), 'value'),
    State('active-thickness-{}'.format(5), 'value'),
    State('active-film-{}'.format(6), 'value'),
    State('active-thickness-{}'.format(6), 'value'),
    State('active-film-{}'.format(7), 'value'),
    State('active-thickness-{}'.format(7), 'value'),
    State('active-film-{}'.format(8), 'value'),
    State('active-thickness-{}'.format(8), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for nine layer stack
@simulator.callback(
    Output(generate_output_id_active(9), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value'),
    State('active-film-{}'.format(2), 'value'),
    State('active-thickness-{}'.format(2), 'value'),
    State('active-film-{}'.format(3), 'value'),
    State('active-thickness-{}'.format(3), 'value'),
    State('active-film-{}'.format(4), 'value'),
    State('active-thickness-{}'.format(4), 'value'),
    State('active-film-{}'.format(5), 'value'),
    State('active-thickness-{}'.format(5), 'value'),
    State('active-film-{}'.format(6), 'value'),
    State('active-thickness-{}'.format(6), 'value'),
    State('active-film-{}'.format(7), 'value'),
    State('active-thickness-{}'.format(7), 'value'),
    State('active-film-{}'.format(8), 'value'),
    State('active-thickness-{}'.format(8), 'value'),
    State('active-film-{}'.format(9), 'value'),
    State('active-thickness-{}'.format(9), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)


def generate_data_output_id(n1, n2):
    return 'Data Output for {} active layers and {} trench layers'.format(n1, n2)


@simulator.callback(
    Output('data-output', 'children'),
    [Input('calculate', 'n_clicks'),
    Input('active_nlayers_dropdown', 'value'),
    Input('trench_nlayers_dropdown', 'value')]
)
def create_data_container(n_clicks, n_active, n_trench):
    if n_clicks:
        print(generate_data_output_id(n_active, n_trench))
        return html.Div(id=generate_data_output_id(n_active, n_trench))

def get_nkvals(mat_name):
    mat_id = Material.query.filter_by(name=mat_name).first().id
    nk_vals = NKValues.query.filter_by(material_id=mat_id).all()
    df = pd.DataFrame([(d.wavelength, d.n_value, d.k_value) for d in nk_vals], 
                  columns=['wavelength', 'n', 'k'])
    df['nk'] = df['n'] + (1j * df['k'])
    ### Handle nm from data instead of Angstrom
    ## TODO- make more robust
    if df.wavelength.min() > 1000:
        df['wavelength'] = df.wavelength /10
    return df

def compute_reflectance(mat_names, thicknesses, medium):
    """
    Compute reflectances of given film stack

    input
    ======

    mat_names: list
        string names of film type
    thicknesses: list
        int values of film thicknesses in Angstroms
    medium: float
        index of refraction of medium on top of stack (air, water, etc)

    output
    ======

    pandas DataFrame
        columns: wavelength, reflectance

    """

    mat_fns = []
    for mat in mat_names:
        mat_df = get_nkvals(mat)
        mat_fn = interp1d(mat_df.wavelength, mat_df.nk, kind='linear')
        mat_fns.append(mat_fn)
    medium_fn = lambda wavelength: medium
    si_df = get_nkvals('Si') ## change to make film passable
    si_fn = interp1d(si_df.wavelength, si_df.nk, kind='linear')
    reflectance = calc_reflectances(n_fn_list=[medium_fn] + mat_fns + [si_fn], 
                                    d_list=[np.inf] + thicknesses + [np.inf], 
                                    th_0=0, 
                                    spectral_range=(260, 1700))
    r_df = pd.DataFrame(reflectance, columns=['wavelength', 'r'])
    return r_df

def spectra_calc_2d():
    """
    Calculate spectra for 2D plot
    
    """
    pass

def spectra_calc_3d():
    """
    Calculate spectra for 3D plot
    
    """
    pass


def generate_callback(n1, n2):
    def callback_data(x1, x2, medium, pattern_density, rr):
        # print('test total value for {} and {}'.format(n1, n2))
        # print('Incoming for x1: {},\n Incoming for x2:{}'.format(x1, x2))
    
        #BUG: active and trench cant have different number of layers?


        active_films = ast.literal_eval(x1.split('*')[0])
        active_thks = ast.literal_eval(x1.split('*')[1])
        active_r = compute_reflectance(active_films, active_thks, medium) #BUG: calculating twice?

        trench_films = ast.literal_eval(x2.split('*')[0])
        trench_thks = ast.literal_eval(x2.split('*')[1])
        trench_r = compute_reflectance(trench_films, trench_thks, medium) #BUG: calculating twice?


        # print('Active', active_r.head())
        # print('Trench', trench_r.head())
        base_reflectance = trench_r.values 
        ref_si = compute_reflectance(['Si'], [50000], 1.33333)

        np.multiply(base_reflectance[:,1], (1 - (pattern_density/100)), base_reflectance[:,1])
        np.add(base_reflectance[:,1], active_r.r*(pattern_density/100), base_reflectance[:,1])
        np.divide(base_reflectance[:,1], ref_si.r, base_reflectance[:,1])
        # print('Parsed Incoming active films: {}'.format(active_films))
        # print('Parsed Incoming active thks: {}'.format(active_thks))
        # print('Parsed Incoming trench films: {}'.format(trench_films))
        # print('Parsed Incoming trench thks: {}'.format(trench_thks))
        graph = html.Div([
            # html.Div(str(slider) + str(medium) + str(rr)),
            dcc.Graph(
                figure={
                    'data': [
                        {
                            'x':base_reflectance[:,0],
                            'y':base_reflectance[:,1],
                            'mode': 'line',
                            'name': 'Reflectance'
                        }
                    ],
                    'figure': go.Layout(
                        xaxis={'title':'reflectance'},
                        yaxis={'title':'wavelength'}
                    )
                }
            )
        ])
        return graph
    return callback_data

## Callback to put all input data into one div 
for val1, val2 in itertools.product(np.arange(1, max_layers), np.arange(1, max_layers)):
    simulator.callback(
        Output(generate_data_output_id(val1, val2), 'children'),
        [Input(generate_output_id_active(val1), 'children'), 
         Input(generate_output_id_trench(val2), 'children')],
        [State('medium', 'value'),
         State('pattern-density-slider', 'value'),
         State('removal-rate', 'value')])(
             generate_callback(val1, val2)
         )