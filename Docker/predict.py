import pandas as pd # type:ignore
import pulp # type:ignore
import os 
import torch # type:ignore
from model import PlayerMatchDataset, NextFormPredictor, Config, MatchEmbedding, PlayerEmbedding
from weather import get_weather_data
from universal_and_venue_details import get_player_performance
from datetime import datetime
import requests # type:ignore
import zipfile
import io
import json
import numpy as np # type:ignore
import argparse
from sklearn.preprocessing import MinMaxScaler # type:ignore
import joblib  # type:ignore
import  warnings

def update_past_match_info(match_id, match_number):
    match_situation_path = r'Docker\match_situation_data.csv'
    match_situation_df = pd.read_csv(match_situation_path)
    
    match_venue_mapping = pd.read_csv(r'Docker\match_number_venue_mapping.csv')
    # venue_details = pd.read_csv(r'...')
    # venue_details['venue_name'] = venue_details['venue_name'].map(venue_mapping)
    venue_details = match_venue_mapping[match_venue_mapping['Match Number'] == match_number]
    # venue_features = venue_details[venue_details['venue_id'] == venue_details['venue_id']]
    # # now = datetime.now()
    # # date_time = now.strftime("%Y-%m-%d %H:%M:%S") 
    
    
    weather_features = get_weather_data(venue_details['venue_lat'], venue_details['venue_long'], )
    total_match_situation_features = pd.concat([weather_features,venue_details],axis=1).values
    numeric_cols = ['match_number','venue_id','matches','total_runs','total_wickets','bowled_wickets','caught_wickets','lbw_wickets','precipitation','temperature_2m','relative_humidity_2m','dew_point_2m','rain','wind_speed_100m']
    #   !TODO CONFIRM ORDER
    match_sit_scalar = joblib.load(r'Docker\scalars\match_situation_minmax_scalar.pkl.pkl')
    match_situation_features = match_sit_scalar.transform(total_match_situation_features[numeric_cols])
    new_values = match_situation_features.flatten().tolist()  

    # Build a dict of column → value:
    new_match = dict(zip(numeric_cols, new_values))
    new_match['match_id'] = int(match_id)
    # Append via .loc at the next integer index
    next_idx = len(match_situation_df)
    match_situation_df.loc[next_idx] = new_match
    match_situation_df.to_csv(match_situation_path, index=False)
    
    return



def get_current_match_info(merged_df,  match_number):
    
    match_venue_mapping = pd.read_csv(r'Docker\match_number_venue_mapping.csv')
    # venue_details = pd.read_csv(r'...')
    # venue_details['venue_name'] = venue_details['venue_name'].map(venue_mapping)
    venue_details = match_venue_mapping[match_venue_mapping['Match Number'] == match_number]
    # venue_features = venue_details[venue_details['venue_id'] == venue_details['venue_id']]
    # # now = datetime.now()
    # # date_time = now.strftime("%Y-%m-%d %H:%M:%S") 
    
    
    weather_features = get_weather_data(venue_details['venue_lat'], venue_details['venue_long'], )
    total_match_situation_features = pd.concat([weather_features,venue_details],axis=1).values
    numeric_cols = ['match_number','venue_id','matches','total_runs','total_wickets','bowled_wickets','caught_wickets','lbw_wickets','precipitation','temperature_2m','relative_humidity_2m','dew_point_2m','rain','wind_speed_100m']
    #   !TODO CONFIRM ORDER
    match_sit_scalar = joblib.load(r'Docker\scalars\match_situation_minmax_scalar.pkl')
    match_situation_features = match_sit_scalar.transform(total_match_situation_features[numeric_cols])
    player_ids = torch.tensor(player_ids)

    teams = merged_df['Team'].unique()
    team1, team2 = teams[0], teams[1]

    team1_ids = merged_df.loc[merged_df['Team']==team1, 'player_id'].tolist()
    team2_ids = merged_df.loc[merged_df['Team']==team2, 'player_id'].tolist()

    pred_fp = model(player_ids, team1_ids, team2_ids, match_number).detach().numpy()
    match_situation_features = match_situation_features.flatten().tolist()  

    # Build a dict of column → value:
    match_situation_dict = dict(zip(numeric_cols, match_situation_features))
    
    return match_situation_features


