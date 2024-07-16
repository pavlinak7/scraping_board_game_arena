import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from collections import Counter
from datetime import timedelta
from scipy.stats import gaussian_kde
import numpy as np
from funkcee import *


# Load the dataset
file_path = 'aktualizace/ukoncene_hry2.csv'
df = pd.read_csv(file_path, delimiter=';')


# Convert date columns to datetime
df['game_date'] = pd.to_datetime(df['game_date'])
df['game_start'] = pd.to_datetime(df['game_start'])
df['game_time'] = pd.to_timedelta(df['game_time']).dt.total_seconds() / 3600


# Prepare data for visualizations
df['game_finish_day'] = df['game_date'].dt.day_name()
df['hour'] = df['game_date'].dt.hour
df['game_start_hour'] = df['game_start'].dt.hour
df['game_finish_hour'] = df['game_date'].dt.hour
df['game_start_date'] = df['game_start'].dt.date
df['game_date_date'] = df['game_date'].dt.date

df['dlouhejprovaz_won'] = df['results'].apply(lambda x: "DlouhejProvaz" in x.split(',')[0])

desired_legend_order = ['Patchwork', "It's a Wonderful World", 'Wingspan', 'Nova Luna', 'Railroad Ink', 
                        'Lost Ruins of Arnak', 'Azul', 'My Shelfie', 'Ticket to Ride', 'Gizmos', 'Carcassonne', 
                        'Welcome To', 'Rauha', 'Potion Explosion', "Hadrian's Wall", 'Fairy Trails', 'Caverna']


#games_finished = df.groupby(df['game_date'].dt.date).size().to_frame('number_of_games').reset_index()
#first_time_playing = df.drop_duplicates(subset=['game_name'], keep='first').set_index('game_date')


#games_won_by_dlouhejprovaz = df[df['results'].str.contains('1st-DlouhejProvaz')].groupby(df['game_date'].dt.date).size().to_frame('number_of_games').reset_index()
def filter_first_element_contains(df, keyword):
    return df[df['results'].apply(lambda x: keyword in x.split(',')[0])]
vys = filter_first_element_contains(df, "DlouhejProvaz")
games_won_by_dlouhejprovaz = vys.groupby(df['game_date'].dt.date).size().to_frame('number_of_games').reset_index()

###################################################################################š
# tabulka her odehraných za poslední týden
one_week_ago = df['game_date'].max() - timedelta(days=7)
recent_games_df = df[df['game_date'] >= one_week_ago]
recent_games_df = recent_games_df[['game_name', 'game_start', 'game_date', 'results']]
recent_games_df.game_start = recent_games_df.game_start.dt.date
recent_games_df.game_date = recent_games_df.game_date.dt.date
data_dict = recent_games_df.to_dict('records')

column_defs = [
    {"headerName": "Game Name", "field": "game_name", "width": 150},
    {"headerName": "Game Start", "field": "game_start", "width": 150},
    {"headerName": "Game Finish", "field": "game_date", "width": 150},
    {"headerName": "Results", "field": "results", "width": 400}
]

######################################################################################
# Nejhrannější hry
top_games = df['game_name'].value_counts().head(15)
filtered_df = df[df['game_name'].isin(top_games.index)]
mean_game_time = filtered_df.groupby('game_name')['game_time'].mean()
sorted_mean_game_time = mean_game_time.reindex(list(top_games.index))

def create_plotly_figure():
    fig = go.Figure()
    fig.add_trace(
                  go.Bar(
                        x=top_games.index,
                        y=top_games.values,
                        #marker_color='blue',
                        )
                  )
    fig.update_layout(
                    xaxis=dict(
                               tickangle=60  # Rotate the x-axis labels by 60 degrees
                              ),
                    width=700,  # Increase the width of the graph
                    height=500,  # Increase the height of the graph
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=10)
                    )
    return fig

