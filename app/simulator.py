import ast
import itertools
import time
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from scipy.interpolate import interp1d
from .core_tmm import calc_reflectances

from app import app, db
from app.models import User, Post, Material, NKValues


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

simulator = dash.Dash(name='simulator', external_stylesheets=external_stylesheets, 
                      sharing=True, server=app, url_base_pathname='/data/')

simulator.config['suppress_callback_exceptions']=True
simulator.title = 'Simulator'

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
        html.Div( # Input/Plot title row
            [
                html.Div(html.H2('Wafer Info',
                        style={
                                "color": "#506784",
                                # "fontSize": "16px",
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "marginBottom": "0",
                                "marginTop": "5"
                            }
                        ),
                    className='six columns'
                ),
                html.Div(html.H2('Theoretical FV Spectra',
                        style={
                                "color": "#506784",
                                # "fontSize": "16px",
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "marginBottom": "0",
                                "marginTop": "5"
                            }
                        ),
                    className='six columns'
                ),
            ],
            className='row'
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
                                            ],
                                            value=1.3333,
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
                                    [
                                        html.Div(
                                            dcc.Dropdown(id='active_nlayers_dropdown', 
                                                    options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                                                    placeholder='N Layers',
                                                    # style={
                                                    #     'width':'50'
                                                    # }
                                            ),
                                            className='four columns'
                                        ),
                                        html.Div(
                                            dcc.RadioItems(id='active-radio',
                                                        options=[
                                                            {'label':'Custom', 'value':'custom'},
                                                            {'label':'3D NAND', 'value':'nand'}
                                                        ],
                                                        value='custom'
                                            ),
                                            className='four columns'
                                        ),
                                    ],
                                    style={
                                        'width':'30%',
                                        'textAlign': 'center',
                                        'display':'table-cell'
                                    },
                                    className='row'
                                ),
                                html.Div(id='active-controls-container', className='row'),
                                html.Div(id='active-nand-container', style={'display':'none'}),
                                dcc.Input(
                                    id='active-input-box', 
                                    type='text', 
                                    placeholder='Si Substrate',
                                    disabled=True,
                                    style={
                                        'textAlign':'center',
                                        'width':'250',
                                        'backgroundColor':'lightgrey'
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
                                    [
                                        html.Div(
                                            dcc.Dropdown(id='trench_nlayers_dropdown', 
                                                    options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                                                    placeholder='N Layers',
                                                    # style={
                                                    #     'width':'50'
                                                    # }
                                            ),
                                            className='four columns'
                                        ),
                                        html.Div(
                                            dcc.RadioItems(id='trench-radio',
                                                        options=[
                                                            {'label':'Custom', 'value':'custom'},
                                                            {'label':'3D NAND', 'value':'nand'}
                                                        ],
                                                        value='custom'          
                                            ),
                                            className='four columns'
                                        ),
                                    ],
                                    style={
                                        'width':'30%',
                                        'textAlign': 'center',
                                        'display':'table-cell'
                                    },
                                    className='row'
                                ),
                                html.Div(id='trench-controls-container', className='row'),
                                html.Div(id='trench-nand-container', style={'display':'none'}),
                                dcc.Input( # Si placeholder
                                    id='trench-input-box', 
                                    type='text', 
                                    placeholder='Si Substrate',
                                    disabled=True,
                                    style={
                                        'textAlign':'center',
                                        'width':'250',
                                        'backgroundColor':'lightgrey'
                                    }
                                ), 
                                html.Div( # Button row
                                    html.Button('Calculate', 
                                        id='calculate',
                                        style={
                                            'color':'white',
                                            'backgroundColor':'green',
                                        }
                                    ),
                                    # className='eight columns',
                                    style={
                                        'height':'300',
                                        'float':'right',
                                        'marginRight':'0',
                                        'marginTop':'70',
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
                        ],
                        className='row'
                    ),
                ],
                className='six columns',
            ),
            html.Div([
                dcc.Tabs(id='chart-tabs', value='r-spectra', children=[
                    dcc.Tab(label='R Spectra', value='r-spectra'),
                    dcc.Tab(label='2D Spectra', value='contour')
                    ]
                ),
                html.Div(id='data-output-active', style={'display':'none'}),
                html.Div(id='data-output-trench', style={'display':'none'}),
                html.Div(id='data-output'),
                html.Div(id='dummy-graph')
                ], 
                className='six columns'
            )
        ],
        className='row',
        style={
            "margin":"2%"
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
                            placeholder='Layer {} Film'.format(i),
                            options=[{'label':mat.name, 'value':mat.name} for mat in Material.query.all()])
                        ], 
                        style= {
                            'width':'125', 
                            'display':'table-cell'
                        }
                    ),
                    html.Div([
                        dcc.Input(
                            id='{}-thickness-{}'.format(stack_type, i),
                            placeholder="(A)".format(i), 
                            type='text',
                            style={
                                'width':'75',
                                'textAlign':'center'
                            }
                        )
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

def create_nand_stacks(stack_type, nand_layers=2, max_layers=max_layers): # 


    """ Function to generate components for stack layers

    TODO: Dropdown > 7 raises error
    
    inputs
    ------
    
    stack_type: str, assigned to prefix of each unique component id
    
    nand_layers: number of unique NAND layers
    
    max_layers: maximum number of layers that can be created
    
    output
    ------
    
    dict:
        key- int, n layers in stack
        value- n rows of layer html components
        
        """
    nand_base = []

    for i in range(1, nand_layers + 1):
        row = html.Div([
                html.Div([
                    dcc.Dropdown(
                        id='{}-film-{}'.format(stack_type, i), 
                        placeholder='NAND Layer {} Film'.format(i),
                        options=[{'label':mat.name, 'value':mat.name} for mat in Material.query.all()])
                    ], 
                    style= {
                        'width':'125', 
                        'display':'table-cell'
                    }
                ),
                html.Div([
                    dcc.Input(
                        id='{}-thickness-{}'.format(stack_type, i),
                        placeholder="(A)".format(i), 
                        type='text',
                        style={
                            'width':'75',
                            'textAlign':'center'
                        }
                    )
                    ],
                    style={
                        'width':'30%',
                        'display':'table-cell'
                    }
                )
            ], className="row")    
        nand_base.append(row)

    # nand_base = html.Div(nand_base, 
    #                     style={
    #                         'marginTop':'5'
    #                     })

    possible_stacks = {}

    for n in range(1, max_layers - nand_layers):
        rows = []
        for i in range(1, n+1):
            row = html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id='{}-film-{}'.format(stack_type, i+nand_layers), 
                            placeholder='Top Layer {} Film'.format(i),
                            options=[{'label':mat.name, 'value':mat.name} for mat in Material.query.all()])
                        ], 
                        style= {
                            'width':'125', 
                            'display':'table-cell'
                        }
                    ),
                    html.Div([
                        dcc.Input(
                            id='{}-thickness-{}'.format(stack_type, i+nand_layers),
                            placeholder="(A)", 
                            type='text',
                            style={
                                'width':'75',
                                'textAlign':'center'
                            }
                        )
                        ],
                        style={
                            'width':'30%',
                            'display':'table-cell'
                        }
                    )
                ], className="row")

            rows.append(row)
        possible_stacks[n] = list(reversed(rows)) + [html.Div(
                                                        [
                                                            html.Div([
                                                                html.Span('NAND Pairs: ',
                                                                ),
                                                                dcc.Input(
                                                                    id='{}-nand-pairs'.format(stack_type),
                                                                    placeholder='N Pairs',
                                                                    type='text',
                                                                    style={
                                                                        'width':'75'
                                                                    }
                                                                ),
                                                                ],
                                                                style={
                                                                    'display':'inline-block',
                                                                    # 'textAlign':'right',
                                                                    # 'horizontalAlign':'right',
                                                                    'vertical-align':'right',
                                                                }
                                                            ),
                                                            html.Div(list(reversed(nand_base)), 
                                                                    #  style={'marginTop':'10'}
                                                            ),
                                                        ],
                                                        style={
                                                            'marginTop':'15'
                                                        }
                                                    )
                                                    ]
    return possible_stacks

