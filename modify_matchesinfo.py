import pandas as pd
import json
from espncricinfo.match import Match



load = True
# player = Player('1058210')
# print(player.json)
# exit()
if load:
    recent_matches_df = pd.read_csv('updated_match_info\\updated_matches_info3.csv')
    with open('updated_match_info\\save_point.json') as file:
        save_point = json.load(file)
    match_idx = save_point['match_idx']
    if 'no_weather_data' in save_point :
        no_weather_data = save_point['no_weather_data']
    print("Loading from checkpoint at", match_idx)
    # set column to dtype
    # recent_matches_df['town_id'] = recent_matches_df['town_id'].astype(str)
    # recent_matches_df['town_name'] = recent_matches_df['town_name'].astype(str)
    recent_matches_df['match_date'] = recent_matches_df['match_date'].astype(str)
    recent_matches_df['match_time'] = recent_matches_df['match_time'].astype(str)
else:
    match_idx = -1
    recent_matches_df = pd.read_csv('updated_match_info\\final.csv')

all_match_jsons = []

match_ids = recent_matches_df['match_id'].tolist()
# match_ids = []
# i = 0
no_weather_data = []
for i, match_id in enumerate(match_ids):
    if i <= match_idx:
        continue
    match_data = Match(str(match_id))
    all_match_jsons.append({match_id: match_data.json})

    if (len(match_data.json['match']['next_datetime_gmt'].split(" ")) == 1):
        data = match_data.json['match']['next_datetime_gmt'].split(" ")   
        if '-' in data:
            match_date = data[0]
            match_time = None
        else:
            match_date = None
            match_time = data[0]
    else:
        match_date, match_time = match_data.json['match']['next_datetime_gmt'].split(" ") if match_data.json['match']['next_datetime_gmt'].split(" ") else (None, None)
    
    # match_town_name = match_data.json['match']['town_name']
    # match_town_id = match_data.json['match']['town_id']
    # if match_town_id is None:
    #     no_weather_data.append({match_id: ['town_id']})
    #     print(f"Match ID {match_id} not found in matches_data.")
    # if match_town_name is None:
    #     if match_id not in no_weather_data:
    #         no_weather_data.append({match_id: ['town_name']})
    #         print(f"Match ID {match_id} not found in matches_data.")
    #     else:
    #         no_weather_data[match_id].append('town_name')
    #         print(f"Match ID {match_id} not found in matches_data.")
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
    
    # recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'town_id'] = str(match_town_id) if match_town_id is not None else None
    # recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'town_name'] = match_town_name
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'match_date'] = match_date
    recent_matches_df.loc[recent_matches_df['match_id'] == match_id, 'match_time'] = match_time
    print(i, match_id, match_date, match_time)
    if i % 100 == 0 and i != 0:
        recent_matches_df.to_csv('updated_match_info\\updated_matches_info3.csv', index=False)
        # saving to json
        save_point = {'match_idx': i, 'no_weather_data': no_weather_data}
        with open('updated_match_info\\save_point.json', 'w') as file:
            json.dump(save_point, file)
        try:
            with open('updated_match_info\\matches2.json', 'r') as f:
                existing_jsons = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_jsons = []

        existing_jsons.extend(all_match_jsons)
        with open('updated_match_info\\matches2.json', 'w') as f:
            json.dump(existing_jsons, f)

        # Clear the list for the next batch
        all_match_jsons.clear()

        print(f"Saved and Processed {i} matches.")
        # print(f"Saved and Processed {i} matches.")
# total_runs,total_wickets,bowled_wickets,caught_wickets,lbw_wickets,town_id
try:
    with open('updated_match_info\\matches2.json', 'r') as f:
            existing_jsons = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    existing_jsons = []

existing_jsons.extend(all_match_jsons)
with open('updated_match_info\\matches2.json', 'w') as f:
    json.dump(existing_jsons, f)
    
save_point = {'match_idx': len(match_ids), 'no_weather_data': no_weather_data}
with open('updated_match_info\\save_point.json', 'w') as file:
    json.dump(save_point, file)

recent_matches_df.to_csv('updated_match_info\\updated_matches_info3.csv', index=False)

import numpy as np #type: ignore
mask = recent_matches_df['venue_id'].isin([np.inf, -np.inf]) | recent_matches_df['venue_id'].isnull()
match_ids_with_invalid_values = recent_matches_df.loc[mask, 'match_id']
print("Match IDs with None or infinite values:")
print(match_ids_with_invalid_values.tolist()), 
exit()




# recent_matches_df = recent_matches_df.replace([np.inf, -np.inf], np.nan).dropna(subset=['venue_id', 'town_id'])

# recent_matches_df['venue_id'] = recent_matches_df['venue_id'].astype(float).astype(int).astype(str)
# recent_matches_df['town_id'] = recent_matches_df['town_id'].astype(float).astype(int).astype(str)
# recent_matches_df['total_runs'] = recent_matches_df['total_runs'].astype(float).astype(int)
# recent_matches_df['total_wickets'] = recent_matches_df['total_wickets'].astype(float).astype(int)
# recent_matches_df['bowled_wickets'] = recent_matches_df['bowled_wickets'].astype(float).astype(int)
# recent_matches_df['caught_wickets'] = recent_matches_df['caught_wickets'].astype(float).astype(int)
# recent_matches_df['lbw_wickets'] = recent_matches_df['lbw_wickets'].astype(float).astype(int)
# exit()
# venue_ids = recent_matches_df['venue_id'].tolist()
# # print(venue_ids)
# # exit()
# venues_df = pd.read_csv('venue_features.csv')

# for i, venue_id in enumerate(venue_ids):
#     if venue_id is not pd.NA:
#         continue
#     venue_data = venues_df[venues_df['venue_id'] == int(venue_id)]
#     if venue_data.empty:
#         print(f"Venue ID {venue_id} not found in venues_df.")
#         continue
#     venue_long = venue_data['venue_long'].iloc[0]
#     venue_lat = venue_data['venue_lat'].iloc[0]
#     mask = recent_matches_df['venue_id'] == venue_id
#     recent_matches_df.loc[mask, 'venue_long'] = venue_long
#     recent_matches_df.loc[mask, 'venue_lat'] = venue_lat

    
# recent_matches_df.to_csv('updated_match_info\\updated_matches_info.csv', index=False)

    