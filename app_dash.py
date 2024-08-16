import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_ag_grid import AgGrid
from datetime import datetime
from dash.dependencies import Input, Output
from datetime import datetime
from funkcee import *

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

################################################################
# Layout of the app
app.layout = dbc.Container([
    dbc.Row([
             dbc.Col([
                      html.Div(
                               className="custom-column graph-container",
                               children = [
                                            html.Label(
                                                         "Hry dokončené v posledních sedmi dnech", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                             html.Br(),
                                            html.Label(
                                                         "Počet:", 
                                                         style={
                                                                'font-size': 'small'
                                                               }
                                                       ),
                                            html.Span(
                                                id="pocet-span",
                                                style={'font-size': 'small'}
                                            ),
                                            html.Div(
                                                     children=[
                                                                AgGrid(
                                                                    id='ag-grid',
                                                                    columnDefs=column_defs,
                                                                    rowData=data_dict,
                                                                    className='ag-theme-alpine',
                                                                    style={'width': '95%'},
                                                                )
                                                     ],
                                                        style={
                                                                'display': 'flex',
                                                                'justifyContent': 'center',
                                                            }
                                                     ),
                                          ],
                                          style={'height': '500px'},
                                          
                               ),
                       ],
                       width=7#, className='custom-column'
                      )
             ]
             , justify="center"
             ),
    dbc.Row([
             dbc.Col([
                      html.Div(
                               className="custom-column graph-container", 
                               children = [
                                            html.Label(
                                                         "Nejhrannější hry", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                           dcc.Graph(
                                                     figure=nejhrannejsi_hry()
                                                     )
                                          ]
                               ),
                       ],
                       width=5#, className='custom-column'
                      ),
            dbc.Col([
                      html.Div(
                               className="custom-column graph-container", 
                               children = [
                                            html.Label(
                                                         "Délka hry", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                           dcc.Graph(
                                                     figure=boxploty()
                                                     )
                                          ]
                               ),
                       ],
                       width=5#, className='custom-column'
                      )
             ]
                          , justify="center"
                          ),
    dbc.Row([
             dbc.Col(
                    [
                      html.Div(
                                className="custom-column graph-container", 
                                children = [
                                            html.Label(
                                                         "Kumulativní graf počtu her", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                                       html.Br(),
                                            html.Label(
                                                         "Křivku vybrané hry zobrazíte dvojklikem na její název v legendě.", 
                                                         style={
                                                                'font-size': 'small'
                                                               }
                                                       ),
                                            dcc.Graph(
                                                      figure=cumulative_games_linechart()
                                                     )
                                           ]
                              ),
                    ],
                     width=12#, className='custom-column'
                    )
            ]),
    dbc.Row([
             dbc.Col(
                    [
                      html.Div(
                                className="custom-column graph-container", 
                                children = [
                                            html.Label(
                                                         "Počet her zahájených/ukončených během jednoho dne", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                                       html.Br(),
                                            dcc.Graph(
                                                      figure=create_boxplot()
                                                     )
                                           ]
                              ),
                    ],
                     width=4#, className='custom-column'
                    )
            ],
            justify="center"
            ),
    dbc.Row([
             dbc.Col([
                      html.Div(
                               className="custom-column graph-container", 
                               children = [
                                            html.Label(
                                                         "Počet dokončených her dle dne a hodiny", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                           dcc.Graph(
                                                     figure=create_heatmap()
                                                     )
                                          ]
                               ),
                       ],
                       width=5#, className='custom-column'
                      ),
              dbc.Col(
                      html.Div(
                               className="custom-column graph-container", 
                               children = [
                                            html.Label(
                                                         "Časy začátků a konců her", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                       dcc.Graph(
                                figure=create_histogram()
                                )
                               ]
                      ), 
                    width=5
                    )
    ],
    justify="center"
    ),

    dbc.Row([
             dbc.Col([
                     html.Div(
                                children = [
                                            html.Label(
                                                         "Datum první hry", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                            dcc.Graph(
                                                        figure=create_scatter_plot()
                                                        ),
                                            ],
                                             style={'overflowX': 'scroll'}  # Enable horizontal scrolling
                                
                             ), 
             ],
                    width=12,
                    className='custom-column'
                    )
            ]),
    dbc.Row([
             dbc.Col(
                    html.Div([
                                html.Label(
                                                "Počet her dokončených daný den vs počet výher", 
                                                style={
                                                    'font-size': 'medium'
                                                    }
                                            ),
                                html.Br(),
                                html.Label(
                                                "Počet dnů, ve kterých byla dokončena aspoň jedna hra: ", 
                                                style={
                                                    'font-size': 'small'
                                                    }
                                            ),
                                html.Span(
                                    id="pocet-dnu-span",
                                    style={'font-size': 'small'}
                                ),
                                html.Br(),
                                html.Label(
                                                "Počet dnů s více než 75 % vyhraných her: ", 
                                                style={
                                                    'font-size': 'small'
                                                    }
                                            ),
                                html.Span(
                                    id="pocet-dnu-75",
                                    style={'font-size': 'small'}
                                ),
                                html.Div([
                                        dcc.Graph(
                                                figure=wins_linechart(df)
                                                ),
                            ],
                             style={'overflowX': 'scroll'}  # Enable horizontal scrolling
                             ), 
                            ]),
                    width=12, 
                    className='custom-column')
            ]),
    dbc.Row(
            [
             dbc.Col(
                     [
                      html.Div(
                               className="custom-column graph-container",
                               children = [
                                            html.Label(
                                                         "Nejčastější protihráči", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                            html.Br(),
                                            AgGrid(
                                                        id='ag-grid2',
                                                        columnDefs=column_defs2,
                                                        rowData=data_dict2,
                                                        className='ag-theme-alpine',
                                                        style={'width': '100%', "height": "300px"},
                                                    )
                            ]
                            ),

                      ], 
                      width=3
                      )
            ]
            ),
    dbc.Row(
            [
             dbc.Col(
                    [
                      html.Div(
                               className="custom-column graph-container", 
                               children = [
                                            html.Label(
                                                         "Procentuální úspěšnost v jednotlivých hrách", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                            dcc.Graph(
                                                    #figure=fig2
                                                    figure=win_percentage(df)
                                                    )
                                            ],
                                ),
                    ], 
                    width=12
                    )
            ]
            ),
    dbc.Row([
             dbc.Col(
                    [
                      html.Div(
                                className="custom-column graph-container", 
                                children = [
                                            html.Label(
                                                         "Turnaje", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                            html.Br(),
                                            html.Label(
                                                         "Čísla značí umístění uživatele na daném turnaji. Tečky značí jednotlivé hry.", 
                                                         style={
                                                                'font-size': 'small'
                                                               }
                                                       ),
                                            dcc.Graph(
                                                      figure=create_tournament_timeline(najs)
                                                     )
                                           ]
                              ),
                    ],
                     width=12#, className='custom-column'
                    )
            ]),
    dbc.Row([
             dbc.Col(
                    [
                      html.Div(
                                className="custom-column graph-container", 
                                children = [
                                            html.Label(
                                                         "ELO", 
                                                         style={
                                                                'font-size': 'medium'
                                                               }
                                                       ),
                                                       html.Br(),
                                            html.Label(
                                                         "Pro zobrazení jen jedné hry klikněte na její název v legendě. Chcete-li zároveň zobrazit nějakou další hru/y, označte ji v legendě dvojklikem", 
                                                         style={
                                                                'font-size': 'small'
                                                               }
                                                       ),
                                            dcc.Graph(
                                                      figure=plot_game_ranks(df)
                                                     )
                                           ]
                              ),
                    ],
                     width=12#, className='custom-column'
                    )
            ])
    
]
, fluid=True
)



@app.callback(
    [Output('pocet-span', 'children'),
     Output('pocet-dnu-span', 'children'),
     Output('pocet-dnu-75', 'children')],
    [Input('pocet-span', 'id'),
     Input('pocet-dnu-span', 'id'),
     Input('pocet-dnu-75', 'id')]
)
def update_pocet_span(pocet_id, dnu_id, pocet_75):
    pocet_unikatnich_dnu = df.game_date.dt.date.nunique()
    days_difference = (datetime.today() - df['game_date'].min()).days

    daily_games = df.groupby(df['game_date'].dt.date).size()
    daily_wins = df[df['dlouhejprovaz_won']].groupby(df['game_date'].dt.date).size()
    daily_wins = daily_wins.reindex(daily_games.index, fill_value=0) # Ensure both series have the same index

    # Calculate the win percentage and identify the days to highlight
    win_percentage = daily_wins / daily_games*100
    highlight_days = win_percentage[(win_percentage >= 75) & (daily_games > 1)].index

    return recent_games_df.shape[0], \
           f"{pocet_unikatnich_dnu} (ze {days_difference})", \
           len(highlight_days)


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)