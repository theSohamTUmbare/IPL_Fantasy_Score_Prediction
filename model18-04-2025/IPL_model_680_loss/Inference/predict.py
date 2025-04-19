import pandas as pd
import pulp
import os 
import torch
import model
from datetime import datetime

def get_pred_fp(player_ids, match_number, match_df):
    match_venue_mapping = pd.read_csv(r'...')
    venue_details = pd.read_csv(r'...')
    venue_mapping = {...}
    venue_details['venue_name'] = venue_details['venue_name'].map(venue_mapping)
    venue_id = match_venue_mapping[match_venue_mapping['Match Number'] == match_number]['Venue ID'].values[0]
    venue_features = venue_details[venue_details['venue_id'] == venue_id]
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d %H:%M:%S") 
    weather_features = get_weather(venue_features['venue_lat'], venue_features['venue_long'], date_time)
    total_match_situation_features = pd.concat([weather_features,venue_features],axis=1).values
    numeric_cols = ['venue_name', 'precipitation','temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'rain', 'wind_speed_100m', 'matches', 'total_runs', 'total_wickets', 'bowled_wickets', 'caught_wickets', 'lbw_wickets']
    match_sit_scalar = load_scalar()
    match_situation_features = match_sit_scalar.transform(total_match_situation_features[numeric_cols])
    player_ids = torch.tensor(player_ids)
    pred_fp = model(, opp_player_features, match_situation_features).detach().numpy()

    numeric_cols = ['venue_name', 'precipitation','temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'rain', 'wind_speed_100m', 'matches', 'total_runs', 'total_wickets', 'bowled_wickets', 'caught_wickets', 'lbw_wickets']
    




def _read_file(excel_file =  r'C:\Users\kumar\IPL_Fantasy_Score_Prediction\model18-04-2025\IPL_model_680_loss\Inference\SquadPlayerNames_IndianT20League.xlsx',match_num = 1,output = 'output.csv'):
    df = pd.read_excel(excel_file,sheet_name=f'match_{match_num}')
    Mapping_Unique_SquadPlayerName_IndianT20League_df = pd.read_csv(r'C:\Users\kumar\IPL_Fantasy_Score_Prediction\model18-04-2025\Mapping_Unique_SquadPlayerName_IndianT20League.csv')
    player_id_mapping = pd.read_csv(r'...')
    df_lineup = df[df['IsPlaying'] != 'NOT_PLAYING']
    # df_lineup = df_.sort_values(by=['Team','lineupOrder'], ascending=True)
    merged_df = df_lineup.merge(Mapping_Unique_SquadPlayerName_IndianT20League_df[['Player Name', 'Team','identifier']],on =['Player Name','Team'], how = 'left')
    merged_df.dropna(inplace=True)
    ##TODO call the model inference method and pass the identifier (alongside the match_id if we have )
    #Todo the predicted_fps are add back to the merged_df 
    #! merged_df is passed to the predictTeam method
    player_ids = player_id_mapping[player_id_mapping['Player Name'].isin(merged_df['Player Name'])]['Player ID'].values
    pred_fp = get_pred_fp(player_ids)
    merged_df['total_fp'] = merged_df['total_fp'].astype(float)
    merged_df['total_fp'] = pred_fp
    optimal_team_df = PredictTeam(merged_df)
    optimal_team_df.sort_values(by=['total_fp'],ascending= False)
    curr = os.getcwd()
    output_df = optimal_team_df[['Player Type','Player Name','Team','lineuporder','total_fp']]
    #? just need the Player Name in the csv and the captain and vice-captain 
    #! 4 backups if needed (optional)
    curr = os.getcwd()
    output_path = os.path.join(curr, output)
    output_df.to_csv(output_path, index=False)
    print(f"Optimal team saved to {output_path}")
    print(f"Total fanstasy point of the team is : {optimal_team_df['total_fp'].sum()}")
    
        

    
def PredictTeam(df: pd.DataFrame):
    """ 
    The optimization maximizes the total fanstasy points while satisfying the following Contraints:-
    -Exactly 11 pplayers are selected.
    -The total credits of selected players does not exceed 100
    -For each player type (role) the selection is between the specified minimum and maximum limits.
    -No more than the maximum allowed players are selected from any single real-life team.
    
    :params df: processed DataFrame containing Players details including expected fanstasy score
    : return : list of ids of 11 players (maybe including their names.)
    """
    #Dream 11 constraints 
    Total_Players = 11
    MAX_TOTAL_CREDITS = 100
    MIN_PER_ROLE = 1
    MAX_PER_ROLE = 4
    MAX_PER_TEAM = 7  # Adjust this based on your requirements
    roles = ['BAT','BOWL','WK','ALL']
    prob = pulp.LpProblem(name='OPtimal_Team',sense=pulp.LpMaximize)
    decision_var = {i : pulp.LpVariable(f'x_{i}',cat='Binary') for i in df.index}
    prob += pulp.lpSum(df.loc[i,'total_fp']* decision_var[i] for i in df.index), 'TotalFantasyPoints'
    prob += pulp.lpSum(decision_var[i] for i in df.index) == Total_Players, 'TotalPlayers'
    prob += pulp.lpSum(df.loc[i,'Credits']*decision_var[i] for i in df.index) <= MAX_TOTAL_CREDITS ,'CreditLimit'
    for role in roles:
        role_indices = df.index[df['Player Type'] == role].tolist()
        if role_indices:
            prob += pulp.lpSum(decision_var[i] for i in role_indices) >= MIN_PER_ROLE, f'MIN_{role}'
            prob += pulp.lpSum(decision_var[i] for i in role_indices) <= MAX_PER_ROLE, f'MAX_{role}'
    for team in df['Team'].unique():
        team_indices = df.index[df['Team'] == team].tolist()
        prob += pulp.lpSum(decision_var[i] for i in team_indices) <= MAX_PER_TEAM, f'TeamLimt_{team}'
    
    #solve the optimization problem 
    solution_status = prob.solve()
    # print(prob)
    print("Optimization Status:", pulp.LpStatus[solution_status])
    selected_indices = [i for i in df.index if pulp.value(decision_var[i] == 1)]
    selected_team_df = df.loc[selected_indices]
    return selected_team_df

# add path to match_number venue_id mapping
# adding path for player_id to player_name mapping


# loading scalars
def add_match_data():
    pass

def get_pred_fp(player_id, model):
    pass

def get_pred_team(match_number, player_names_team_1, player_names_team_2, playing_or_not):
    match_venue_mapping = pd.read_csv(r"/inference/player_id_mapping.csv")
    player_id_mapping = pd.read_csv(r"/inference/player_id_mapping.csv")
    
    

    