###################################################
# délka her
filtered_df = filtered_df.copy()
filtered_df['game_name'] = pd.Categorical(filtered_df['game_name'], categories=list(top_games.index), ordered=True)
filtered_df = filtered_df.sort_values('game_name')

def boxploty(df):
    fig = go.Figure()
    fig.add_trace(
                  go.Box(
                        x=filtered_df['game_name'],
                        y=filtered_df["game_time"],
                        marker=dict(color='blue', size = 3), 
                        line=dict(color='blue', width = 1),
                        fillcolor='rgba(0,0,0,0)',
                        boxmean=True
                    )
                )
    fig.update_layout(
                    xaxis=dict(
                               tickangle=60  # Rotate the x-axis labels by 60 degrees
                              ),
                    yaxis_title='Délka hry [min]',
                    height=500,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=10)
                )
    return fig

#########################################################################
def cumulative_games_linechart(df):
    games_by_date = df.groupby(['game_name', df['game_date'].dt.date]).size().reset_index(name='count') # Group by game_name and game_date, then count the number of games
    total_games_played = games_by_date.groupby('game_name')['count'].sum().reset_index() # Calculate the total number of games played for each game
    top_15_games = total_games_played.nlargest(15, 'count')['game_name']  # Get the top 15 most played games
    games_by_date_top15 = games_by_date[games_by_date['game_name'].isin(top_15_games)] # Filter the dataframe to include only the top 15 games

    # Calculate the cumulative sum for each of the top 15 games
    games_by_date_top15 = games_by_date_top15.copy()
    games_by_date_top15['cumulative_count'] = games_by_date_top15.groupby('game_name')['count'].cumsum()

    # Calculate the cumulative sum of all games
    games_by_date_all = df.groupby(df['game_date'].dt.date).size().reset_index(name='count')
    games_by_date_all['cumulative_count'] = games_by_date_all['count'].cumsum()
    games_by_date_all['game_name'] = 'Total'

    # Combine the dataframes
    combined_df = pd.concat([games_by_date_top15, games_by_date_all], ignore_index=True)

    # Ensure the order of the legend
    category_order = ['Total'] + top_15_games.tolist()
    combined_df['game_name'] = pd.Categorical(combined_df['game_name'], categories=category_order, ordered=True)
    combined_df = combined_df.sort_values(['game_name', 'game_date'])


    fig = go.Figure()

    # Add traces for top 15 games
    for game in top_15_games:
        game_data = combined_df[combined_df['game_name'] == game]
        fig.add_trace(
                    go.Scatter(
                                x=game_data['game_date'], 
                                y=game_data['cumulative_count'], 
                                mode='lines', 
                                name=game
                            )
                    )

    # Add trace for total games
    total_data = combined_df[combined_df['game_name'] == 'Total']
    fig.add_trace(
                  go.Scatter(
                            x=total_data['game_date'], 
                            y=total_data['cumulative_count'], 
                            mode='lines', 
                            name='Total',
                            visible=True  # This controls the initial visibility
                        )
                )

    # Update layout
    fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Cumulative Sum of Games',
                    legend_title='Game Name',
                    template='plotly_white',
                    updatemenus=[
                                dict(
                                    type="buttons",
                                    direction="left",
                                    buttons=list(
                                                [
                                                dict(
                                                    args=[{"visible": [True] * (len(top_15_games) + 1)}],
                                                    label="Show Total",
                                                    method="update"
                                                    ),
                                                dict(
                                                    args=[{"visible": [True] * len(top_15_games) + [False]}],
                                                    label="Hide Total",
                                                    method="update"
                                                    )
                                                ]
                                                ),
                                    pad={"r": 10, "t": 10},
                                    showactive=True,
                                    x=0.1,
                                    xanchor="left",
                                    y=1.1,
                                    yanchor="top"
                                ),
                            ],
                    height=700,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=10),
    )

    return fig

