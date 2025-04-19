import pandas as pd
import pulp
import os 
def _read_file(excel_file =  r'C:\Users\kumar\IPL_Fantasy_Score_Prediction\model18-04-2025\IPL_model_680_loss\Inference\SquadPlayerNames_IndianT20League.xlsx',match_num = 1,output = 'output.csv'):
    df = pd.read_excel(excel_file,sheet_name=f'match_{match_num}')
    Mapping_Unique_SquadPlayerName_IndianT20League_df = pd.read_csv(r'C:\Users\kumar\IPL_Fantasy_Score_Prediction\model18-04-2025\Mapping_Unique_SquadPlayerName_IndianT20League.csv')
    df_lineup = df[df['IsPlaying'] != 'NOT_PLAYING']
    # df_lineup = df_.sort_values(by=['Team','lineupOrder'], ascending=True)
    merged_df = df_lineup.merge(Mapping_Unique_SquadPlayerName_IndianT20League_df[['Player Name', 'Team','identifier']],on =['Player Name','Team'], how = 'left')
    merged_df.dropna(inplace=True)
    ##TODO call the model inference method and pass the identifier (alongside the match_id if we have )
    #Todo the predicted_fps are add back to the merged_df 
    #! merged_df is passed to the predictTeam method
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



    