active_layers = create_possible_stacks('active')
trench_layers = create_possible_stacks('trench')

active_nand_stack = create_nand_stacks('active')
trench_nand_stack = create_nand_stacks('trench')

@simulator.callback(
    Output('slider-output', 'children'),
    [Input('pattern-density-slider', 'value')]
)
def pattern_density_div(value):
    return '{}%'.format(value)

@simulator.callback(
    dash.dependencies.Output('active-controls-container', 'children'),
    [dash.dependencies.Input('active_nlayers_dropdown', 'value')],
    [dash.dependencies.State('active-radio', 'value')])
def render_active_components(n_layers, stack_type):
    # trigger page refresh?
    if n_layers:
        if stack_type == 'custom':
            return active_layers[n_layers]
        elif stack_type == 'nand':
            return active_nand_stack[n_layers]

@simulator.callback(
    dash.dependencies.Output('trench-controls-container', 'children'),
    [dash.dependencies.Input('trench_nlayers_dropdown', 'value')],
    [dash.dependencies.State('trench-radio', 'value')])
def render_trench_components(n_layers, stack_type):
    # trigger page refresh?
    if n_layers:
        if stack_type == 'custom':
            return trench_layers[n_layers]
        elif stack_type == 'nand':
            return trench_nand_stack[n_layers]