#############################################################
def create_boxplot(df):
    # Count the number of games started and finished each day
    games_started_per_day = df['game_start_date'].value_counts().sort_index()
    games_finished_per_day = df['game_date_date'].value_counts().sort_index()

    # Create a dataframe for plotting
    games_per_day = pd.DataFrame({
        'Date': games_started_per_day.index.union(games_finished_per_day.index),
        'Games Started': games_started_per_day.reindex(games_started_per_day.index.union(games_finished_per_day.index), fill_value=0),
        'Games Finished': games_finished_per_day.reindex(games_started_per_day.index.union(games_finished_per_day.index), fill_value=0)
    }).fillna(0)


    fig = go.Figure()
    fig.add_trace(
                  go.Box(
                        y=games_per_day['Games Started'],
                        fillcolor='rgba(0,0,0,0)',
                        marker=dict(color='blue', size=3),
                        line=dict(color='blue', width=1),
                        )
                )
    fig.add_trace(
                  go.Box(
                        y=games_per_day['Games Finished'],
                        name='Games Finished',
                        fillcolor='rgba(0,0,0,0)',
                        marker=dict(color='blue', size=3),
                        line=dict(color='blue', width=1),
                    )
                  )
    fig.update_layout(
                    yaxis_title='Number of Games',
                    showlegend=False,
                    boxmode='group',  # Group the boxplots together
                    width=500,
                    plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=10),
                    )

    return fig

###############################################################################
def create_heatmap(data):
    # Create a pivot table for the heatmap
    heatmap_data = data.pivot_table(index='game_finish_day', columns='hour', values='game_number', aggfunc='count', fill_value=0)
    
    # Reorder the days of the week, starting with Monday
    days_order = ['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday']
    heatmap_data = heatmap_data.reindex(days_order)
    
    fig = go.Figure(
               data=go.Heatmap(
                            z=heatmap_data.values,
                            x=heatmap_data.columns,
                            y=heatmap_data.index,
                            colorscale='YlGnBu',
                            colorbar=dict(title='Number of Games')
                              )
                    )
    fig.update_layout(
                    xaxis_title='Hour of Day',
                    yaxis_title='Day of Week',
                    yaxis=dict(categoryorder='array', categoryarray=days_order),  # Ensure correct order
                    width=650,  
                    height=500,  # Increase the height of the graph
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(t=20, b=10),
                )
    
    return fig

########################################################################
def create_histogram():
    fig = go.Figure()

    # Create KDE for game start hour
    start_hour_kde = gaussian_kde(df['game_start_hour'])
    start_hour_range = np.linspace(0, 24, 1000)
    start_hour_density = start_hour_kde(start_hour_range)

    fig.add_trace(
                  go.Scatter(
                            x=start_hour_range,
                            y=start_hour_density,
                            mode='lines',
                            line=dict(color='blue', width=2),
                            name='Game Start Hour'
                        ))

    # Create KDE for game finish hour
    finish_hour_kde = gaussian_kde(df['game_finish_hour'])
    finish_hour_range = np.linspace(0, 24, 1000)
    finish_hour_density = finish_hour_kde(finish_hour_range)

    fig.add_trace(
                  go.Scatter(
                            x=finish_hour_range,
                            y=finish_hour_density,
                            mode='lines',
                            line=dict(color='red', width=2),
                            name='Game Finish Hour'
                        ))
    fig.update_layout(
                    xaxis=dict(title='Hour', dtick=1),
                    yaxis=dict(title='Density'),
                    legend=dict(
                                x=0,  # Position the legend to the left
                                y=0.98,  # Position the legend to the top
                                xanchor='left',  # Anchor the legend's x position to the left
                                yanchor='top'  # Anchor the legend's y position to the top
                            ),
                    width=650,
                    height=500,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=10)
                )
    
    return fig

########################################################### 
#první hry
first_played = df.groupby('game_name')['game_date'].min().reset_index() # Get the first time each game was played
first_played_sorted = first_played.sort_values(by='game_date')

