import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

matches_df = pd.read_csv("new.csv")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://archive-api.open-meteo.com/v1/archive"

def log_progress(current, total):
    print(f"Processing match {current}/{total} ({(current/total)*100:.2f}%)")

# Iterate through matches dataframe
for index, row in matches_df.iterrows():
    log_progress(index + 1, len(matches_df))
    match_id = row["match_id"]
    latitude = row["venue_lat"]
    longitude = row["venue_long"]
    match_date = row["match_date"]
    match_time = row["match_time"]
    
    # Generate start and end times for the next 5 hours
    start_datetime = pd.to_datetime(f"{match_date} {match_time}")
    end_datetime = start_datetime + pd.DateOffset(hours=5)
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_datetime.strftime("%Y-%m-%d"),
        "end_date": end_datetime.strftime("%Y-%m-%d"),
        "start_time": start_datetime.strftime("%H:%M"),
        "end_time": end_datetime.strftime("%H:%M"),
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
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
    }
    
    hourly_data["precipitation"] = hourly.Variables(0).ValuesAsNumpy()
    hourly_data["temperature_2m"] = hourly.Variables(2).ValuesAsNumpy()
    hourly_data["relative_humidity_2m"] = hourly.Variables(3).ValuesAsNumpy()
    hourly_data["dew_point_2m"] = hourly.Variables(4).ValuesAsNumpy()
    hourly_data["rain"] = hourly.Variables(5).ValuesAsNumpy()
    hourly_data["wind_speed_100m"] = hourly.Variables(6).ValuesAsNumpy()
    
    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print(hourly_dataframe)

    # Define the CSV file name for each match
csv_filename = f"weather_test.csv"

# Save the DataFrame to CSV
hourly_dataframe.to_csv(csv_filename, index=False)

print(f"Saved data to {csv_filename}")
