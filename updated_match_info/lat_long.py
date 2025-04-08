# import pandas as pd
# import requests
# import time

# # OpenCage API Key (Replace with your actual key)
# API_KEY = "050735998d7f455db15d3b3cad0881db"

# # Function to get coordinates from OpenCage API
# def get_coordinates(venue_name, city_name):
#     query = f"{venue_name}, {city_name}" if pd.notna(city_name) else venue_name
#     url = "https://api.opencagedata.com/geocode/v1/json"
#     params = {
#         "q": query,
#         "key": API_KEY,
#         "limit": 1
#     }
    
#     response = requests.get(url, params=params)
#     if response.status_code == 200:
#         data = response.json()
#         if data["results"]:
#             location = data["results"][0]["geometry"]
#             return location["lat"], location["lng"]
#     return None, None

# # Load dataset
# file_path = "updated_matches_info1.csv"
# df = pd.read_csv(file_path)

# # Identify missing coordinates
# total_missing = sum((df["venue_long"] == 0.0) & (df["venue_lat"] == 0.0))
# processed = 0

# print(f"Total missing venues: {total_missing}")

# for index, row in df.iterrows():
#     if row["venue_long"] == 0.0 and row["venue_lat"] == 0.0:
#         venue_name = row["venue"]
#         city_name = row["city"] if "city" in df.columns else ""
#         print(f"Fetching coordinates for: {venue_name}, {city_name} ...", end=" ")
        
#         lat, lon = get_coordinates(venue_name, city_name)
#         if lat is not None and lon is not None:
#             df.at[index, "venue_lat"] = lat
#             df.at[index, "venue_long"] = lon
#             print(f"Found -> Lat: {lat}, Lon: {lon}")
#         else:
#             print("Not found")
        
#         processed += 1
#         print(f"Progress: {processed}/{total_missing}")

#         time.sleep(1)  # Prevent hitting API limits

# # Save the updated data
# df.to_csv("updated_matches_info_with_coordinates.csv", index=False)
# print("Updated CSV file created successfully!")


import pandas as pd
import requests
import time

# Replace with your OpenCage API Key
API_KEY = "050735998d7f455db15d3b3cad0881db"

# Function to get coordinates from OpenCage API
def get_coordinates(venue_name, city_name):
    query = f"{venue_name}, {city_name}" if pd.notna(city_name) else venue_name
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": query,
        "key": API_KEY,
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        data = response.json()
        
        if data["results"]:
            location = data["results"][0]["geometry"]
            return location["lat"], location["lng"]
    except requests.RequestException as e:
        print(f"API Error: {e}")
    
    return None, None  # Return None if no data is found or API fails

# Load dataset
file_path = "unique_venues.csv"  # Ensure this file exists
df = pd.read_csv(file_path)

# Identify missing coordinates
missing_venues = (df["venue_lat"] == 0.0) & (df["venue_long"] == 0.0)
missing_venues.append(pd.isna(df['venue_lat']) & pd.isna(df['venue_long']))

total_missing = missing_venues.sum()

print(f"Total missing venues: {total_missing}")

processed = 0

for index, row in df[missing_venues].iterrows():
    venue_name = row["venue_name"]
    city_name = row["town_name"] if "town_name" in df.columns else ""

    print(f"Fetching coordinates for: {venue_name}, {city_name} ...", end=" ")

    lat, lon = get_coordinates(venue_name, city_name)
    if lat is not None and lon is not None:
        df.at[index, "venue_lat"] = lat
        df.at[index, "venue_long"] = lon
        print(f"Found -> Lat: {lat}, Lon: {lon}")
    else:
        print("Not found")

    processed += 1
    print(f"Progress: {processed}/{total_missing}")

    time.sleep(1.5)  # Delay to prevent hitting API rate limits

# Save the updated data
output_file = "updated_unique_venues_with_coordinates.csv"
df.to_csv(output_file, index=False)
print(f"Updated CSV file created successfully: {output_file}")