first_day_of_month = pd.date_range(start=first_played_sorted['game_date'].min(), 
                                   end=first_played_sorted['game_date'].max(), freq='MS')

def create_scatter_plot():
    fig = go.Figure()

    # Plot each game's first play date on the same y-axis value
    y_value = 1
    fig.add_trace(
                  go.Scatter(
                            x=first_played_sorted['game_date'],
                            y=[y_value] * len(first_played_sorted),
                            mode='markers+text',
                            text=['&#127922;'] * len(first_played_sorted),  # Meeple emoji
                            textfont=dict(size=15),
                            textposition='middle center'
                        ))
    # Add annotations for each point
    for idx, row in first_played_sorted.iterrows():
        fig.add_annotation(
                            x=row['game_date'],
                            y=y_value + 0.1,  # Adjust y value for text placement
                            text=row['game_name'],
                            showarrow=False,
                            yshift=10,
                            textangle=-90,  # Rotate text 90 degrees
                            font=dict(size=14),
                            align='center'
                        )
    fig.update_layout(
                    xaxis=dict(
                                title='Date',
                                tickformat='%Y-%m-%d',
                                tickangle=-90,
                                tickvals=first_day_of_month,
                                showgrid=True,
                                gridcolor='#d7d9db',
                                range=['2022-10-20', first_played_sorted['game_date'].max() + pd.Timedelta(days=2)]
                            ),
                    yaxis=dict(
                                showticklabels=False,
                                range=[0.99, 1.2],  # Adjusted range to better fit the text
                                showgrid=False
                            ),
                    width=10000,
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=40, b=50, l=40, r=40),
                )

    return fig


########################################################
#linegraph her/výher
def wins_linechart(df):
    # Group by date and count the number of games and the number of wins by DlouhejProvaz
    daily_games = df.groupby(df['game_date'].dt.date).size()
    daily_wins = df[df['dlouhejprovaz_won']].groupby(df['game_date'].dt.date).size()
    daily_wins = daily_wins.reindex(daily_games.index, fill_value=0) # Ensure both series have the same index

    # Calculate the win percentage and identify the days to highlight
    win_percentage = daily_wins / daily_games*100
    highlight_days = win_percentage[(win_percentage >= 75) & (daily_games > 1)].index

    fig = go.Figure()
    fig.add_trace(
                  go.Scatter(
                             x=daily_games.index, 
                             y=daily_games.values, 
                             mode='lines', 
                             name='Games Finished'
                             )
                )
    fig.add_trace(
                  go.Scatter(
                             x=daily_wins.index, 
                             y=daily_wins.values, 
                             mode='lines', 
                             name='Wins by DlouhejProvaz'
                             )
                 )
    fig.add_trace( # Fill between
                  go.Scatter(
                            x=daily_games.index.tolist() + daily_games.index.tolist()[::-1],
                            y=daily_games.tolist() + daily_wins.tolist()[::-1],
                            fill='toself',
                            fillcolor='rgba(0, 255, 0, 0.3)',
                            line=dict(color='rgba(255,255,255,0)'),
                            hoverinfo="skip",
                            showlegend=False,
                        )
                )
    fig.add_trace( # Highlight the specific days with red dots
                 go.Scatter(
                            x=highlight_days,
                            y=daily_games[highlight_days],
                            mode='markers',
                            marker=dict(color='red', size=6),
                            name='>=75% Wins'
                        )
                 )
    fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Number of Games',
                    template='plotly_white',
                    width=10000,
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=20, b=10), 
                    xaxis=dict(
                                tickformat='%Y-%m-%d',
                                tickangle=-90,
                                showgrid=True,
                                gridcolor='white',
                                range=['2022-10-20', df['game_date'].max() + pd.Timedelta(days=2)]
                            ),
                    legend=dict(
                                x=0,   # x-position of the legend (0 is left, 1 is right)
                                y=-0.5,   # y-position of the legend (0 is bottom, 1 is top)
                                xanchor='left',
                                yanchor='bottom',
                                orientation='h'  # horizontal legend layout
                            )
                )
    
    return fig

