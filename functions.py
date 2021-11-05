
import requests
import lxml.html as lh
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup
import js2xml
from datetime import date, timedelta


# get training data
def get_training_data(start_date, end_date, ma):

    # data storage
    hitting_data_list = []
    pitching_data_list = []
    game_data_list = []

    # initialize data pull
    start = start_date
    end = start_date + timedelta(days=ma-1)
    today = end + timedelta(days=1)
    while end <= end_date:

        # print progress
        print(today.strftime("%Y-%m-%d"))

        # pull data
        hitting_data_list.append(get_team_data(start, end, 'bat'))
        pitching_data_list.append(get_team_data(start, end, 'pit'))
        game_data_list.append(get_todays_games(today))

        # iterate day
        start = start + timedelta(days=1)
        end = end + timedelta(days=1)
        today = today + timedelta(days=1)

    # append together
    hitting_data = pd.concat(hitting_data_list)
    pitching_data = pd.concat(pitching_data_list)
    game_data = pd.concat(game_data_list)

    # merge away team data
    hitting_data_team = hitting_data.add_suffix('_hit_team')
    pitching_data_team = pitching_data.add_suffix('_pitch_team')
    hitting_data_team = hitting_data_team.rename(columns={'team_hit_team': 'team', 'date_hit_team': 'date'})
    pitching_data_team = pitching_data_team.rename(columns={'team_pitch_team': 'team', 'date_pitch_team': 'date'})
    training_data = game_data.merge(hitting_data_team, on=['date', 'team']).merge(pitching_data_team, on=['date', 'team'])

    # merge home team data
    hitting_data_opponent = hitting_data.add_suffix('_hit_opponent')
    pitching_data_opponent = pitching_data.add_suffix('_pitch_opponent')
    hitting_data_opponent = hitting_data_opponent.rename(columns={'team_hit_opponent': 'opponent', 'date_hit_opponent': 'date'})
    pitching_data_opponent = pitching_data_opponent.rename(columns={'team_pitch_opponent': 'opponent', 'date_pitch_opponent': 'date'})
    training_data = training_data.merge(hitting_data_opponent, on=['date', 'opponent']).merge(pitching_data_opponent, on=['date', 'opponent'])

    return training_data


# get team data
def get_team_data(start_date, end_date, side):

    # dates as strings
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # build teamURL
    teamURL = 'https://www.fangraphs.com/leaders.aspx?pos=all&stats=' + side + '&lg=all&qual=0&type=8&' \
              'season=2021&month=1000&season1=2021&ind=0&team=0%2Cts&rost=&age=0&filter=&players=0&' \
              'startdate=' + start_date_str + '&enddate=' + end_date_str

    # query tables
    page = requests.get(teamURL)
    doc = lh.fromstring(page.content)
    tr_elements = doc.xpath('//tr')

    # store data table headers
    stats = []
    for t in tr_elements[36]:
        name = t.text_content()
        stats.append(name)

    # delete first two variables
    stats = stats[2:]

    # store data by team
    data_raw = []
    i = 0
    j = 0

    # pull data by team
    for j in range(30):

        # loop over columns
        col_j = []
        for t in tr_elements[38 + j]:
            name = t.text_content()
            name = name.replace('%', '')
            name = name.replace('\xa0', 'nan')
            col_j.append(name)

        # append team j to raw data
        data_raw.append(col_j)

    # format data
    teams = [item[1] for item in data_raw]
    [item.pop(0) for item in data_raw]
    [item.pop(0) for item in data_raw]
    team_data_clean = pd.DataFrame(np.array(data_raw, dtype=np.float32))
    team_data_clean.columns = stats
    team_data_clean.insert(loc=0, column='team', value=teams)
    team_data_clean.insert(loc=0, column='date', value=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"))

    return team_data_clean


# get today's games
def get_todays_games(date):

    # date as string
    date_str = date.strftime("%Y-%m-%d")

    # build todaysgamesURL
    todaysgamesURL = 'https://www.fangraphs.com/scoreboard.aspx?date=' + date_str

    # query games
    page = requests.get(todaysgamesURL)
    doc = BeautifulSoup(page.content, "html.parser")
    try:
        script = doc.find("script", text=re.compile("Highcharts.Chart")).text
    except AttributeError:
        print('No games on ' + date_str)
        return pd.DataFrame([])
    parsed = js2xml.parse(script)
    games_raw = parsed.xpath('//property[@name="title"]/object/property[@name="text"]/string/text()')

    # clean games query
    games_raw = list(filter(None, games_raw))
    while 'Leverage Index' in games_raw:
        games_raw.remove('Leverage Index')
    games_clean = [item[item.find(' - ')+3:] for item in games_raw]

    # clean teams
    home_teams = [game[game.find('@')+1: game.rfind('(')].lstrip() for game in games_clean]
    away_teams = [game[0: game.find('(')].lstrip() for game in games_clean]

    # team names
    team_names = ['Red Sox', 'Royals', 'Tigers', 'Mariners', 'Yankees',
                   'Padres', 'Reds', 'Phillies', 'Nationals', 'Marlins',
                   'Cubs', 'Brewers', 'Rockies', 'Orioles', 'White Sox',
                   'Cleveland', 'Twins', 'Rays', 'Rangers', 'Diamondbacks',
                   'Braves', 'Dodgers', 'Mets', 'Pirates', 'Cardinals',
                   'Giants', 'Blue Jays', 'Astros', 'Athletics', 'Angels']

    # team abbreviations
    team_abbreviations = ['BOS', 'KCR', 'DET', 'SEA', 'NYY', 'SDP', 'CIN', 'PHI', 'WSH', 'MIA',
                          'CHC', 'MIL', 'COL', 'BAL', 'CHW', 'CLE', 'MIN', 'TBR', 'TEX', 'ARZ',
                          'ATL', 'LAD', 'NYM', 'PIT', 'STL', 'SFG', 'TOR', 'HOU', 'OAK', 'LAA']

    # replace names with abbreviations
    home_df = pd.DataFrame({'name': home_teams})
    away_df = pd.DataFrame({'name': away_teams})
    name2abbrev_df = pd.DataFrame({'name': team_names, 'abbreviation': team_abbreviations})
    home_teams_df = home_df.merge(name2abbrev_df, on='name')
    away_teams_df = away_df.merge(name2abbrev_df, on='name')
    teams = pd.concat((away_teams_df, home_teams_df), axis=1)
    del teams['name']
    teams.columns.values[0] = 'team'
    teams.columns.values[1] = 'opponent'

    # who won each game
    away_score = [game[game.find('(') + 1: game.find(')')] for game in games_clean]
    home_score = [game[game.rfind('(') + 1: game.rfind(')')] for game in games_clean]
    teams['team_score'] = list(map(int, away_score))
    teams['opponent_score'] = list(map(int, home_score))

    # final game_data object
    teams['win'] = teams['team_score'] - teams['opponent_score']
    teams = teams.drop(teams[teams.win == 0].index)
    teams['win'][teams['win'] > 0] = 1
    teams['win'][teams['win'] < 0] = 0
    teams.insert(loc=0, column='date', value=date_str)
    game_data = teams

    return game_data
