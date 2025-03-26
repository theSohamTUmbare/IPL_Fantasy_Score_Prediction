from espncricinfo.match import Match
from espncricinfo.player import Player
import json

# m = Match('1426306')
# match_json = m.match_json
# print(m.json['comms'])

# ['68079', '68209', '68081', '61375', '65429']
import os

import json
import os
import numpy as np
import pandas as pd
folder_path = "C:\\Users\\bitso\\OneDrive\\Desktop\\ipl hackathon\\ipl_json"
filenames = os.listdir(folder_path)  # List all files and folders in the directory
print(len(filenames))
# player_data = Player('474307')
# print(player_data)
# exit()
# for filename in filenames:
#     match_id = filename.split(".")[0]
#     m = Match(match_id)
# #     # match_json = m.match_json
#     print(m.json['team'])
# #     # print(m.json)
#     break


# Helper functions
def overs_to_balls(overs_str):
    """Convert overs (e.g., '3.4') to total balls bowled."""
    if '.' in overs_str:
        overs, balls = overs_str.split('.')
        return int(overs) * 6 + int(balls)
    return int(overs_str) * 6

def str_to_float(overs_str):
    """Convert overs to a float value (e.g., '3.4' -> 3.6667)."""
    if '.' in overs_str:
        overs, balls = overs_str.split('.')
        return int(overs) + int(balls) / 6
    return float(overs_str)

# Initialize dictionaries to store player and venue data
players = {}
venues = {}
matches = []
# venue_names = set()
# Specify the folder containing JSON files
# folder_path = "path_to_your_json_folder"  # Replace with actual path