###############################################################
def extract_opponents(results):
    players = results.split(', ')
    opponents = [p.split('-')[1] for p in players if 'DlouhejProvaz' not in p]
    return opponents

df['opponents'] = df['results'].apply(extract_opponents)

# Flatten the list of lists and get the top 5 most common opponents
all_opponents = [opponent for sublist in df['opponents'] for opponent in sublist]
top_5_opponents = Counter(all_opponents).most_common(5)

# Extract the opponent names and their game counts
opponents_data = [{'name': opponent[0], 'count': opponent[1]} for opponent in top_5_opponents]
opponents_data_df = pd.DataFrame(opponents_data)
data_dict2 = opponents_data_df.to_dict('records')

column_defs2 = [
    {"headerName": "Game Name", "field": "name", "width": 150},
    {"headerName": "Počet společných her", "field": "count", "width": 200, "cellStyle": {"textAlign": "center"}}
]

####################################################################
def win_percentage(df):
    # Count the total number of games and victories for each unique game
    total_games = df['game_name'].value_counts().reset_index()
    total_games.columns = ['game_name', 'total_games']

    victories = df[df['results'].apply(lambda x: "DlouhejProvaz" in x.split(',')[0])]['game_name'].value_counts().reset_index()
    victories.columns = ['game_name', 'victories']

    filtered_total_games = total_games[total_games['total_games'] >= 3] # games that have been played at least three times
    filtered_victories = victories[victories['game_name'].isin(filtered_total_games['game_name'])]

    # Merge the filtered dataframes
    filtered_game_stats = pd.merge(filtered_total_games, filtered_victories, on='game_name', how='left').fillna(0)
    filtered_game_stats['win_percentage'] = (filtered_game_stats['victories'] / filtered_game_stats['total_games']) * 100

    fig = go.Figure()
    fig.add_shape(
                type="line",
                x0=-0.5,  # start from the leftmost bar
                y0=50,
                x1=len(filtered_game_stats['game_name'])-0.5,  # end at the rightmost bar
                y1=50,
                line=dict(color="white", width=1),
                layer="below"
            )
        # Add the text "50" to the line
    fig.add_annotation(
                    x=len(filtered_game_stats['game_name']) - 0.5,  # position near the end of the line
                    y=47,
                    text="50",
                    showarrow=False,
                    #font=dict(color="white"),
                    align="left",
                    xanchor="left",
                    yanchor="bottom",
                    #bgcolor="black"  # Optional: to ensure readability
                )
    fig.add_trace(
                 go.Bar(
                    x=filtered_game_stats['game_name'],
                    y=filtered_game_stats['win_percentage'],
                    text=filtered_game_stats['win_percentage'].apply(lambda x: f'{x:.1f}%'),
                    textposition='outside',
                    name='Win Percentage'
                       )
                )
    fig.update_layout(
                    yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),  # Hide y-axis grid and labels
                    xaxis=dict(showgrid=False, tickangle=60),  # Hide x-axis grid
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=500,
                    margin=dict(t=20, b=10),  # Increase the height of the graph
                    )

    return fig
################################################################
# turnaje
ukoncene = pd.read_csv("aktualizace/ukoncene_hry2.csv", sep=";")
tournaments = pd.read_csv("aktualizace/tournaments2.csv", sep=";")
umisteni = pd.read_csv("aktualizace/umisteni_na_turnajich2.csv", sep=";")


tournaments["stul_cislo"] = tournaments.url.apply(lambda x: int(x[-9:]))
tournaments["turnaj_cislo"] = tournaments["tournament_url"].apply(lambda x: int(x[-6:]) if len(x) > 6 else np.nan)

sp = tournaments.merge(umisteni, left_on="turnaj_cislo", right_on="tournament_link", how="left")

spojeno = ukoncene.merge(sp, left_on="game_number", right_on="stul_cislo", how="left")

