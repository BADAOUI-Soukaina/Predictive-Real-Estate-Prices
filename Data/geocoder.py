import pandas as pd
import requests
import time
import urllib.parse

# ≡===============================
#  CONFIG
# ===============================
INPUT_FILE = "df_latest.csv"         
OUTPUT_FILE = "quartiers_geocodes.csv"
USER_AGENT = "MyGeocoderApp/1.0 (contact: marwasghir2004l@gmail.com)"


# ===============================
# 1. Fonction de normalisation
# ===============================
def normalize(text):
    if pd.isna(text):
        return ""
    return (
        str(text)
        .lower()
        .replace(" ", "-")
        .replace("é", "e")
        .replace("è", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ù", "u")
        .strip()
    )


# ===============================
# 2. Fonction de géocodage OSM
# ===============================
def geocode_osm(query):
    base_url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        time.sleep(1)  # anti-ban

        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                return lat, lon

    except Exception as e:
        print(f"Erreur pour {query}: {e}")

    return None, None


# ===============================
# 3. Chargement des données
# ===============================
print("📌 Chargement du dataset...")
df = pd.read_csv(INPUT_FILE, sep=";")

# liste unique des quartiers
df_q = df[["quartier_key"]].drop_duplicates().reset_index(drop=True)
df_q["lat"] = None
df_q["lon"] = None

print(f"📌 {len(df_q)} quartiers uniques à géocoder.")


# ===============================
# 4. Géocodage
# ===============================
for i, row in df_q.iterrows():

    key = row["quartier_key"].replace("_", " ")

    print(f"➡️ Géocodage : {key}  ({i+1}/{len(df_q)})")

    lat, lon = geocode_osm(key)

    df_q.at[i, "lat"] = lat
    df_q.at[i, "lon"] = lon

    print(f"   → lat/lon = {lat}, {lon}")

print("✔ Géocodage terminé.")


# ===============================
# 5. Sauvegarde
# ===============================
df_q.to_csv(OUTPUT_FILE, index=False)
print(f"📁 Résultats enregistrés dans : {OUTPUT_FILE}")
