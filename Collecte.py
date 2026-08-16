import requests
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Liste des stations : nom, latitude, longitude, apiKey
stations = [
    ("Paris", 48.986, 2.449, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Londres", 51.51, 0.028, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Tokyo", 35.55, 139.784, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Seoul", 37.4943, 126.4905, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("New York", 40.761, -73.864, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Miami", 25.848, -80.242, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Austin", 30.162, -97.689, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Dallas", 32.846, -96.87, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Denver", 39.705, -104.764, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Los Angeles", 33.96, -118.4, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Chicago", 41.977, -87.905, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Houston", 29.634, -95.246, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("Seattle", 47.441, -122.3, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("San Francisco", 37.616, -122.389, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
]

today = (datetime.now() + timedelta(hours=2)).date()

# Liste qui contiendra les résultats pour le CSV
results = []

for station_name, lat, lon, api_key, units in stations:
    url = (
        "https://api.weather.com/v3/wx/forecast/hourly/15day"
        f"?apiKey={api_key}"
        f"&geocode={lat},{lon}"
        f"&units={units}&language=en-US&format=json"
    )

    try:
        # Date et heure de la requête
        request_time = datetime.now() + timedelta(hours=2)

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        times = data["validTimeLocal"]
        temperatures = data["temperature"]

        temps_by_day = defaultdict(list)

        for time_str, temp in zip(times, temperatures):
            dt = datetime.fromisoformat(time_str)
            day = dt.date()

            if today <= day <= today + timedelta(days=2):
                temps_by_day[day].append(temp)

        print(f"\\n=== {station_name} ===")

        for offset in range(3):
            day = today + timedelta(days=offset)

            if day in temps_by_day:
                tmin = min(temps_by_day[day])
                tmax = max(temps_by_day[day])

                print(f"J+{offset} ({day}) : Tmin = {tmin}°C | Tmax = {tmax}°C")

                # Ajout des données pour le CSV
                results.append({
                    "Station": station_name,
                    "Heure_requete": request_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Jour": f"J+{offset}",
                    "Date": day.isoformat(),
                    "Tmin": tmin,
                    "Tmax": tmax
                })
            else:
                print(f"J+{offset} ({day}) : aucune donnée disponible")

    except requests.RequestException as e:
        print(f"\\n=== {station_name} ===")
        print(f"Erreur lors de l'appel API : {e}")

# Enregistrement dans un fichier CSV (ajout sans écraser)
csv_file = "temperatures_3jours.csv"

# Vérifie si le fichier existe déjà
file_exists = os.path.isfile(csv_file)

with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "Station",
            "Heure_requete",
            "Jour",
            "Date",
            "Tmin",
            "Tmax"
        ]
    )

    # Écrit l'en-tête uniquement si le fichier est nouveau
    if not file_exists:
        writer.writeheader()

    # Ajoute les nouvelles lignes à la fin du fichier
    writer.writerows(results)

print(f"\\nLes résultats ont été ajoutés dans : {csv_file}")