seskup = (spojeno.groupby(["game_name", "tournament_url", "tournament"])
          .agg({'game_start': 'min', 'game_date': 'max'})
          .reset_index())

toto = seskup.loc[seskup.tournament != "není"]
#toto['num_tournaments'] = toto.groupby('game_name')['tournament'].transform('count')
toto = toto.copy()
toto['num_tournaments'] = toto.groupby('game_name')['tournament'].transform('count')


toto = toto.sort_values(by=["num_tournaments", "game_name", "game_start"], ascending=[True, True, True])

spojeno2 = spojeno.merge(toto, on="tournament_url", how="left")

najs = (spojeno2.loc[:, ["game_name_x", "tournament_y", "tournament_url", "game_start_y", "game_date_y", 
                         "num_tournaments", "game_number", "game_start_x", "results", "place"]]
        .sort_values(by=["num_tournaments", "game_name_x", "game_start_y", "game_start_x"], ascending=[True, True, True, True]))

najs.place = najs.place.astype('Int64')


def create_tournament_timeline(najs):
    # Convert date columns to datetime
    najs["game_start"] = pd.to_datetime(najs["game_start_x"])
    najs["game_date"] = pd.to_datetime(najs["game_date_y"])

    # Filter out rows where 'game_date' is NaT
    najs_filtered = najs.dropna(subset=['game_date'])

    # Ensure the order matches the user's provided order
    order = ["All Games", 'Patchwork', "It's a Wonderful World", 'Wingspan', 'Nova Luna', 'Railroad Ink', 
             'Lost Ruins of Arnak', 'Azul', 'My Shelfie', 'Ticket to Ride', 'Gizmos', 'Carcassonne', 
             'Welcome To', 'Rauha', 'Potion Explosion', "Hadrian's Wall", 'Fairy Trails', 'Caverna']

    game_order = ['Caverna', 'Fairy Trails', "Hadrian's Wall", 'Potion Explosion', 'Rauha', 'Welcome To', 
                  'Carcassonne', 'Gizmos', 'Ticket to Ride', 'My Shelfie', 'Azul', 'Lost Ruins of Arnak', 
                  'Railroad Ink', 'Nova Luna', 'Wingspan', "It's a Wonderful World", 'Patchwork']

    # Create an ordered color map
    colors = px.colors.qualitative.Plotly
    color_map = {game: colors[i % len(colors)] for i, game in enumerate(game_order)}

    # Create the figure
    fig = go.Figure()

    # Add lines and markers for each tournament, ensuring only one legend entry per game
    added_legends = set()
    traces = []  # List to store the traces
    annotations = {game: [] for game in game_order}  # Dictionary to store annotations for each game

    for index, row in najs_filtered.iterrows():
        show_legend = row['game_name_x'] not in added_legends
        line_trace = go.Scatter(
            x=[row['game_start'], row['game_date']],
            y=[row['tournament_y'], row['tournament_y']],
            mode='lines',
            name=row['game_name_x'],
            line=dict(color=color_map[row['game_name_x']], width=2),  # Adjust line width here
            text=[row['tournament_y'], row['tournament_y']],
            hoverinfo='text',
            showlegend=show_legend
        )
        marker_trace = go.Scatter(
            x=[row['game_start']],
            y=[row['tournament_y']],
            mode='markers',
            marker=dict(color=color_map[row['game_name_x']], size=5),  # Adjust marker size here
            text=[row['game_name_x']],
            hoverinfo='none',
            name=row['game_name_x']+'_marker',
            showlegend=False,
            visible=False  # Set marker traces to be initially invisible
        )
        traces.append(line_trace)
        traces.append(marker_trace)
        if show_legend:
            added_legends.add(row['game_name_x'])

        # Create annotation for the 'Place' column value
        if pd.notna(row['place']):
            annotation = dict(
                x=row['game_date'],
                y=row['tournament_y'],
                text=str(row['place']),
                showarrow=False,
                font=dict(color=color_map[row['game_name_x']]),
                xanchor='left',
                xshift=10  # Shift the text slightly to the right of the line
            )
            annotations[row['game_name_x']].append(annotation)

    # Add the traces to the figure in the original order
    for trace in traces:
        fig.add_trace(trace)

    # Define x-axis range
    x_axis_range = ['2023-01-01', '2024-07-31']

    # Create dropdown buttons
    buttons = []
    for game in game_order:
        visible_traces = [trace.name == game or trace.name == game+'_marker' for trace in traces]
        all_annotations = annotations[game] if game in annotations else []

        button = dict(
            label=game,
            method='update',
            args=[{'visible': visible_traces},
                  {#'title': f"Tournament Timeline - {game}",
                   'annotations': all_annotations,
                   'xaxis.range': x_axis_range,
                   'showlegend': False}]
        )
        buttons.append(button)

    # Add a button for showing all games without markers and place annotations
    visible_traces_all_games = [not trace.name.endswith('_marker') for trace in traces]
    button_all_games = dict(
        label="All Games",
        method="update",
        args=[{"visible": visible_traces_all_games},
              {#"title": "Tournament Timeline - All Games",
               "annotations": [],
               'xaxis.range': x_axis_range,
               'showlegend': True}]
    )
    # Ensure "All Games" button is the first one
    buttons.insert(0, button_all_games)

    # Reorder the buttons according to the specified order
    ordered_buttons = [next(button for button in buttons if button['label'] == game) for game in order]

    # Add the buttons to the layout
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=ordered_buttons,
                direction="down",
                showactive=True,
                x=0.5,  # Center the dropdown menu
                xanchor="center",
                y=1.15,  # Position above the chart
                yanchor="top"
            )
        ],
        legend=dict(
            traceorder='reversed'
        ),
        #xaxis_title="Date",
        yaxis_title="",
        yaxis=dict(showticklabels=False, showgrid=False),  # Hide y-axis labels and grid
        xaxis=dict(
            showgrid=False,  # Hide x-axis grid
            tickangle=-90,  # Rotate x-axis labels 90 degrees
            range=x_axis_range  # Set the x-axis range
        ),
        showlegend=True,  # Show legend by default
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent paper background
        height=700,  # Set the figure height to 500
        margin=dict(t=10, b=10)  # Set top and bottom margins to 10
    )

    return fig

