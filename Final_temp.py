import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
UNITS = "m"  # "m" = Celsius, "e" = Fahrenheit

BASE_URL = "https://api.weather.com/v1/location/{location}/observations/historical.json"

# Villes à analyser
CITIES = {
    "New York": {
        "location": "KLGA:9:US",
        "timezone": "America/New_York",
    },
    "Londres": {
        "location": "EGLL:9:UK",
        "timezone": "Europe/London",
    },
    "Paris": {
        "location": "LFPG:9:FR",
        "timezone": "Europe/Paris",
    },
    "Miami": {
        "location": "KMIA:9:US",
        "timezone": "America/New_York",
    },
    "Tokyo": {
        "location": "RJTT:9:JP",
        "timezone": "Asia/Tokyo",
    },
    "Seoul": {
        "location": "RKSI:9:KR",
        "timezone": "Asia/Seoul",
    },
}

for city, config in CITIES.items():

    location = config["location"]
    tz = ZoneInfo(config["timezone"])

    # Date de la veille dans le fuseau horaire de la ville
    yesterday = datetime.now(tz).date() - timedelta(days=1)
    date_str = yesterday.strftime("%Y%m%d")

    url = (
        BASE_URL.format(location=location)
        + "?"
        + urllib.parse.urlencode({
            "apiKey": API_KEY,
            "units": UNITS,
            "startDate": date_str,
            "endDate": date_str,
        })
    )

    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))

        observations = data.get("observations", [])

        temperatures = []

        for obs in observations:

            temp = obs.get("temp")
            ts = obs.get("valid_time_gmt")

            if temp is None or ts is None:
                continue

            # UTC -> heure locale de la ville
            dt_local = datetime.fromtimestamp(
                ts,
                tz=timezone.utc
            ).astimezone(tz)

            # On garde uniquement les observations de la veille
            if dt_local.date() == yesterday:
                temperatures.append((temp, dt_local))

        if temperatures:

            # Maximum
            max_temp, max_time = max(
                temperatures,
                key=lambda x: x[0]
            )

            # Minimum
            min_temp, min_time = min(
                temperatures,
                key=lambda x: x[0]
            )

            print(f"\n{city}")
            print("-" * len(city))
            print(f"Date       : {yesterday}")
            print(f"Maximale   : {max_temp} °C à {max_time.strftime('%H:%M')}")
            print(f"Minimale   : {min_temp} °C à {min_time.strftime('%H:%M')}")

        else:
            print(f"\n{city} : aucune observation disponible")

    except Exception as e:
        print(f"\n{city} : ERREUR - {e}")