def generate_output_id_active(n):
    return 'Active container {}'.format(n)

def generate_output_id_trench(n):
    return 'Trench container {}'.format(n)


@simulator.callback( # generate dummy nand-pairs div
    Output('active-nand-container', 'children'),
    [Input('active-radio', 'value')]
)
def create_dummy_drampair_div(stack_type):
    if stack_type == 'custom':
        return html.Div(id='active-nand-pairs')


@simulator.callback( # generate dummy nand-pairs div
    Output('trench-nand-container', 'children'),
    [Input('trench-radio', 'value')]
)
def create_dummy_drampair_div(stack_type):
    if stack_type == 'custom':
        return html.Div(id='trench-nand-pairs')


@simulator.callback(
    Output('data-output-active', 'children'),
    [Input('active_nlayers_dropdown', 'value')],
    [State('active-radio', 'value')]
)
def display_controls_active(n, stack_type):
    if stack_type == 'nand':
        n = n+2
    return html.Div('Controls container for active {}'.format(n), id=generate_output_id_active(n))

@simulator.callback(
    Output('data-output-trench', 'children'),
    [Input('trench_nlayers_dropdown', 'value')],
    [State('trench-radio', 'value')]
)
def display_controls_trench(n, stack_type):
    if stack_type == 'nand':
        n = n+2
    return html.Div('Controls container trench {}'.format(n), id=generate_output_id_trench(n))


# Func called to all stack data entry callbacks
def stack_calc(values):
    # TODO- cleaner parsing

    films = []
    for val in values[1::2]:
        films.append(str(val))
    thks = []
    for val in values[2::2]:
        thks.append(int(val))

    if values[0]:
        dram_films = films[:2] * int(values[0])
        dram_thks = thks[:2] * int(values[0])

        films = dram_films + films[2:]
        thks = dram_thks + thks[2:]
    
    print('VALUE: {}'.format(values))
    print ('STACK CALC FILMS: {}'.format(films))
    print ('STACK CLAC THKS: {}'.format(thks))


    return str(films) + '*' + str(thks) #data to be parsed from hidden div-- split on "*"








#### TRENCH STACK LAYER CALLBACKS
# Callback for one layer stack
@simulator.callback(
    Output(generate_output_id_trench(1), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
    State('trench-thickness-{}'.format(1), 'value')])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for two layer stack
