import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import time

# Load match data
matches_df = pd.read_csv("updated_original_matches_final.csv")

def log_progress(current, total):
    print(f"Processing match {current}/{total} ({(current/total)*100:.2f}%)")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Weather API URL
url = "https://archive-api.open-meteo.com/v1/archive"

# List to store weather data
weather_data = []

total_matches = len(matches_df)
load = False


for index, row in matches_df.iterrows():
    log_progress(index + 1, total_matches)
    match_id = row["match_id"]
    latitude = row["venue_lat"]
    longitude = row["venue_long"]
    match_date = row["match_date"]
    match_time = row["match_time"]

    # Skip rows with missing lat/lon
    if pd.isna(latitude) or pd.isna(longitude):
        continue

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": match_date,
        "end_date": match_date,
        "daily": "apparent_temperature_mean",
        
        "hourly": ["apparent_temperature", "relative_humidity_2m", "dew_point_2m", "precipitation"],
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Process daily data
        daily = response.Daily()
        daily_apparent_temperature_mean = daily.Variables(0).ValuesAsNumpy()[0]

        # Process hourly data
        hourly = response.Hourly()
        hourly_apparent_temperature = hourly.Variables(0).ValuesAsNumpy().mean()
        hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy().mean()
        hourly_precipitation = hourly.Variables(2).ValuesAsNumpy().sum()
        hourly_temperature_2m_spread = hourly.Variables(4).ValuesAsNumpy().mean()
        hourly_temperature_2m = hourly.Variables(5).ValuesAsNumpy().mean()

        weather_data.append([
            match_id, match_date, latitude, longitude, daily_apparent_temperature_mean,
            hourly_relative_humidity_2m, hourly_apparent_temperature,
            hourly_precipitation, hourly_is_day, hourly_temperature_2m_spread,
            hourly_temperature_2m
        ])
        
        # Delay to avoid hitting API limits
        time.sleep(1)
    except Exception as e:
        print(f"Error fetching data for match {match_id}: {e}")

# Convert to DataFrame and save
weather_df = pd.DataFrame(weather_data, columns=[
    "match_id", "match_date", "latitude", "longitude", "daily_apparent_temperature_mean",
    "hourly_relative_humidity_2m", "hourly_apparent_temperature",
    "hourly_precipitation", "hourly_is_day", "hourly_temperature_2m_spread",
    "hourly_temperature_2m"
])

weather_df.to_csv("weather.csv", index=False)
print("Weather data saved to weather.csv")


