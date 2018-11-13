import itertools
from app import app
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

simulator = dash.Dash(name='simulator', external_stylesheets=external_stylesheets, 
                      sharing=True, server=app, url_base_pathname='/data/')

simulator.config['suppress_callback_exceptions']=True

max_layers = 10

simulator.layout= html.Div([
    html.Div(
        html.H1('Theospec'),
        style={'textAlign':'center'}
    ),
    html.Div([
        html.Div([
            html.H5('Medium'),
            html.Div(
                dcc.RadioItems(
                    id='medium',
                    options=[
                        {'label':'Air', 'value':1},
                        {'label':'Water', 'value':1.3333}
                ]), style={'display':'inline-block', 'vertical-align':'middle'})
        ], className='one column'),
        html.Div([
            html.H5('Pattern Density'),
            html.Div(
                dcc.Slider(
                    id='pattern-density-slider',
                    min=0,
                    max=100,
                    step=5,
                    value=50
                )),
            html.Div(id='slider-output', style={'textAlign':'center'})
        ], className='two columns'),
        html.Div([
            html.H5('Removal Rate'),
            html.Div(
                dcc.Input(
                    id='removal-rate', type='text', placeholder='A/s' 
                )
            )
        ], className='two columns'),
        html.Div(html.H3('Plot'), className='six columns', style={'textAlign':'center'})
    ], className='row'),
    html.Div([
        html.Div([
            html.Div(html.H4('Active Stack')),
            html.Div(
                dcc.Dropdown(id='active_nlayers_dropdown', 
                            options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                            placeholder='N Film Layers'),
                style={
                    'width':'30%',
                    'textAlign': 'center',
                    'display':'table-cell'
                }),
            html.Div(id='active-controls-container', className='row'),
            dcc.Input(id='active-input-box', type='text', placeholder='Si Substrate'), 
            ], className="three columns")]
    ),
    html.Div([
        html.Div([
            html.Div(html.H4('Trench Stack')),
            html.Div(
                dcc.Dropdown(id='trench_nlayers_dropdown', 
                            options=[{'label':i, 'value':i} for i in range(1, max_layers)],
                            placeholder='N Film Layers'),
                style={
                    'width':'30%',
                    'textAlign': 'center',
                    'display':'table-cell'
                }),
            html.Div(id='trench-controls-container', className='row'),
            dcc.Input(id='trench-input-box', type='text', placeholder='Si Substrate'), 
            html.Div(html.Button('Calculate', id='calculate'),
                style={
                    'height':'400px',
                    'width':'500px'
                }),
        ], className="three columns")]
    ),
    html.Div([
        html.Div(id='data-output-active', style={'display':'none'}),
        html.Div(id='data-output-trench', style={'display':'none'}),
        html.Div(id='data-output')
        ], className='six columns')
])


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
                            options=[{'label':i, 'value':i} for i in film_options])
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
    return html.Div('Test for active {}'.format(n), id=generate_output_id_active(n))

@simulator.callback(
    Output('data-output-trench', 'children'),
    [Input('trench_nlayers_dropdown', 'value')]
)
def display_controls_trench(n):
    return html.Div('Test for trench {}'.format(n), id=generate_output_id_trench(n))


# Func called to all stack data entry callbacks
def stack_calc(values):
    films = []
    for val in values[::2]:
        films.append(val)
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
    [State('medium', 'value'),
    State('pattern-density-slider', 'value'),
    State('removal-rate', 'value'),
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
    def callback_data(x1, x2, medium, slider, rr):
        print('test total value for {} and {}'.format(n1, n2))
        print('x1: {}, x2:{}'.format(x1, x2))
        active_films = [int(x) for x in x1.split('*')[0][1:-1].split(',')]
        active_thks = [int(x) for x in x1.split('*')[1][1:-1].split(',')]
        trench_films = [int(x) for x in x2.split('*')[0][1:-1].split(',')]
        trench_thks = [int(x) for x in x2.split('*')[1][1:-1].split(',')]
        graph = html.Div([
            html.Div(str(slider) + str(medium) + str(rr)),
            dcc.Graph(
                figure={
                    'data': [
                        {
                            'x':active_films,
                            'y':active_thks,
                            'mode': 'markers'
                        },
                        {
                            'x':trench_films,
                            'y':trench_thks,
                            'mode': 'markers'
                        }
                    ]
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