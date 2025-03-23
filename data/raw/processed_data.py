import pandas as pd
import numpy as np

# ---------------------------
# 1. Load Source CSV Files
# ---------------------------
batting = pd.read_csv('./data/raw/Batting_data.csv')
bowling = pd.read_csv('./data/raw/Bowling_data.csv')
fielding = pd.read_csv('./data/raw/Fielding_Data.csv')
fantasy = pd.read_csv('./data/raw/Final_Fantasy_data.csv')

# ---------------------------
# 2. Aggregate Batting Data
# ---------------------------
# Compute averages for batting features per player
batting_agg = batting.groupby('fullName').agg({
    'runs': 'mean',              # Average runs per match
    'strike_rate': 'mean',       # Average strike rate
    'fours': 'mean',             # Average fours per match
    'sixes': 'mean',             # Average sixes per match
    'balls': 'mean'              # Average balls faced
}).reset_index()
batting_agg.columns = ['fullName', 'avg_runs', 'avg_strike_rate', 'avg_fours', 'avg_sixes', 'avg_balls_faced']

# Count centuries (runs >= 100) and half-centuries (50 <= runs < 100)
centuries = batting[batting['runs'] >= 100].groupby('fullName').size().reset_index(name='centuries')
half_centuries = batting[(batting['runs'] >= 50) & (batting['runs'] < 100)].groupby('fullName').size().reset_index(name='half_centuries')
batting_agg = batting_agg.merge(centuries, on='fullName', how='left').merge(half_centuries, on='fullName', how='left')
batting_agg['centuries'] = batting_agg['centuries'].fillna(0)
batting_agg['half_centuries'] = batting_agg['half_centuries'].fillna(0)

# ---------------------------
# 3. Aggregate Bowling Data
# ---------------------------
# Compute averages for bowling features per player
bowling_agg = bowling.groupby('fullName').agg({
    'total_balls': 'mean',       # Average balls bowled per match
    'dots': 'mean',              # Average dot balls per match
    'conceded': 'mean',          # Average runs conceded
    'wickets': 'mean',           # Average wickets per match
    'economyRate': 'mean',       # Average economy rate
    'overs': 'median'            # Median overs bowled as a proxy for consistency
}).reset_index()
bowling_agg.columns = ['fullName', 'avg_balls_bowled', 'avg_dots', 'avg_conceded', 'avg_wickets', 'avg_economy', 'median_overs']

# ---------------------------
# 4. Aggregate Fielding Data
# ---------------------------
# Compute average fielding fantasy points per player
fielding_agg = fielding.groupby('fullName').agg({
    'Fielding_FP': 'mean'
}).reset_index()
fielding_agg.columns = ['fullName', 'avg_fielding_FP']

# ---------------------------
# 5. Aggregate Fantasy Points Data
# ---------------------------
# Use Total_FP as the overall fantasy point metric
fantasy_agg = fantasy.groupby('fullName').agg({
    'Total_FP': 'mean'
}).reset_index()
fantasy_agg.columns = ['fullName', 'avg_total_FP']

# ---------------------------
# 6. Merge All Aggregated Data
# ---------------------------
# Merge all data on fullName (our proxy for player ID)
df = batting_agg.merge(bowling_agg, on='fullName', how='outer')\
                .merge(fielding_agg, on='fullName', how='outer')\
                .merge(fantasy_agg, on='fullName', how='outer')
df.fillna(0, inplace=True)

# ---------------------------
# 7. Create Final DataFrame with Desired Columns
# ---------------------------
# Note: "Player_learned_embedding" is a placeholder that will be learned during training.
final_df = pd.DataFrame({
    'fullName': df['fullName'],
    'Player_learned_embedding': '',  # Placeholder for the learned embedding
    'Total_Runs_Scored_per_match': df['avg_runs'],
    'Total_Runs_Scored_per_T20_match': df['avg_runs'],  # Assuming T20 is the only format here
    'strike_rate_Global': df['avg_strike_rate'],
    'strike_rate_T20': df['avg_strike_rate'],  # Same as above
    'avg_fours_per_T20_match': df['avg_fours'],
    'avg_sixes_per_T20_match': df['avg_sixes'],
    'avg_fantasy_point_scored_in_T20_match': df['avg_total_FP'],
    'Balls_Played': df['avg_balls_faced'],
    'Avg_Balls_Thrown_per_T20_match': df['avg_balls_bowled'],
    'avg_dot_balls_per_T20_match': df['avg_dots'],
    'avg_median_overs_per_T20_match': df['median_overs'],
    'avg_run_conceded_per_T20': df['avg_conceded'],
    'avg_wickets_taken_per_match': df['avg_wickets'],
    'avg_economyRate_per_match': df['avg_economy'],
    'avg_fielding_FP': df['avg_fielding_FP'],
    'total_centuries': df['centuries'],
    'total_halftcenturies': df['half_centuries']
})

# ---------------------------
# 8. Save the Final DataFrame to CSV
# ---------------------------
final_df.to_csv('Player_Features.csv', index=False)
print("CSV file 'Player_Features.csv' has been created.")
