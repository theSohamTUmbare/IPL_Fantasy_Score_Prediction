import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup Open-Meteo API client with caching and retry
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
url = "https://archive-api.open-meteo.com/v1/archive"

def get_weather_data(latitude, longitude, match_date, match_time):
    if pd.isna(latitude) or pd.isna(longitude):
        raise ValueError("Latitude or Longitude is missing.")
    if pd.isna(match_date) or pd.isna(match_time):
        raise ValueError("Match date or time is missing.")

    start_datetime = pd.to_datetime(f"{match_date} {match_time}")
    end_datetime = start_datetime + pd.DateOffset(hours=5)
    rounded_time = start_datetime.round('h')
    start_hour_int = rounded_time.hour
    end_hour_int = start_hour_int + 5

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_datetime.strftime("%Y-%m-%d"),
        "end_date": end_datetime.strftime("%Y-%m-%d"),
        "hourly": [
            "precipitation", "temperature_2m_spread", "temperature_2m", 
            "relative_humidity_2m", "dew_point_2m", "rain", "wind_speed_100m"
        ]
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()

    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "precipitation": hourly.Variables(0).ValuesAsNumpy(),
        "temperature_2m": hourly.Variables(2).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(3).ValuesAsNumpy(),
        "dew_point_2m": hourly.Variables(4).ValuesAsNumpy(),
        "rain": hourly.Variables(5).ValuesAsNumpy(),
        "wind_speed_100m": hourly.Variables(6).ValuesAsNumpy()
    }

    result = {
        "precipitation": hourly_data["precipitation"][start_hour_int:end_hour_int].mean(),
        "temperature_2m": hourly_data["temperature_2m"][start_hour_int:end_hour_int].mean(),
        "relative_humidity_2m": hourly_data["relative_humidity_2m"][start_hour_int:end_hour_int].mean(),
        "dew_point_2m": hourly_data["dew_point_2m"][start_hour_int:end_hour_int].mean(),
        "rain": hourly_data["rain"][start_hour_int:end_hour_int].mean(),
        "wind_speed_100m": hourly_data["wind_speed_100m"][start_hour_int:end_hour_int].mean()
    }

    return result

if __name__ == "__main__":
    result = get_weather_data(
        latitude=28.6139,
        longitude=77.2090,
        match_date="2023-04-10",
        match_time="16:00"
    )
    print(result)