@simulator.callback(
    Output(generate_output_id_trench(2), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('trench-nand-pairs', 'value'),
    State('trench-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
    State('active-thickness-{}'.format(1), 'value')
    ])
def callback_data(n_clicks, *values):
    if n_clicks:
        return stack_calc(values)

# Callback for two layer stack
@simulator.callback(
    Output(generate_output_id_active(2), 'children'),
    [Input('calculate', 'n_clicks')],
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    [State('active-nand-pairs', 'value'),
    State('active-film-{}'.format(1), 'value'),
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
    Input('trench_nlayers_dropdown', 'value')],
    [State('active-radio', 'value'),
    State('trench-radio', 'value')]
)
def create_data_container(n_clicks, n_active, n_trench, active_stack_type, trench_stack_type):
    if n_clicks:
        if active_stack_type == 'nand':
            n_active = n_active + 2
        if trench_stack_type == 'nand':
            n_trench = n_trench + 2
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

def compute_reflectance_1d(mat_names, thicknesses, medium):
    """
    Compute reflectances of given film stack for fixed stack thickness

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

def compute_reflectance_2d(active_names, active_thicknesses, trench_names, trench_thicknessness, 
                          rr, medium):
    """
    Compute reflectances of given film stack for variable thicknesses

    input
    ======

    mat_names: list
        string names of film type
    thicknesses: list
        int values of film thicknesses in Angstroms
    rr: numeric
        removal rate in A/min
    medium: float
        index of refraction of medium on top of stack (air, water, etc)

    output
    ======

    pandas DataFrame
        columns: wavelength, reflectance

    """
    a_s = rr / 60 # removal rate in A/s
    top_layer = active

    active_fns = []
    trench_fns = []
    for mat_names, n_fn_list in zip((active_names, trench_names), (active_fns, trench_fns)):
        for mat in mat_names:
            mat_df = get_nkvals(mat)
            mat_fn = interp1d(mat_df.wavelength, mat_df.nk, kind='linear')
            fns.append(mat_fn)
    medium_fn = lambda wavelength: medium
    si_df = get_nkvals('Si') ## change to make film passable
    si_fn = interp1d(si_df.wavelength, si_df.nk, kind='linear')

    reflectance = calc_reflectances(n_fn_list=[medium_fn] + mat_fns + [si_fn], 
                                    d_list=[np.inf] + current_thicknesses + [np.inf], 
                                    th_0=0, 
                                    spectral_range=(260, 1700))
    r_df = pd.DataFrame(reflectance, columns=['wavelength', '0s'])


    for sec in range(active_thicknesses[-1]/a_s): #
        thk_by_pol_time = thicknesses[:-1] + [thicknesses[-1] - sec*a_s]
        r_by_pol_time = calc_reflectances(n_fn_list=[medium_fn] + mat_fns + [si_fn], 
                                        d_list=[np.inf] + thk_by_pol_time + [np.inf], 
                                        th_0=0, 
                                        spectral_range=(260, 1700))
        r_df['{}s'.format(sec)] = r_by_pol_time[:,1]
    return r_df

def combine_spectra(active_r, trench_r, pattern_density, medium):
    
    """ 
    Compute aggregate spectra from active and trench reflectance 
    as a function of pattern_density

    input
    ------
    
    active_r: pandas Dataframe with columns wavelength and r

    trench_r: pandas Dataframe with columns wavelength and r

    pattern_density: float, fraction of pattern mask containing active sites
                     (between 0 and 1)

    output
    -------
    numpy array, computed reflectance with columns 0 and 1 as wavelength 
    and reflectance respectively
        
    """

    base_reflectance = trench_r.copy().values
    ref_si = compute_reflectance_1d(['Si'], [50000], medium)

    np.multiply(base_reflectance[:,1], (1 - (pattern_density/100)), base_reflectance[:,1])
    np.add(base_reflectance[:,1], active_r.r*(pattern_density/100), base_reflectance[:,1])
    np.divide(base_reflectance[:,1], ref_si.r, base_reflectance[:,1])

    return base_reflectance



def generate_callback(n1, n2):
    def callback_data(x1, x2, tab, medium, pattern_density, rr):

        t_start = time.perf_counter()

        active_films = ast.literal_eval(x1.split('*')[0])
        active_thks = [x/10 for x in ast.literal_eval(x1.split('*')[1])] # convert to nm for calc
        active_r = compute_reflectance_1d(active_films, active_thks, medium)


        trench_films = ast.literal_eval(x2.split('*')[0]) # convert to nm for calc
        trench_thks = [x/10 for x in ast.literal_eval(x2.split('*')[1])] # convert to nm for calc
        trench_r = compute_reflectance_1d(trench_films, trench_thks, medium)

        combined_spectra = combine_spectra(active_r, trench_r, pattern_density, medium)


        if tab == 'r-spectra':

            # active_films = ast.literal_eval(x1.split('*')[0])
            # active_thks = ast.literal_eval(x1.split('*')[1])
            # active_r = compute_reflectance_1d(active_films, active_thks, medium)

            # trench_films = ast.literal_eval(x2.split('*')[0])
            # trench_thks = ast.literal_eval(x2.split('*')[1])
            # trench_r = compute_reflectance_1d(trench_films, trench_thks, medium)

            # combined_spectra = combine_spectra(active_r, trench_r, pattern_density, medium)


            t_end = time.perf_counter()
            print("CALC TIME:    ", (t_end - t_start), "SECONDS")
            print('Active films: {}'.format(active_films))
            print('Active thks: {}'.format(active_thks))
            print('Combined spectra:{}'.format(combined_spectra[:,:5]))
            graph = html.Div([
                    dcc.Graph(
                        figure={
                            'data': [
                                {
                                    'x':combined_spectra[:,0],
                                    'y':combined_spectra[:,1],
                                    'mode': 'line',
                                    'name': 'Reflectance'
                                }
                            ],
                            'layout': go.Layout(
                                xaxis=dict(
                                    title='wavelength',
                                    # range=[200, 1000]
                                    ),
                                yaxis=dict(
                                    title='computed intensity',
                                    # range=[0, 2]
                                    )
                                )
                            },
                    )
                ])
        elif tab == 'contour':
            rr = int(rr)

            # active_films = ast.literal_eval(x1.split('*')[0]) # convert to nm for calc
            # active_thks = [x/10 for x in ast.literal_eval(x1.split('*')[1])] # convert to nm for calc
            # active_r = compute_reflectance_1d(active_films, active_thks, medium)


            # trench_films = ast.literal_eval(x2.split('*')[0]) # convert to nm for calc
            # trench_thks = [x/10 for x in ast.literal_eval(x2.split('*')[1])] # convert to nm for calc
            # trench_r = compute_reflectance_1d(trench_films, trench_thks, medium)

            # spectra_matrix = combine_spectra(active_r, trench_r, pattern_density, medium)
            
            rr_as = rr / 60 # removal rate in A/s
            rr_nm = (rr / 10) / 60 # removal rate in nm/s

            # setting rr for testing purposes
            rr_nms = 10000 / 10 / 60

            t_start = time.perf_counter()
            print(active_thks[-1])
            starting_thk_active = active_thks[-1] # in nm
            starting_thk_trench = trench_thks[-1] # in nm

            # pol_time = int(starting_thk_active/rr_nms)
            # setting explicit int for testing
            pol_time = 7

            full_matrix = np.zeros((combined_spectra.shape[0], pol_time))

            for sec in range(pol_time):
                active_thks_sim = active_thks[:-1] + [(starting_thk_active - sec*rr_nms)]
                active_r_sim = compute_reflectance_1d(active_films, active_thks_sim, medium)

                trench_thks_sim = trench_thks[:-1] + [(starting_thk_trench - sec*rr_nms)]
                trench_r_sim = compute_reflectance_1d(trench_films, trench_thks_sim, medium)

                combined_spectra = combine_spectra(active_r_sim, trench_r_sim, pattern_density, medium)
                # spectra_matrix = np.hstack((spectra_matrix, combined_spectra[:,1]))
                # full_matrix.append(combined_spectra[:,1])
                # full_matrix[:, sec] = active_r_sim.r.values
                full_matrix[:, sec] = combined_spectra[:,1]

            t_stop = time.perf_counter()

            print('Comp time: {:.2f}'.format(t_stop - t_start))

            # for x axis labels
            pol_time = active_thks[-1] / rr_nm
            print('Active thks: {}'.format(active_thks[-1]))
            print('RR nm/s: {}'.format(rr_nm))
            print('pol time: {}'.format(pol_time))
            x_labels = list(range(0, int(pol_time), full_matrix.shape[1])),
            print('x-labels: {}'.format(x_labels))
            print('full-matrix-shape: {}'.format(full_matrix.shape))

            graph = html.Div([
                        dcc.Graph(
                            figure={
                                'data': [
                                    go.Contour(
                                        z=np.array(full_matrix),
                                        # x=list(range(int((active_thks[-1]/rr_as) * 60))), # testing rr_nms
                                        # x=list(range(0, int(pol_time), full_matrix.shape[1])),
                                        x=[0, 10, 20, 30, 40, 50],
                                        y=combined_spectra[:,0],
                                        colorscale='Jet',
                                        contours=dict(
                                            coloring='heatmap'
                                        )
                                    )
                                ],
                                'layout': go.Layout(
                                    xaxis=dict(
                                        title='Polish Time (s)',
                                        # range=[200, 1000]
                                        ),
                                    yaxis=dict(
                                        title='Wavelength',
                                        # range=[0, 2]
                                        )
                                    )
                            },
                    )
                ])
            pd.DataFrame(full_matrix).to_csv('spectra_matrix.csv')
        
        return graph
    return callback_data


@simulator.callback(
    Output('dummy-graph', 'style'),
    [Input('data-output', 'children')]
)
def turnoff_dummy_plot(output):
    if output:
        return {'display':'none'}

@simulator.callback(
    Output('dummy-graph', 'children'),
    [Input('chart-tabs', 'value')]
)
def tab_callback(tab):
    if tab == 'r-spectra':
        return dcc.Graph(
                figure={
                    'data':[],
                    'layout': go.Layout(
                        xaxis=dict(
                            title='wavelength',
                            range=[200, 1500]
                            ),
                        yaxis=dict(
                            title='computed intensity',
                            range=[0, 2]
                            )
                        )
                    },
            ),
    elif tab == 'contour':
        return dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Contour(
                    )
                ],
                # layout=go.Layout(
                #     plot_bgcolor='midnightblue'
                )
            )

@simulator.callback(
    Output('removal-rate', 'disabled'),
    [Input('chart-tabs', 'value')]
)
def disable_rr_input_for_2dplot(tab):
    if tab == 'r-spectra':
        return True


@simulator.callback(
    Output('removal-rate', 'style'),
    [Input('chart-tabs', 'value')]
)
def disable_rr_input_for_2dplot(tab):
    if tab == 'r-spectra':
        return {'color':'grey', 'textAlign':'center', 'width':'75'}
    else:
        return {'textAlign':'center', 'width':'75'}


@simulator.callback(
    Output('removal-rate', 'value'),
    [Input('chart-tabs', 'value')]
)
def disable_rr_input_for_2dplot(tab):
    if tab == 'r-spectra':
        return "n/a"
    elif tab == 'contour':
        return 1000


## Callback to put all input data into one div 
for val1, val2 in itertools.product(np.arange(1, max_layers), np.arange(1, max_layers)):
    simulator.callback(
        Output(generate_data_output_id(val1, val2), 'children'),
        [Input(generate_output_id_active(val1), 'children'), 
         Input(generate_output_id_trench(val2), 'children'),
         Input('chart-tabs', 'value')],
        [State('medium', 'value'),
         State('pattern-density-slider', 'value'),
         State('removal-rate', 'value')])(
             generate_callback(val1, val2)
         )
    # simulator.callback(
    #     Output('graph', 'figure'),
    #     [Input(generate_data_output_id(val1, val2), 'children')])(
    #         callback_plot(val1, val2)
    #     )
