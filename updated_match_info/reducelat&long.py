import pandas as pd

df = pd.read_csv("updated_matches_info2.csv")
df_cleaned = df[(df['venue_long'] != 0) | (df['venue_lat'] != 0)]

df_cleaned = df_cleaned.drop_duplicates(subset=['venue_long', 'venue_lat'])

df_cleaned.to_csv("cleaned_dataset.csv", index=False)

print("Rows with venue_long and venue_lat as 0 removed successfully, and duplicates dropped.")
