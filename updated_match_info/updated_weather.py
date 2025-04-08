import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import os
matches_df = pd.read_csv(r"updated_match_info\updated_matches_info3.csv")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"

def log_progress(current, total):
    print(f"Processing match {current}/{total} ({(current/total)*100:.2f}%)")

no_match_time_data = []
no_match_date_data = []
no_lat_long_data = []
# Iterate through matches dataframe
# matches_data = []
output_csv = "updated_match_info\\weather_data.csv"

# If file exists, load it to avoid repeating work
if os.path.exists(output_csv):
    processed_df = pd.read_csv(output_csv)
    processed_match_ids = set(processed_df["match_id"].astype(str))
    matches_data = processed_df.to_dict(orient='records')
    print(f"Resuming from previous run. {len(processed_match_ids)} matches already processed.")
else:
    processed_match_ids = set()
    matches_data = []
    
match_ids = ['811111','811117','811123','1068308','1068327','1068409','1127465','693111','804553','804599','947107','947219','543883','543884', '543885']
# match_ids = []

for index, row in matches_df.iterrows():
    # if str(row["match_id"]) in processed_match_ids:
    #     continue  # skip already processed
    if str(row['match_id']) not in match_ids:
        continue
    log_progress(index + 1, len(matches_df))
    match_id = row["match_id"]
    latitude = row["venue_lat"]
    longitude = row["venue_long"]
    match_date = row["match_date"]
    match_time = row["match_time"]
    print(match_id)
    if pd.isna(latitude) or pd.isna(longitude):
        print(f"Skipping match {match_id} due to missing lat/long")
        no_lat_long_data.append(match_id)
        continue
    if pd.isna(match_time):
        print(f"Skipping match {match_id} due to time")
        no_match_time_data.append(match_id)
        continue
    if pd.isna(match_date):
        print(f"Skipping match {match_id} due to date")
        no_match_date_data.append(match_id)
        continue
    start_datetime = pd.to_datetime(f"{match_date} {match_time}")
    end_datetime = start_datetime + pd.DateOffset(hours=5)

    # adjusted_time = start_datetime - pd.Timedelta(hours=5, minutes=30)

    # Round to the nearest hour
    rounded_time = start_datetime.round('h')
    print(match_time)
    # Extract the hour integer
    start_hour_int = rounded_time.hour
    end_hour_int = start_hour_int + 5
    print(start_hour_int)
    # print(start_hour_int)
    # break
    # break
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_datetime.strftime("%Y-%m-%d"),
        "end_date": end_datetime.strftime("%Y-%m-%d"),
        # "start_time": start_datetime.strftime("%H:%M"),
        # "end_time": end_datetime.strftime("%H:%M"),
        # "timezone": "Asia/Kolkata",
        "hourly": [
            "precipitation", "temperature_2m_spread", "temperature_2m", 
            "relative_humidity_2m", "dew_point_2m", "rain", "wind_speed_100m"
        ]
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")
    
    # Process hourly data for the next 5 hours
    hourly = response.Hourly()
    # print(hourly.Interval())
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
    }
    # print(hourly_data['date'])
    # exit()
    hourly_data["precipitation"] = hourly.Variables(0).ValuesAsNumpy()
    
    # print(hourly_data['precipitation'])
    # break
    # print(hourly_data['precipitation'])
    hourly_data["temperature_2m"] = hourly.Variables(2).ValuesAsNumpy()
    
    hourly_data["relative_humidity_2m"] = hourly.Variables(3).ValuesAsNumpy()

    hourly_data["dew_point_2m"] = hourly.Variables(4).ValuesAsNumpy()

    hourly_data["rain"] = hourly.Variables(5).ValuesAsNumpy()

    hourly_data["wind_speed_100m"] = hourly.Variables(6).ValuesAsNumpy()
    
    match_data = {
        "match_id": match_id,
        "precipitation": hourly_data["precipitation"][start_hour_int: end_hour_int].mean(),
        "temperature_2m": hourly_data["temperature_2m"][start_hour_int: end_hour_int].mean(),
        "relative_humidity_2m": hourly_data["relative_humidity_2m"][start_hour_int: end_hour_int].mean(),
        "dew_point_2m": hourly_data["dew_point_2m"][start_hour_int: end_hour_int].mean(),
        "rain": hourly_data["rain"][start_hour_int: end_hour_int].mean(),
        "wind_speed_100m": hourly_data["wind_speed_100m"][start_hour_int: end_hour_int].mean()
    }
    matches_data.append(match_data)

    # Save every 50 entries
    if len(matches_data) % 50 == 0:
        print(f"Saving progress at {len(matches_data)} matches...")
        pd.DataFrame(matches_data).to_csv(output_csv, index=False)

    # Save any remaining data after loop

pd.DataFrame(matches_data).to_csv(output_csv, index=False)
print("Final data saved.")
print(no_match_time_data)
print(no_match_date_data)
print(no_lat_long_data)

# Save the DataFrame to CSV
# hourly_dataframe.to_csv(csv_filename, index=False)

print("Saved data to csv")
