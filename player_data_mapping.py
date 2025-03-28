from espncricinfo.player import Player
from espncricinfo.match import Match            
import pandas as pd
import numpy as np
import json
# match = Match('1216537')
# print(match.get_json()['team'])

load = True
player_idx = 0
player_positions = set()
# player = Player('1058210')
# print(player.json)
# exit()
if load:
    df = pd.read_csv('updated_players\\updated_players.csv')
    with open('updated_players\save_point.json') as file:
        save_point = json.load(file)
    player_idx = save_point['player_idx']
    if 'no_data' in save_point :
        no_data = set(save_point['no_data'])
    if 'player_positions' in save_point:
        player_positions = set(save_point['player_positions'])
    
    print("Loading from checkpoint at", player_idx)
else:
    df = pd.read_csv('players.csv')
    df['age'] = None
    df['cricinfo_id'] = ''
    df['bowling'] = False
    df['batting'] = False
    df['all_rounder'] = False
    df['position'] = ''
    df['batting_style'] = ''
    df['bowling_style'] = ''

mapping_df = pd.read_csv('player_id_mapping.csv')
player_ids = df['player_id'].tolist()
no_data = set()

for i, player_id in enumerate(player_ids):
    if i <= player_idx:
        continue
    player_mapping = mapping_df.loc[mapping_df['identifier'] == player_id]
    # player_mapping = mapping_df[mapping_df['identifier'] == player_id]
    
    print(i, player_id, end = " ")
    if player_mapping['key_cricinfo'].values.size > 0 and not pd.isnull(player_mapping['key_cricinfo'].values[0]):

        player_cricinfo_id = int(player_mapping['key_cricinfo'].values[0])
        print(player_cricinfo_id)
        bowling = False
        batting = False
        allrounder = False
        batting_style = None
        bowling_style = None
        player = Player(str(player_cricinfo_id))
        if player.json == None:
            print("NO Data on", player_id, player_cricinfo_id)
            no_data.add(player_id)
            player_age = None
            batting = pd.NA
            bowling = pd.NA
            allrounder = pd.NA
            batting_style = None
            bowling_style = None
            player_position_name = None
            continue
        player_json = player.json
        player_styles = player_json['style']
        player_age = player_json['age'] 
        player_position = player_json['position']
        # print("player_position:", player_position)

        if 'batter' or 'Batsman' in player_position['name'].lower():
            batting = True
        if 'bowler' in player_position['name'].lower():
            bowler = True
        if 'allrounder' in player_position['name'].lower():
            allrounder = True
          
            
        player_position_name  = player_position['name']
        
        player_positions.add(player_position_name)
        
        for index, row in enumerate(player_styles):
            if row['type'] == 'batting':
                if 'keeper' in player_position['name'].lower() or player_position_name == 'Unknown':
                    batting = True
                batting_style = row['description']
            if row['type'] == 'bowling':
                if 'keeper' in player_position['name'].lower() or player_position_name == 'Unknown':
                    bowling = True
                bowling_style = row['description']
    else:
        print("NO Data on", player_id)
        no_data.add(player_id)
        player_age = None
        batting = pd.NA
        bowling = pd.NA
        allrounder = pd.NA
        batting_style = None
        bowling_style = None
        player_position_name = None
        
    print(player_age, batting, bowling, allrounder, batting_style, bowling_style, player_position_name) 
    
    df.loc[df['player_id'] == player_id, 'age'] = player_age
    df.loc[df['player_id'] == player_id, 'batting'] = batting
    df.loc[df['player_id'] == player_id, 'bowling'] = bowling
    df.loc[df['player_id'] == player_id, 'all_rounder'] = allrounder
    df.loc[df['player_id'] == player_id, 'batting_style'] = batting_style
    df.loc[df['player_id'] == player_id, 'bowling_style'] = bowling_style 
    df.loc[df['player_id'] == player_id, 'bowling_style'] = bowling_style 
    df.loc[df['player_id'] == player_id, 'player_position'] = player_position_name 
    df.loc[df['player_id'] == player_id, 'cricinfo_id'] = player_cricinfo_id
    
    if i % 50 == 0:
        df.to_csv('updated_players\\updated_players.csv')
        save_point = {'player_idx': i, 'no_data': list(no_data), 'player_positions': list(player_positions)}
        with open('updated_players\save_point.json', 'w') as file:
            json.dump(save_point, file)
        print("Saving checkpoint at player_idx:", i)
df.to_csv('updated_players\\updated_players.csv')
print("Completed all players")