# Process each JSON file
count = 0
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        match_id = filename.split(".")[0]
        print("Processing match: ", match_id)
        # with open(os.path.join(folder_path, filename), 'r') as f:
        #     match_data.json = json.load(f)
        match_data = Match(match_id)

        
        # print(data)
        # break
        # for key, value in match_data.get_json.items():
        #     print(key, " = ",  value, " ")
        # Extract venue information
        for m in match_data.json['match']:
            print(m)
        # break 
        # team1_short_name = match_data.json['match'].get('team1_short_name', 'Unknown')
        # team2_short_name = match_data.json['match'].get('team2_short_name', 'Unknown')
        # date = match_data.json['match'].get('start_date', 'Unknown')
        # runs_team1 = int(match_data.json['innings'][0].get('runs', 0))
        # runs_team2 = int(match_data.json['innings'][1].get('runs', 0))
        # wickets_team1 = int(match_data.json['innings'][0].get('wickets', 0))
        # wickets_team2 = int(match_data.json['innings'][1].get('wickets', 0))

        # break
        venue_id = match_data.json['match'].get('ground_id', len(venues))
        # venue_id = len(venue_names)
        venue_name = match_data.json['match'].get('ground_name', 'unknown')
        # venue_names.add(venue_name)
        
        if venue_id not in venues:
            venues[venue_id] = {
                'name': venue_name,
            }
        # print(venues[venue_id])
        venues[venue_id]['matches'] += 1

        # Extract playing XI
        print(match_data.json['team'])
        team1_players = [p['player_id'] for p in match_data.json['team'][0]['player']]
        team2_players = [p['player_id'] for p in match_data.json['team'][1]['player']] if len(match_data.json['team']) > 1 else []
        all_players = team1_players + team2_players
        # print(len(all_players))
        # Record matches played
        # print(match_data.json['']
        #       )
        # break
    
        for player_id in all_players:
            if player_id not in players:
                players[player_id] = {
                    'matches_played': [],
                    'batting_innings': [],
                    'bowling_innings': []
                }
            players[player_id]['matches_played'].append(match_id)

        # Extract batting and bowling stats
        # print(match_data.json['centre'])
        centre_data = match_data.json.get('centre', {})
        # for key, value in match_data.json['centre'].items():
        #     print(key, " = ",  value, " ")
        # print(centre_data)
        # Batting stats
        batting_stats = centre_data.get('batting', [])
        # print(batting_stats)
        for batsman in batting_stats:
            player_id = str(batsman['player_id'])
            if player_id not in players:
                players[player_id] = {
                    'matches_played': [match_id],
                    'batting_innings': [],
                    'bowling_innings': []
                }
            runs = int(batsman.get('runs', 0))
            balls = int(batsman.get('balls_faced', 0))
            
            # for key, value in batsman.items():
            #     print(key, " = ",  value, " ")
            # break
            runs_summary = [int(x) for x in batsman.get('runs_summary', ['0'] * 7)]
            dot_balls = runs_summary[0]
            fours = runs_summary[4] if len(runs_summary) > 4 else 0
            sixes = runs_summary[6] if len(runs_summary) > 6 else 0
            dismissal_type = batsman.get('dismissal_name', '')
            
            # print(runs, balls, fours, sixes, dismissal_type)
        
            players[player_id]['batting_innings'].append({
                'runs': runs,
                'balls': balls,
                'dot_balls': dot_balls,
                'fours': fours,
                'sixes': sixes
            })
            
            # Update venue stats
            venues[venue_id]['total_runs'] += runs
            if dismissal_type and dismissal_type.lower() != 'not out':
                venues[venue_id]['total_wickets'] += 1
                if dismissal_type.lower() == 'bowled':
                    venues[venue_id]['bowled_wickets'] += 1
                if dismissal_type.lower() == 'caught':
                    venues[venue_id]['caught_wickets'] += 1
        # Bowling stats
        bowling_stats = centre_data.get('bowling', [])
        for bowler in bowling_stats:
            player_id = str(bowler['player_id'])
            if player_id not in players:
                players[player_id] = {
                    'matches_played': [match_id],
                    'batting_innings': [],
                    'bowling_innings': []
                }
            # print(bowler)
            # for key, value in bowler.items():
            #     print(key, " = ",  type(value), " ")
            overs_str = bowler.get('overs', '0.0')
            balls_bowled = overs_to_balls(overs_str)
            runs_conceded = int(bowler.get('conceded', 0))
            wickets = int(bowler.get('wickets', 0))
            maidens = int(bowler.get('maidens', 0))
            economy_rate = str_to_float(batsman.get('economy_rate', '5.0'))
            # print(overs_str, balls_bowled, runs_conceded, wickets, maidens)
            # break
            
            players[player_id]['bowling_innings'].append({
                'overs': str_to_float(overs_str),
                'balls_bowled': balls_bowled,
                'runs_conceded': runs_conceded,
                'wickets': wickets,
                'maidens': maidens,
                'economy_rate': economy_rate
            })
        
        
        # match_dict = {
        #     'match_id': match_id,
        #     'teams': team1_short_name + " VS " + team2_short_name,
        #     'date': date,
        #     'runs_team1': runs_team1,
        #     'runs_team2': runs_team2,
        #     'wickets_team1': wickets_team1,
        #     'wickets_team2': wickets_team2,
        #     'venue_name': venue_name
        # }
        # matches.append(match_dict)
        
        count += 1
        print("Processed match: ", match_id, "Count: ", count)
        
        # if count == 5:
        #     break
    break
