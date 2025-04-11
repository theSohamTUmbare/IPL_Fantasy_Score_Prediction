from trash import get_fp
import pandas as pd
import pulp

def PreprocessCSV(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file)
    df = df[df['IsPlaying'] != 'NOT_PLAYING']
    df.sort_values(by=['Team','lineupOrder'],inplace=True)
    player_ids = df['player_id'].tolist()
    teams = df['Team'].tolist()
    total_fp_dict = get_fp(player_ids,teams) #returns a dictionary {player_id: total_fp}
    df['total_fp'] = df['player_id'].map(total_fp_dict)
    return df    
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
        role_indices = df.index[df['player Type'] == role].tolist()
        if role_indices:
            prob += pulp.lpSum(decision_var[i] for i in role_indices) >= MIN_PER_ROLE, f'MIN_{role}'
            prob += pulp.lpSum(decision_var[i] for i in role_indices) <= MAX_PER_ROLE, f'MAX_{role}'
    for team in df['Team'].unique():
        team_indices = df.index[df['Team'] == team].tolist()
        prob += pulp.lpSum(decision_var[i] for i in team_indices) <= MAX_PER_ROLE, f'TeamLimt_{team}'
    
    #solve the optimization problem 
    solution_status = prob.solve()
    print("Optimization Status:", pulp.LpStatus[solution_status])
    selected_indices = [i for i in df.index if pulp.value(decision_var[i] == 1)]
    selected_team_df = df.loc[selected_indices]
    return selected_team_df
def main():
    csv_file = "SquadPlayerNames_IndianT20League - Match_1.csv"
    df = PreprocessCSV(csv_file)
    optimal_team_df = PredictTeam(df)
    optimal_team_df.sort_values(by=['total_fp'])
    print("\nSelected Dream11 Team:")
    print(optimal_team_df[['Player Name', 'Player Type', 'Credits', 'Team', 'total_fp', 'lineupOrder']])
    total_fp_selected = optimal_team_df['total_fp'].sum()
    total_credits_selected = optimal_team_df['Credits'].sum()
    print(f"\nTotal Fantasy Points: {total_fp_selected}")
    print(f"Total Credits Used: {total_credits_selected}")
    


if __name__ == '__main__':
    main()