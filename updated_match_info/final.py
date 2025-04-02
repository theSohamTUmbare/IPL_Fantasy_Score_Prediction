import pandas as pd

# Load the original dataset
original_file = "updated_matches_info1.csv"  # Change to your actual filename
df_original = pd.read_csv(original_file)

# Load the new dataset with correct coordinates
updated_venues_file = "updated_unique_venues_with_coordinates.csv"  # Change to your actual filename
df_updated = pd.read_csv(updated_venues_file)

# Merge the data based on venue_name and city to update venue_long and venue_lat
df_original = df_original.merge(
    df_updated[['venue_name', 'city', 'venue_lat', 'venue_long']], 
    on=['venue_name', 'city'], 
    how='left', 
    suffixes=('', '_new')
)

# Replace old values only where they were originally 0.0
df_original['venue_lat'] = df_original['venue_lat'].where(df_original['venue_lat'] != 0.0, df_original['venue_lat_new'])
df_original['venue_long'] = df_original['venue_long'].where(df_original['venue_long'] != 0.0, df_original['venue_long_new'])

# Drop extra columns after merging
df_original.drop(columns=['venue_lat_new', 'venue_long_new'], inplace=True)

# Save the updated CSV file
output_file = "updated_original_matches_final.csv"
df_original.to_csv(output_file, index=False)

print(f"Updated CSV file saved successfully: {output_file}")
