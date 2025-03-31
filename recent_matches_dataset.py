from espncricinfo.player import Player
from espncricinfo.match import Match
import pandas as pd # type: ignore
import json
import os

# def save_matches():
    # """Save matches to json file"""
    
players_path = r'C:\Users\bitso\OneDrive\Desktop\ipl hackathon\IPL_Fantasy_Score_Prediction\src\data_processing\Global_MatchData'
players_df = pd.read_csv('C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\updated_players\\updated_players.csv')
no_player_data = []
no_venue_data = []

filenames = os.listdir(players_path)  # List all files and folders in the directory 
for file_idx in range(len(filenames)):
    if not filenames[file_idx].endswith('.csv'):
        continue
    filename = filenames[file_idx]
    print(filename)
    file_path = os.path.join(players_path, filename)
    match_df = pd.read_csv(file_path)
    player_ids = match_df['player_id'].tolist()
    match_df['age'] = match_df.get('age', pd.Series(dtype='Int64'))  # Use Int64 to allow for NaN values
    match_df['batting'] = match_df.get('batting', pd.Series(dtype='bool'))  # Use bool to allow for NaN values
    match_df['bowling'] = match_df.get('bowling', pd.Series(dtype='bool')) 
    match_df['all_rounder'] = match_df.get('all_rounder', pd.Series(dtype='bool')) 
    match_df['bowling_style'] = match_df.get('bowling_style', pd.Series(dtype='string'))
    match_df['batting_style'] = match_df.get('batting_style', pd.Series(dtype='string')) 
    
    for player_id in player_ids:
        # print("player_id", player_id)
        player = players_df.loc[players_df['player_id'] == player_id] 
        if player.empty:
            print(f"Player with ID {player_id} not found in players_df.")
            no_player_data.append(player_id)
            continue
        player_age = player['age'].values[0] if len(player['age'].values) > 0 else None
        player_batting = player['batting'].values[0] if len(player['batting'].values) > 0 else None
        player_bowling = player['bowling'].values[0] if len(player['bowling'].values) > 0 else None
        player_all_rounder = player['all_rounder'].values[0] if len(player['all_rounder'].values) > 0 else None
        player_bowling_style = player['bowling_style'].values[0] if len(player['bowling_style'].values) > 0 else None
        player_batting_style = player['batting_style'].values[0] if len(player['batting_style'].values) > 0 else None
    
        match_df.loc[match_df['player_id'] == player_id, 'age'] = int(player_age) if pd.notna(player_age) else pd.NA
        match_df.loc[match_df['player_id'] == player_id, 'batting'] = player_batting
        match_df.loc[match_df['player_id'] == player_id, 'bowling'] = player_bowling
        match_df.loc[match_df['player_id'] == player_id, 'all_rounder'] = player_all_rounder
        match_df.loc[match_df['player_id'] == player_id, 'bowling_style'] = player_bowling_style
        match_df.loc[match_df['player_id'] == player_id, 'batting_style'] = player_batting_style
    # match_df.to_csv('player_test.csv', index=False)
    # break
    match_df.to_csv(file_path, index=False)


with open('no_data.json', 'w') as f:
    no_data = {
        "no_player_data": no_player_data,
        # "no_venue_data": no_venue_data
    }
    json.dump(no_data, f)

# with open('C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\IPL_Fantasy_Score_Prediction\\save_matches\\matches.json') as file:
#     matches_data = json.load(file)
#     matches_data = {match_id.split(" ")[0]: data for match_id, data in matches_data.items()}

# # for match_id, data in matches_data.items():
# #     print(match_id, data['venue_data'])
# #     # exit()
# #     break
# recent_matches_df = pd.read_csv('IPL_Fantasy_Score_Prediction\matches_info.csv')

# match_ids = recent_matches_df['match_id'].tolist()
# for match_id in match_ids:
#     match_data = matches_data.get(str(match_id))
#     print(match_id)
#     if match_data is None:
#         no_venue_data.append(match_id)
#         print(f"Match ID {match_id} not found in matches_data.")
#         continue  # Skip to the next iteration if match_data is None
    
#     venue_data = match_data.get('venue_data')
#     if venue_data is None:
#         no_venue_data.append(match_id)
#         print(f"Venue data not found for Match ID {match_id}.")
#         continue
#     # print(venue_data)
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'venue_id'] = venue_data['venue_id']
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'venue_name'] = venue_data['venue_name']
#     # matches,total_runs,total_wickets,bowled_wickets,caught_wickets,lbw_wickets
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'total_runs'] = int(venue_data['total_runs']) if not pd.isna(venue_data['total_runs']) else 0
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'total_wickets'] = int(venue_data['wickets']) if not pd.isna(venue_data['total_runs']) else 0
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'bowled_wickets'] = int(venue_data['bowled']) if not pd.isna(venue_data['total_runs']) else 0
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'caught_wickets'] = int(venue_data['caught']) if not pd.isna(venue_data['total_runs']) else 0
#     recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'lbw_wickets'] = int(venue_data['lbw']) if not pd.isna(venue_data['total_runs']) else 0
#     # recent_matches_df.to_csv('match_test.csv', index=False)
# #     break
# # exit()
# recent_matches_df.to_csv('IPL_Fantasy_Score_Prediction\matches_info.csv', index=False)
# # save no_player_data to json file
# with open('no_data.json', 'w') as f:
#     no_data = {
#         # "no_player_data": no_player_data,
#         "no_venue_data": no_venue_data
#     }
#     json.dump(no_data, f)









# with open('save_matches/matches.json', 'r') as f:
#     matches = json.load(f)

# for match_id, data in matches.items():
#     print(match_id.split(" "), data['venue_data'])
#     exit()
    
# print(matches.get('1001349 T20I'))
