import os
import glob
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Define your directories (update these paths)
input_dir = 'src\data_processing\Global_player_csvs'      # Folder containing the CSV files
output_dir = 'src\data_processing\Cleaned_Global_player_csvs'    # Folder where cleaned CSV files will be saved

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Get list of all CSV files in the input directory
csv_files = glob.glob(os.path.join(input_dir, '*.csv'))

# Define the columns to be processed
numeric_cols = [
    'batting_position', 'runs', 'balls', 'fours', 'sixes', 'strike_rate',
    'overs', 'total_balls', 'dots', 'maidens',
    'conceded', 'fours_conceded', 'sixes_conceded',
    'wickets', 'LBW', 'Bowled', 'noballs',
    'wides', 'economy_rate', 'catches', 'stumping', 'direct_hit', 'indirect_hit'
]

# Define the selected features list (adjust if needed)
selected_features = ['match_id'] + numeric_cols + ['strike_rate_fp', 'batting_fp', 'bowling_fp', 'fielding_fp', 'total_fp']

# Initialize the scaler
scaler = MinMaxScaler()

# Process each CSV file
for csv_file in csv_files:
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)
    
    # Drop unwanted columns if they exist
    for col in ['date', 'event', 'teamname', 'overs_bowled']:
        if col in df.columns:
            df = df.drop(columns=[col])
    
    # Convert specified columns to numeric
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    
    # Normalize the numeric columns
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    
    # Select the desired features
    df_selected = df[selected_features]
    
    # Create the output file path with the same name as the original file
    base_name = os.path.basename(csv_file)
    output_file = os.path.join(output_dir, base_name)
    
    # Save the cleaned DataFrame to CSV without index
    df_selected.to_csv(output_file, index=False)
