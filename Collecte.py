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


# ============================================================
# PARAMÈTRES
# ============================================================

# Nombre de jours à analyser
NB_JOURS = 3

# Probabilité de pluie minimale
# IMPORTANT : > 50 %, donc 50 % exactement n'est PAS retenu
SEUIL_PLUIE = 50

# Chute de température minimale
# IMPORTANT : > 5 °C, donc -5 °C exactement n'est PAS retenu
SEUIL_BAISSE_TEMPERATURE = 5


# ============================================================
# DATE / HEURE DE LA REQUÊTE
# ============================================================

request_time = datetime.now() + timedelta(hours=2)
today = request_time.date()


# ============================================================
# LISTE DES RÉSULTATS
# ============================================================

results = []


# ============================================================
# TRAITEMENT DES STATIONS
# ============================================================

for station_name, lat, lon, api_key, units in stations:

    print()
    print("=" * 60)
    print(f"=== {station_name} ===")
    print("=" * 60)

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
        # APPEL API
        # --------------------------------------------------------

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()


        # --------------------------------------------------------
        # RÉCUPÉRATION DES DONNÉES
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
        # CONSTRUCTION DES DONNÉES HORAIRES
        # --------------------------------------------------------

        hourly_data = []

        for i in range(len(times)):

            dt = datetime.fromisoformat(
                times[i]
            )

            # On garde uniquement les 3 prochains jours
            if (
                today
                <= dt.date()
                <= today + timedelta(days=NB_JOURS - 1)
            ):

                hourly_data.append({
                    "datetime": dt,
                    "temperature": temperatures[i],
                    "precipChance": precip_chances[i],
                    "precipType": precip_types[i],
                    "qpfRain": qpf_rain[i]
                })


        # --------------------------------------------------------
        # TRI CHRONOLOGIQUE
        # --------------------------------------------------------

        hourly_data.sort(
            key=lambda x: x["datetime"]
        )


        # --------------------------------------------------------
        # ANALYSE DES HEURES
        # --------------------------------------------------------

        previous_temperature = None
        previous_datetime = None

        for item in hourly_data:

            dt = item["datetime"]
            temperature = item["temperature"]

            precip_chance = item["precipChance"]
            precip_type = item["precipType"]
            rain_amount = item["qpfRain"]


            # ====================================================
            # 1. PLUIE > 50 %
            # ====================================================

            pluie = (
                precip_chance is not None
                and precip_chance > SEUIL_PLUIE
            )


            # ====================================================
            # 2. CHUTE DE TEMPÉRATURE > 5 °C EN 1 HEURE
            # ====================================================

            temperature_previous = None
            variation_temperature = None
            chute_temperature = False


            # On ne compare que si l'heure précédente
            # est exactement une heure avant
            if (
                previous_temperature is not None
                and previous_datetime is not None
                and dt - previous_datetime == timedelta(hours=1)
            ):

                temperature_previous = previous_temperature

                variation_temperature = (
                    temperature
                    - previous_temperature
                )

                # Exemple :
                #
                # 20°C -> 14°C
                # variation = -6°C
                # -6 < -5 => TRUE
                #
                if (
                    variation_temperature
                    < -SEUIL_BAISSE_TEMPERATURE
                ):

                    chute_temperature = True


            # ====================================================
            # 3. CONSERVATION UNIQUEMENT DES ÉVÉNEMENTS
            # ====================================================

            if pluie or chute_temperature:

                jour = (
                    f"J+{(dt.date() - today).days}"
                )


                # ------------------------------------------------
                # CRÉATION DE LA LIGNE CSV
                # ------------------------------------------------

                result = {

                    "Station": station_name,

                    "Heure_requete": request_time.strftime(
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

                    "Temperature_precedente":
                        temperature_previous,

                    "Variation_temperature":
                        variation_temperature,

                    "Chute_temperature":
                        "OUI"
                        if chute_temperature
                        else "NON",

                    "Probabilite_pluie":
                        precip_chance,

                    "Type_precipitation":
                        precip_type,

                    "Pluie_mm":
                        rain_amount,

                    "Pluie_sup_50":
                        "OUI"
                        if pluie
                        else "NON"
                }


                results.append(result)


                # ------------------------------------------------
                # AFFICHAGE CONSOLE
                # ------------------------------------------------

                if pluie:

                    print(
                        f"🌧 {dt.strftime('%Y-%m-%d %H:%M')} "
                        f"| {precip_chance}% "
                        f"| Temp : {temperature}°C "
                        f"| Pluie : {rain_amount}"
                    )


                if chute_temperature:

                    print(
                        f"🌡️ BAISSE "
                        f"{dt.strftime('%Y-%m-%d %H:%M')} "
                        f"| "
                        f"{temperature_previous}°C → "
                        f"{temperature}°C "
                        f"| "
                        f"{variation_temperature:+.1f}°C"
                    )


            # ----------------------------------------------------
            # MÉMORISATION POUR L'HEURE SUIVANTE
            # ----------------------------------------------------

            previous_temperature = temperature
            previous_datetime = dt


    # ============================================================
    # GESTION DES ERREURS
    # ============================================================

    except requests.RequestException as e:

        print(
            f"Erreur API pour {station_name} : {e}"
        )

    except (KeyError, ValueError) as e:

        print(
            f"Erreur dans les données de "
            f"{station_name} : {e}"
        )


# ============================================================
# ÉCRITURE DU CSV
# ============================================================

csv_file = "alertes_meteo_3jours.csv"

file_exists = os.path.isfile(
    csv_file
)


fieldnames = [
    "Station",
    "Heure_requete",
    "Jour",
    "Date",
    "Heure",
    "Temperature",
    "Temperature_precedente",
    "Variation_temperature",
    "Chute_temperature",
    "Probabilite_pluie",
    "Type_precipitation",
    "Pluie_mm",
    "Pluie_sup_50"
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

    # En-tête uniquement lors de la création
    # du fichier
    if not file_exists:
        writer.writeheader()

    writer.writerows(results)


# ============================================================
# FIN
# ============================================================

print()
print("=" * 60)
print(
    f"Terminé : {len(results)} lignes ajoutées."
)
print(
    f"Fichier : {csv_file}"
)
print("=" * 60)
