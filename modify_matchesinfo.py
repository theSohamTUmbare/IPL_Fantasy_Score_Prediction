import pandas as pd
import json
from espncricinfo.match import Match


recent_matches_df = pd.read_csv('IPL_Fantasy_Score_Prediction\\matches_info.csv')

match_ids = recent_matches_df['match_id'].tolist()
# i = 0
no_weather_data = []
for i, match_id in enumerate(match_ids):
    match_data = Match(str(match_id))
    match_date, match_time = match_data.json['match']['next_datetime_local'].split(" ")
    match_town_name = match_data.json['match']['town_name']
    match_town_id = match_data.json['match']['town_id']
    if match_town_id is None:
        no_weather_data.append({match_id: ['town_id']})
        print(f"Match ID {match_id} not found in matches_data.")
    if match_town_name is None:
        if match_id not in no_weather_data:
            no_weather_data.append({match_id: ['town_name']})
            print(f"Match ID {match_id} not found in matches_data.")
        else:
            no_weather_data[match_id].append('town_name')
            print(f"Match ID {match_id} not found in matches_data.")
    if match_date is None:
        if match_id not in no_weather_data:
            no_weather_data.append({match_id: ['match_date']})
            print(f"Match ID {match_id} not found in matches_data.")
        else:
            no_weather_data[match_id].append('match_date')
            print(f"Match ID {match_id} not found in matches_data.")
    if match_time is None:
        if match_id not in no_weather_data:
            no_weather_data.append({match_id: ['match_time']})
            print(f"Match ID {match_id} not found in matches_data.")
        else:
            no_weather_data[match_id].append('match_time')
            print(f"Match ID {match_id} not found in matches_data.")
        print(f"Match ID {match_id} not found in matches_data.")
    
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'town_id'] = match_town_id
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'town_name'] = match_town_name
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'match_date'] = match_date
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'match_time'] = match_time
    print(i, match_id, match_date, match_time, match_town_name, match_town_id)
    if i % 25 == 0 and i != 0:
        print(f"Processed {i} matches.")
        recent_matches_df.to_csv('IPL_Fantasy_Score_Prediction\\updated_matches_info.csv', index=False)

recent_matches_df.to_csv('IPL_Fantasy_Score_Prediction\\updated_matches_info.csv', index=False)
    