def update_match_performances():
    
    with open('latest_updated_match.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    last_match_id = data['latest_match_id']
    url = "https://cricsheet.org/downloads/ipl_json.zip"

    # 2. Download the content
    response = requests.get(url)
    response.raise_for_status()  # will raise an error if the download failed
    z = zipfile.ZipFile(io.BytesIO(response.content))

    # 3. Find all new match-ids > last_id
    new_matches = []
    for member in z.namelist():
        if not member.endswith(".json"):
            continue
        name = os.path.basename(member)
        try:
            mid = int(name[:-5])   # strip “.json” and parse
        except ValueError:
            continue

        if mid > last_match_id:
            new_matches.append((mid, member))

    if not new_matches:
        print("No new matches found.")
        return

    # 4. (Optionally) sort so you extract oldest→newest
    new_matches.sort(key=lambda x: x[0])
    file_paths = []
    EXTRACT_DIR = 'model18-04-2025\Global_raw_dataset\ipl_json'
    # 5. Extract them
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    for mid, member in new_matches:
        print(f"Extracting match {mid}: {member}")
        z.extract(member, EXTRACT_DIR)
        file_path = os.path.join(EXTRACT_DIR, os.path.basename(member))
        player_stats, match_number = get_player_performance(file_path)
        update_past_match_info(mid, match_number)        
        for player_id, player_data in player_stats.values():
            player_path = f"Docker\\Processed_Player_records\\{str(player_id)}.csv"
            player_df = pd.read_csv(player_path)
            numeric_cols = ['match_id', 'batting_position', 'runs', 'balls', 'fours', 'sixes', 'strike_rate', 'overs', 'total_balls', 'dots', 'maidens', 'conceded', 'fours_conceded', 'sixes_conceded', 'wickets', 'LBW', 'Bowled', 'noballs', 'wides', 'economy_rate', 'catches', 'stumping', 'direct_hit', 'indirect_hit', 'strike_rate_fp', 'batting_fp', 'bowling_fp', 'fielding_fp', 'total_fp']
            player_match_performance_dict = {
                'match_id': mid.astype(np.int64),
                'batting_position': player_data['batting_position'],
                'runs': player_data['runs'],
                'balls': player_data['balls'],
                'fours': player_data['fours'],
                'sixes': player_data['sixes'],
                'strike_rate': player_data['strike_rate'],
                'overs': player_data['overs'],
                'total_balls': player_data['total_balls'],
                'dots': player_data['dots'],
                'maidens': player_data['maidens'],
                'conceded': player_data['conceded'],
                'fours_conceded': player_data['fours_conceded'],
                'sixes_conceded': player_data['sixes_conceded'],
                'wickets': player_data['wickets'],
                'LBW': player_data['LBW'],
                'Bowled': player_data['Bowled'],
                'noballs': player_data['noballs'],
                'wides': player_data['wides'],
                'economy_rate': player_data['economy_rate'],
                'catches': player_data['catches'],
                'stumping': player_data['stumping'],
                'direct_hit': player_data['direct_hit'],
                'indirect_hit': player_data['indirect_hit'],
                'strike_rate_fp': player_data['strike_rate_fp'],
                'batting_fp': player_data['batting_fp'],
                'bowling_fp': player_data['bowling_fp'],
                'fielding_fp': player_data['fielding_fp'],
                'total_fp': player_data['total_fp']
            }
            new_match = pd.DataFrame([player_match_performance_dict], columns=player_df.columns)
            # !TODO normalize row with new scalar
            match_performance_scalar = joblib.load(r'Docker\scalars\match_situation_minmax_scalar.pkl.pkl')
            new_match = match_performance_scalar.transform(new_match[numeric_cols])
    
            new_player_df = pd.concat([new_match, player_df], ignore_index=True)
            new_player_df.to_csv(player_path, index=False)
                  
     
    # 6. Update state.json to the highest match-id we saw
    new_max_id = max(mid for mid, _ in new_matches)
    
    data['latest_match_id'] = new_max_id
    
    with open('latest_updated_match.json', 'r', encoding='utf-8') as f:
        json.dump(data, f, indent=2)



def parse_event_time(input_str):
    # Split by commas
    parts = input_str.strip().split(',')
    
    # Extract date and time (assuming always in this format)
    date_str = parts[1].strip()  # e.g., "22 March 2025"
    time_str = parts[2].strip().split()[0]  # e.g., "02:00"

    # Combine date and time for parsing
    datetime_str = f"{date_str} {time_str} {parts[2].strip().split()[1]}"  # e.g., "22 March 2025 02:00 PM"
    
    # Parse datetime
    dt = datetime.strptime(datetime_str, "%d %B %Y %I:%M %p")
    
    # Format output
    date_formatted = dt.strftime("%Y-%m-%d")
    time_formatted = dt.strftime("%H:%M")
    
    return date_formatted,time_formatted



def _read_file(excel_file =  r'Docker\SquadPlayerNames_IndianT20League.xlsx', match_num = 1,output = 'output.csv'):
    update_match_performances()
    df = pd.read_excel(excel_file,sheet_name=f'match_{match_num}')
    Mapping_Unique_SquadPlayerName_IndianT20League_df = pd.read_csv(r'Docker\Mapping_Unique_SquadPlayerName_IndianT20League.csv')
    # player_id_mapping = pd.read_csv(r'...')
    df_lineup = df[df['IsPlaying'] != 'NOT_PLAYING']
    # df_lineup = df_.sort_values(by=['Team','lineupOrder'], ascending=True)
    merged_df = df_lineup.merge(Mapping_Unique_SquadPlayerName_IndianT20League_df[['Player Name', 'Team','identifier']],on =['Player Name','Team'], how = 'left')
    merged_df.dropna(inplace=True)
    ##TODO call the model inference method and pass the identifier (alongside the match_id if we have )
    #Todo the predicted_fps are add back to the merged_df 
    #! merged_df is passed to the predictTeam method
    # player_ids = player_id_mapping[player_id_mapping['Player Name'].isin(merged_df['Player Name'])]['Player ID'].values
    player_ids = merged_df['player_id']
    
    teams = merged_df['Team'].unique()
    team1, team2 = teams[0], teams[1]

    team1_ids = merged_df.loc[merged_df['Team']==team1, 'player_id'].tolist()
    team2_ids = merged_df.loc[merged_df['Team']==team2, 'player_id'].tolist()

    target_match_situation_dict = get_current_match_info(match_num, merged_df)
    dataset = PlayerMatchDataset(
        Config.UNIV_CSV,
        Config.PLAYER_MATCH_CSV,
        Config.MATCH_PLAYER_CSV,
        Config.MATCH_INFO_CSV
    
    )
    pred_fp = get_output(dataset, target_match_situation_dict, team1_ids, team2_ids, player_ids)
    merged_df['total_fp'] = merged_df['total_fp'].astype(float)
    merged_df['total_fp'] = pred_fp
    
    # team_1_ids = 
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
    #TODO change the limits for type_player  (if possible remove multiple X_FACTOR_SUBSTITUTE)
    #! Try to choose more ALL type player 
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


# ---------------- Inference ----------------
def get_inference_sample(dataset, pid, t1_ids, t2_ids, upcoming_info):
    if pid not in dataset.univ_features.index or pid not in dataset.player_match_data:
        warnings.warn(f"Skipping {pid}: not in dataset")
        return None
    univ = dataset.univ_features.loc[pid].values.astype(float)
    univ_tensor = torch.tensor(univ, dtype=torch.float32)
    recent = dataset.player_match_data[pid].tail(dataset.context_len)
    context_feats = recent.drop(columns=['teamname','match_id',
                                        'strike_rate_fp','batting_fp',
                                        'bowling_fp','fielding_fp','total_fp'],
                                errors='ignore').values.astype(float)
    context_tensor = torch.tensor(context_feats, dtype=torch.float32)
    keys = list(dataset.match_info_df.columns)
    t1_list, t2_list, info_list = [], [], []
    for _, r in recent.iterrows():
        mid = int(r['match_id'])
        mpf = os.path.join(dataset.match_players_dir, f"{mid}.csv")
        mp = pd.read_csv(mpf)
        team = r['teamname']
        ids1 = mp.loc[mp['Team']==team, 'player_id'].tolist()
        ids2 = mp.loc[mp['Team']!=team, 'player_id'].tolist()
        f1 = dataset.univ_features.reindex(ids1).dropna().values.astype(float)
        f2 = dataset.univ_features.reindex(ids2).dropna().values.astype(float)
        t1_list.append(f1); t2_list.append(f2)
        info_list.append([dataset.match_info_df.loc[mid].get(k,0.0) for k in keys])
    f1u = dataset.univ_features.reindex(t1_ids).dropna().values.astype(float)
    f2u = dataset.univ_features.reindex(t2_ids).dropna().values.astype(float)
    t1_list.append(f1u); t2_list.append(f2u)
    info_list.append([upcoming_info.get(k,0.0) for k in keys])
    def pad(arrs):
        if not arrs: return torch.empty((0,0,0))
        mx = max(a.shape[0] for a in arrs)
        pads = [np.pad(a, ((0, mx - a.shape[0]), (0,0)), mode='constant') for a in arrs]
        return torch.tensor(np.stack(pads), dtype=torch.float32)
    t1_t = pad(t1_list); t2_t = pad(t2_list)
    info_t = torch.tensor(np.array(info_list), dtype=torch.float32)
    return {'player_id': pid,
            'univ_features': univ_tensor,
            'context_matches': context_tensor,
            'team1_players': t1_t[:,:11,:],
            'team2_players': t2_t[:,:11,:],
            'match_info': info_t}

def get_output(dataset, match_info_dict, team1_ids, team2_ids, player_ids):
    model.eval()
    
    for pid in player_ids:
        samp = get_inference_sample(dataset, pid, team1_ids, team2_ids,
                                    match_info_dict)
        if samp is None: continue
        pe = model.player_embedding_module(samp['univ_features']).unsqueeze(1)
        fl = samp['context_matches'][-1].unsqueeze(0).unsqueeze(1)
        me = model.match_embedding(
            samp['team1_players'][:, -1, :, :].unsqueeze(1),
            samp['team2_players'][:, -1, :, :].unsqueeze(1),
            samp['match_info'][:, -1, :].unsqueeze(1)
        )
        pred = model.fantasy_score_prediction_module(fl, pe, me)
        print(f"Player {pid} → predicted fantasy score: {pred.squeeze().item():.2f}")

# ---------------- CLI Entry Point ----------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fantasy-score inference')
    parser.add_argument('--model-path',         type=str, required=True)
    parser.add_argument('--univ-csv',           type=str, required=True)
    parser.add_argument('--player-matches-dir', type=str, required=True)
    parser.add_argument('--match-players-dir',  type=str, required=True)
    parser.add_argument('--match-info-csv',     type=str, required=True,
                        help='CSV with historical match info')
    parser.add_argument('--upcoming-match-id',  type=int, required=True,
                        help='Match ID of upcoming game for inference')
    parser.add_argument('--team1-ids',          nargs='+', required=True,
                        help='11 player IDs for Team 1')
    parser.add_argument('--team2-ids',          nargs='+', required=True,
                        help='11 player IDs for Team 2')
    parser.add_argument('--lineup-csv',         type=str,
                        help='Optional CSV with column "player_id" for lineup')
    args = parser.parse_args()

    dataset = PlayerMatchDataset(
        Config.UNIV_CSV,
        Config.PLAYER_MATCH_CSV,
        Config.MATCH_PLAYER_CSV,
        Config.MATCH_INFO_CSV
    )
    
    player_emb = PlayerEmbedding(Config.PLAYER_INPUT_DIM, Config.PERFORMANCE_EMBD_DIM)
    fs_pred = FantasyScorePrediction(Config.PERFORMANCE_EMBD_DIM)
    model = NextFormPredictor(
        player_emb,
        MatchEmbedding,
        fs_pred,
        custom_asymmetric_loss,
        Config.PERFORMANCE_EMBD_DIM,
        num_layers=3,
        n_head=4
    ).to(Config.DEVICE)
    load_checkpoint(model, args.model_path)

    lineup = pd.read_csv(args.lineup_csv) if args.lineup_csv else None
    get_output(ds, match_info_dict, args.team1_ids, args.team2_ids, lineup)

    

    