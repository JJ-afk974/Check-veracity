import requests
import csv
from datetime import datetime, timedelta
from collections import defaultdict

# Liste des stations : nom, latitude, longitude, apiKey
stations = [
    ("Paris", 48.986, 2.449, "e1f10a1e78da46f5b10a1e78da96f525"),
    ("Londres", 51.51, 0.028, "e1f10a1e78da46f5b10a1e78da96f525"),
    ("Tokyo", 35.55, 139.784, "e1f10a1e78da46f5b10a1e78da96f525"),
    ("Seoul", 37.4943, 126.4905, "e1f10a1e78da46f5b10a1e78da96f525"),
    ("New York", 40.761, -73.864, "e1f10a1e78da46f5b10a1e78da96f525"),
    ("Miami", 25.848, -80.242, "e1f10a1e78da46f5b10a1e78da96f525"),
]

today = datetime.now().date()

# Liste qui contiendra les résultats pour le CSV
results = []

for station_name, lat, lon, api_key in stations:
    url = (
        "https://api.weather.com/v3/wx/forecast/hourly/15day"
        f"?apiKey={api_key}"
        f"&geocode={lat},{lon}"
        "&units=m&language=en-US&format=json"
    )

    try:
        # Date et heure de la requête
        request_time = datetime.now()

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

# Enregistrement dans un fichier CSV
csv_file = "temperatures_3jours.csv"

with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
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
    writer.writeheader()
    writer.writerows(results)

print(f"\\nLes résultats ont été enregistrés dans : {csv_file}")