################################################################
#ELO
def plot_game_ranks(ukoncene):
    top_games = ukoncene['game_name'].value_counts().head(15).index.to_list()
    ukoncene = ukoncene.loc[ukoncene['game_name'].isin(top_games),:]
    ukoncene = ukoncene.sort_values(by='game_date')

    # Determine the y-axis limits based on the data
    y_min = ukoncene['rank'].min()
    y_max = ukoncene['rank'].max()

    fig = go.Figure()

    # Plot each game's rank over time in the desired order
    for game in desired_legend_order:
        if game in ukoncene['game_name'].unique():
            game_ukoncene = ukoncene[ukoncene['game_name'] == game]
            fig.add_trace(
                          go.Scatter(
                                x=game_ukoncene['game_date'],
                                y=game_ukoncene['rank'],
                                mode='lines+markers',
                                name=game,
                                marker=dict(size=3),  # Change marker size
                                line=dict(width=2)     # Change line width
                                   )
                            )
    fig.update_layout(
                    yaxis=dict(
                                title='ELO points',
                                range=[y_min, y_max]  # Set the y-axis range
                            ),
                    legend_title='Game Name',
                    legend=dict(
                                itemclick="toggleothers",
                                itemdoubleclick="toggle",
                                traceorder='normal'  # Maintain the order of legend items as added
                            ),  # Allows single click to isolate a trace and double click to reset
                    height=700,
                    plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
                    paper_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=10),
                )
    fig.update_xaxes(tickangle=45)

    return fig