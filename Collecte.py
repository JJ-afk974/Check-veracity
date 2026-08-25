import requests
import csv
import os
from datetime import datetime, timedelta


# ============================================================
# CONFIGURATION
# ============================================================

stations = [
    ("Paris", 48.986, 2.449, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Londres", 51.51, 0.028, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Madrid", 40.452, -3.584, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Milan", 45.626, 8.696, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Munich", 48.354, 11.792, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Amsterdam", 52.31, 4.765, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Varsovie", 52.169, 20.979, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
    ("Helsinski", 60.317, 24.967, "e1f10a1e78da46f5b10a1e78da96f525", "m"),
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
    ("Atlanta", 33.639, -84.405, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
    ("San Francisco", 37.616, -122.389, "e1f10a1e78da46f5b10a1e78da96f525", "e"),
]


# Nombre de jours de prévisions à conserver
NB_JOURS = 3

# Seuil de chute de température
SEUIL_BAISSE = 5


# ============================================================
# DATE DU JOUR
# ============================================================

now = datetime.now() + timedelta(hours=2)
today = now.date()


# ============================================================
# LISTE DES RÉSULTATS
# ============================================================

results = []


# ============================================================
# TRAITEMENT DES STATIONS
# ============================================================

for station_name, lat, lon, api_key, units in stations:

    print(f"\n{'=' * 60}")
    print(f"Traitement de {station_name}")
    print(f"{'=' * 60}")

    url = (
        "https://api.weather.com/v3/wx/forecast/hourly/15day"
        f"?apiKey={api_key}"
        f"&geocode={lat},{lon}"
        f"&units={units}"
        f"&language=en-US"
        f"&format=json"
    )

    try:

        # --------------------------------------------------------
        # Appel API
        # --------------------------------------------------------

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()


        # --------------------------------------------------------
        # Récupération des données
        # --------------------------------------------------------

        times = data["validTimeLocal"]
        temperatures = data["temperature"]

        precip_chances = data.get(
            "precipChance",
            [None] * len(times)
        )

        precip_types = data.get(
            "precipType",
            [None] * len(times)
        )

        qpf_rain = data.get(
            "qpfRain",
            [None] * len(times)
        )


        # --------------------------------------------------------
        # Construction des données horaires
        # --------------------------------------------------------

        hourly_data = []

        for i in range(len(times)):

            dt = datetime.fromisoformat(times[i])

            # On conserve uniquement les 3 prochains jours
            if today <= dt.date() <= today + timedelta(days=NB_JOURS - 1):

                hourly_data.append({
                    "datetime": dt,
                    "temperature": temperatures[i],
                    "precipChance": precip_chances[i],
                    "precipType": precip_types[i],
                    "qpfRain": qpf_rain[i]
                })


        # --------------------------------------------------------
        # Tri chronologique
        # --------------------------------------------------------

        hourly_data.sort(
            key=lambda x: x["datetime"]
        )


        # --------------------------------------------------------
        # Calcul des informations supplémentaires
        # --------------------------------------------------------

        previous_temperature = None
        previous_datetime = None


        for item in hourly_data:

            dt = item["datetime"]
            temperature = item["temperature"]


            # ----------------------------------------------------
            # Jour relatif
            # ----------------------------------------------------

            day_offset = (dt.date() - today).days
            jour = f"J+{day_offset}"


            # ----------------------------------------------------
            # Informations pluie
            # ----------------------------------------------------

            precip_chance = item["precipChance"]
            precip_type = item["precipType"]
            rain_amount = item["qpfRain"]


            # Détection de pluie
            #
            # On considère qu'il y a de la pluie si :
            # - precipType == "rain"
            # OU
            # - une quantité de pluie > 0 est prévue
            # ----------------------------------------------------

            pluie_prevue = (
                precip_type == "rain"
                or (
                    rain_amount is not None
                    and rain_amount > 0
                )
            )


            # ----------------------------------------------------
            # Variation de température
            # ----------------------------------------------------

            temperature_previous = None
            variation_temperature = None
            chute_plus_5 = False


            # On ne compare que deux heures consécutives
            if (
                previous_temperature is not None
                and previous_datetime is not None
                and dt - previous_datetime == timedelta(hours=1)
            ):

                temperature_previous = previous_temperature

                variation_temperature = (
                    temperature - previous_temperature
                )

                # Exemple :
                # 20°C -> 14°C = -6°C
                #
                # Donc chute_plus_5 = True
                if variation_temperature < -SEUIL_BAISSE:
                    chute_plus_5 = True


            # ----------------------------------------------------
            # Affichage console des événements intéressants
            # ----------------------------------------------------

            if pluie_prevue:

                print(
                    f"  🌧 {dt.strftime('%Y-%m-%d %H:%M')} "
                    f"| {temperature}°C "
                    f"| pluie {precip_chance}% "
                    f"| {rain_amount}"
                )


            if chute_plus_5:

                print(
                    f"  🌡️ BAISSE TEMPÉRATURE "
                    f"{previous_temperature}°C → {temperature}°C "
                    f"à {dt.strftime('%Y-%m-%d %H:%M')} "
                    f"({variation_temperature:+.1f}°C)"
                )


            # ----------------------------------------------------
            # Ajout au CSV
            # ----------------------------------------------------

            results.append({

                "Station": station_name,

                "Heure_requete": now.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "Jour": jour,

                "Date": dt.strftime(
                    "%Y-%m-%d"
                ),

                "Heure": dt.strftime(
                    "%H:%M"
                ),

                "Temperature": temperature,

                "Temperature_precedente": temperature_previous,

                "Variation_temperature": variation_temperature,

                "Chute_plus_5C": "OUI"
                    if chute_plus_5
                    else "NON",

                "Precipitation_probabilite": precip_chance,

                "Precipitation_type": precip_type,

                "Pluie_mm": rain_amount,

                "Pluie_prevue": "OUI"
                    if pluie_prevue
                    else "NON"
            })


            # ----------------------------------------------------
            # Mémorisation pour l'heure suivante
            # ----------------------------------------------------

            previous_temperature = temperature
            previous_datetime = dt


    except requests.RequestException as e:

        print(
            f"Erreur lors de l'appel API pour "
            f"{station_name} : {e}"
        )


    except (KeyError, ValueError) as e:

        print(
            f"Erreur dans les données reçues pour "
            f"{station_name} : {e}"
        )


# ============================================================
# ÉCRITURE DU CSV
# ============================================================

csv_file = "previsions_horaires_3jours.csv"

file_exists = os.path.isfile(csv_file)


fieldnames = [
    "Station",
    "Heure_requete",
    "Jour",
    "Date",
    "Heure",
    "Temperature",
    "Temperature_precedente",
    "Variation_temperature",
    "Chute_plus_5C",
    "Precipitation_probabilite",
    "Precipitation_type",
    "Pluie_mm",
    "Pluie_prevue"
]


with open(
    csv_file,
    mode="a",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    # Écriture de l'en-tête uniquement
    # si le fichier n'existe pas encore
    if not file_exists:
        writer.writeheader()

    writer.writerows(results)


# ============================================================
# FIN
# ============================================================

print(
    f"\nLes prévisions horaires ont été ajoutées dans : "
    f"{csv_file}"
)

print(
    f"Nombre de lignes ajoutées : {len(results)}"
)
