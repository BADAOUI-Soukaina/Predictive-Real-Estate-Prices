import pandas as pd
import requests
import time
import os 
import sys 

# ----------------------------------------------------------------------
# 1. PARAMÈTRES ET CONFIGURATION
# ----------------------------------------------------------------------

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# Le chemin d'accès au fichier Excel
FILE_PATH = 'dataset_geocodes_arcgis_et_enrichi.xlsx' 


# Noms des colonnes attendues pour les coordonnées et l'identifiant
COL_LAT = 'lat'
COL_LON = 'lon'
COL_QUARTIER = 'quartier_key' 

# Types de POI à rechercher et leurs tags OpenStreetMap correspondants
POI_TAGS = {
    'nb_ecoles': 'amenity=school',
    'nb_hopitaux': 'amenity=hospital',
    'nb_pharmacies': 'amenity=pharmacy',
    'nb_mosquees': 'amenity=place_of_worship',
    'nb_banques': 'amenity=bank',
    'nb_centres_commerciaux': 'shop=mall',
}

RADIUS = 1500 
DELAY_SECONDS = 3 

# ----------------------------------------------------------------------
# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES
# ----------------------------------------------------------------------

try:
    df = pd.read_excel(FILE_PATH)
except FileNotFoundError:
    print(f"ERREUR : Le fichier spécifié ({FILE_PATH}) est introuvable. Veuillez vérifier le chemin.")
    sys.exit(1)
except Exception as e:
    print(f"ERREUR : Impossible de lire le fichier Excel. Problème : {e}")
    sys.exit(1)

# Nettoyer les noms des colonnes 
df.columns = df.columns.str.strip()
print("Noms des colonnes nettoyés.")

# Convertir les coordonnées en numérique et gérer les valeurs invalides (NaN)
df[COL_LAT] = pd.to_numeric(df[COL_LAT], errors='coerce')
df[COL_LON] = pd.to_numeric(df[COL_LON], errors='coerce')

# Vérification de l'existence des colonnes nécessaires
if COL_LAT not in df.columns or COL_LON not in df.columns:
    print("-" * 70)
    print(f"ERREUR FATALE : Colonnes de coordonnées non trouvées.")
    print(f"Attendu: '{COL_LAT}' et '{COL_LON}'. Trouvé: {list(df.columns)}")
    sys.exit(1)

print(f"Fichier '{FILE_PATH}' chargé avec succès.")
print(f"Nombre de lignes (quartiers) à traiter : {len(df)}")
nombre_requetes_total = len(df) * len(POI_TAGS)
temps_estime = (nombre_requetes_total * DELAY_SECONDS) / 60
print(f"Temps de traitement estimé : environ {temps_estime:.1f} minutes.")
print("-" * 70)

# ----------------------------------------------------------------------
# 3. FONCTION DE RECHERCHE OVERPASS (LOGIQUE D'EXTRACTION CORRIGÉE)
# ----------------------------------------------------------------------

def get_poi_count_overpass(lat, lon, tag):
    """
    Construit la requête Overpass et retourne le nombre d'éléments trouvés.
    """
    # Force la conversion en chaîne pour éviter les problèmes de formatage de float
    lat_str = str(lat)
    lon_str = str(lon)
    
    query = f"""
    [out:json];
    (
      node(around:{RADIUS},{lat_str},{lon_str})[{tag}];
      way(around:{RADIUS},{lat_str},{lon_str})[{tag}]; 
    );
    out count;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=30)
        response.raise_for_status() 
        data = response.json()
        
        if data and 'elements' in data and data['elements']:
            count_element = data['elements'][0]
            
            # CORRECTION : Accéder à 'tags' puis à 'total' pour obtenir le compte
            if (count_element['type'] == 'count' and 
                'tags' in count_element and 
                'total' in count_element['tags']):
                
                # Convertir la chaîne de caractères 'total' en nombre entier
                return int(count_element['tags']['total'])
        
        # Ce message s'affiche uniquement si la requête réussit mais le compte n'est pas trouvé
        # Cela devrait maintenant être très rare, sauf si le compte est réellement 0.
        # print(f"--- ATTENTION DEBOGAGE PARSING ÉCHOUÉ ({lat_str}, {lon_str}) : {data}")
        return 0
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print(f"\nAVERTISSEMENT: Serveur Overpass surchargé (Erreur 429). Augmentez DELAY_SECONDS.")
            time.sleep(DELAY_SECONDS * 5)
        return 0
    except requests.exceptions.RequestException as e:
        # Capture les erreurs de connexion, de timeout, etc.
        print(f"\nAVERTISSEMENT: Erreur de connexion/requête pour ({lat_str}, {lon_str}): {e}")
        return 0
    except Exception as e:
        print(f"\nAVERTISSEMENT: Erreur inattendue pour ({lat_str}, {lon_str}): {e}")
        return 0

# ----------------------------------------------------------------------
# 4. EXÉCUTION DE L'EXTRACTION ET ENRICHISSEMENT
# ----------------------------------------------------------------------

# Initialisation des nouvelles colonnes
for col_name in POI_TAGS.keys():
    df[col_name] = 0 

for index, row in df.iterrows():
    
    quartier = row.get(COL_QUARTIER, f'Ligne {index + 1}')

    # Sauter les lignes où les coordonnées sont NaN (invalides)
    if pd.isna(row[COL_LAT]) or pd.isna(row[COL_LON]):
        print(f"-> Traitement : {quartier} ({index + 1}/{len(df)}) - IGNORÉ (Coordonnées manquantes/invalides)")
        continue 
        
    lat = row[COL_LAT]
    lon = row[COL_LON]
    
    print(f"-> Traitement : {quartier} ({index + 1}/{len(df)})")
    
    for col_name, tag in POI_TAGS.items():
        count = get_poi_count_overpass(lat, lon, tag)
        df.loc[index, col_name] = count
        
        time.sleep(DELAY_SECONDS) 

# ----------------------------------------------------------------------
# 5. SAUVEGARDE DES RÉSULTATS
# ----------------------------------------------------------------------

print("-" * 70)
print("FIN DU TRAITEMENT.")

# Sauvegarder le résultat dans un nouveau fichier Excel
df.to_excel('dataset_enrichi_comodites.xlsx', index=False)
print("\nFichier sauvegardé avec succès sous 'dataset_enrichi_comodites.xlsx'.")