exit()
# Compute player features
player_features = []
for player_id, data in players.items():
    batting_innings = data['batting_innings']
    bowling_innings = data['bowling_innings']

    # Batting features
    total_runs = sum(inn['runs'] for inn in batting_innings)
    total_balls = sum(inn['balls'] for inn in batting_innings)
    total_fours = sum(inn['fours'] for inn in batting_innings)
    total_sixes = sum(inn['sixes'] for inn in batting_innings)
    total_dot_balls = sum(inn['dot_balls'] for inn in batting_innings)
    total_centuries = sum(1 for inn in batting_innings if inn['runs'] >= 100)
    total_half_centuries = sum(1 for inn in batting_innings if inn['runs'] >= 50)
    highest_runs = max(inn['runs'] for inn in batting_innings) if batting_innings else 0

    
    strike_rate = (total_runs / total_balls) * 100 if total_balls > 0 else 0
    four_rate = total_fours / total_balls if total_balls > 0 else 0
    six_rate = total_sixes / total_balls if total_balls > 0 else 0
    dot_ball_rate = total_dot_balls / total_balls if total_balls > 0 else 0

    # Bowling features
    total_balls_bowled = sum(inn['balls_bowled'] for inn in bowling_innings)
    total_runs_conceded = sum(inn['runs_conceded'] for inn in bowling_innings)
    total_wickets = sum(inn['wickets'] for inn in bowling_innings)
    total_maidens = sum(inn['maidens'] for inn in bowling_innings)
    total_overs_bowled = sum(inn['overs'] for inn in bowling_innings)
    highest_wickets = max(inn['wickets'] for inn in bowling_innings) if bowling_innings else 0
    avg_economy_rate = sum(inn['economy_rate'] for inn in bowling_innings) / len(bowling_innings) if len(bowling_innings) > 0 else 0

    # floor_overs_bowled = np.floor(total_overs_bowled)
    # maiden_over_rate = total_maidens / floor_overs_bowled if floor_overs_bowled > 0 else 0
    # avg_runs_conceded = total_runs_conceded / total_balls_bowled if total_balls_bowled > 0 else 0
    # wickets_taken = total_wickets / total_balls_bowled if total_balls_bowled > 0 else 0

    # Player occupation
    occupation = 2 if batting_innings and bowling_innings else (0 if batting_innings else (1 if bowling_innings else -1))

    player_features.append({
        '_id': player_id,
        'Player Occupation': occupation,
        'Total Runs Scored in all matches combined': total_runs,
        'strike rate in all matches combined': strike_rate,
        'no. of fours': total_fours,
        'no. of sixes': total_sixes,
        'highest runs scored in a match': highest_runs,
        'Balls Played till now': total_balls,
        'no. of dot_balls': dot_ball_rate,
        'maiden_overs': total_maidens,
        'run conceded': total_runs_conceded,
        'Average Economy Rate': avg_economy_rate,
        'no. of wickets': total_wickets,
        'no. of balls thrown': total_balls_bowled,
        'highest wickets taken in a match': highest_wickets,
        'total_centuries': total_centuries,
        'total_halfcenturies': total_half_centuries
    })

# Compute venue features
venue_features = []
for venue_id, data in venues.items():
    matches = data['matches']
    total_runs = data['total_runs']
    total_wickets = data['total_wickets']
    bowled_wickets = data['bowled_wickets']
    caught_wickets = data['caught_wickets']
    print(total_wickets, bowled_wickets, caught_wickets) 
    avg_runs = total_runs / matches if matches > 0 else 0
    avg_wickets = total_wickets / matches if matches > 0 else 0
    bowled_ratio = bowled_wickets / total_wickets if total_wickets > 0 else 0
    caught_ratio = caught_wickets / total_wickets if total_wickets > 0 else 0
    venue_features.append({
        'Venue ID': venue_id,
        'Venue Name': data['name'],
        'Historical average Runs at the venue': avg_runs,
        'Historical Average Wickets in Venue': avg_wickets,
        'Bowled wickets/ total wickets ratio': bowled_ratio,
        'Caught wickets/ total wickets ratio': caught_ratio
    })

# Save to CSV
df_players = pd.DataFrame(player_features)
df_players.to_csv('player_features.csv', index=False)
df_venues = pd.DataFrame(venue_features)
df_venues.to_csv('venue_features.csv', index=False)
print("Player features saved to 'player_features.csv'")
print("Venue features saved to 'venue_features.csv'")