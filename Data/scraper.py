import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import numpy as np

# --- Configuration et variables globales ---
VILLES = ["fès", "casablanca", "rabat", "marrakech", "tanger", "agadir"] 
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

import datetime

def save_checkpoint(data, count, prefix="Mubawab_Backup"):
    """Sauvegarde le dataset partiel avec numéro de checkpoint ou timestamp."""
    if not data:
        return
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{count}_{ts}.csv"
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f" Backup sauvegardé : {filename} ({len(data)} lignes)")


def extract_details(soup, link):
    
    details = {
        'Prix': 'Nan', 'Type de Bien': 'Nan', 'Surface': 'Nan', 
        'Nombre de Pièces': 'Nan', 'Nombre de Chambres': 'Nan', 
        'Nombre de Salles de Bain': 'Nan', 'Étage': 'Nan', 
        'État': 'Nan', 'Quartier': 'Nan', 'Lien': link, 
        'Ville_Reelle': 'Nan',
        'Terrasse': 'Non', 'Garage': 'Non', 'Ascenseur': 'Non', 
        'Piscine': 'Non', 'Sécurité': 'Non',
    }

    # 1. Extraction du Prix
    v_prix = soup.find('h3', {"class": "orangeTit"})
    if v_prix:
        details['Prix'] = v_prix.text.strip().replace('\xa0', ' ')
        
    # 2. Localisation (Ville_Reelle et Quartier)
    loc_span = soup.find('span', {"class": "listingH3"})
    if loc_span:
        loc_text = loc_span.text.strip().replace('\n', ', ').replace('\t', '')
        parts = loc_text.split(",")
        details['Ville_Reelle'] = parts[-1].strip() if len(parts) > 0 else 'Nan'
        details['Quartier'] = parts[0].strip() if len(parts) > 1 else 'Nan'
    
    if details['Quartier'] == 'Nan' or details['Ville_Reelle'] == 'Nan':
        loc_h3 = soup.find('h3', {"class": "greyTit"})
        if loc_h3:
            loc_text_h3 = loc_h3.text.strip()
            match = re.search(r'(.+)\s+à\s+(.+)', loc_text_h3, re.IGNORECASE)
            if match:
                details['Quartier'] = match.group(1).strip()
                details['Ville_Reelle'] = match.group(2).strip()
            elif loc_text_h3:
                 parts = loc_text_h3.split(",")
                 details['Ville_Reelle'] = parts[-1].strip() if len(parts) > 0 else 'Nan'
                 details['Quartier'] = parts[0].strip() if len(parts) > 1 else 'Nan'


    # 3. Extraction des Features Détaillées (Type de Bien, État, Étage)
    feature_containers = soup.find_all('div', class_='adMainFeature col-4')
    for container in feature_containers:
        label_element = container.find('p', class_='adMainFeatureContentLabel')
        value_element = container.find('p', class_='adMainFeatureContentValue')
        
        if label_element and value_element:
            label = label_element.text.strip()
            value = value_element.text.strip()

            if label == "Type de bien": details['Type de Bien'] = value
            elif label == "Étage du bien": details['Étage'] = value
            elif label == "État": details['État'] = value
            
    # 4. Attributs Primaires (Surface, Pièces, SDB)
    attribute_features = soup.find_all('div', {"class": "adDetailFeature"})
    for feature_div in attribute_features:
        text = feature_div.text.strip()
        if "m²" in text:
            details['Surface'] = text.split('\n')[0].strip()
        elif "Pièce" in text:
            details['Nombre de Pièces'] = text.split('\n')[0].strip()
        elif "Chambre" in text:
            details['Nombre de Chambres'] = text.split('\n')[0].strip()
        elif "bain" in text:
            details['Nombre de Salles de Bain'] = text.split('\n')[0].strip()
            
    # 5. Caractéristiques Supplémentaires (Binaires) - LOGIQUE V11
    CARACS_BINAIRES = {
        'Terrasse': 'Terrasse', 'Garage': 'Garage', 'Ascenseur': 'Ascenseur', 
        'Piscine': 'Piscine', 'Sécurité': 'Sécurité', 
    }
    
    all_features_spans = soup.find_all('span', class_='fSize11 centered')
    
    for span in all_features_spans:
        t = span.text.strip()
        for keyword, detail_key in CARACS_BINAIRES.items():
            if keyword.lower() in t.lower():
                details[detail_key] = "Oui"

    return details


def scrape_mubawab_immo_v12():
    """Fonction principale de scraping qui gère la navigation et la sauvegarde."""
    start_time = time.time()
    all_data = []
    
    # Nouvelle limite de sécurité/forcée
    MAX_PAGES_FORCE = 250 
    MAX_PAGES_ABSOLUE = 1000 

    for ville in VILLES:
        liens = []
        base_url_list = f"https://www.mubawab.ma/fr/ct/{ville}/immobilier-a-vendre-all:p:1"

        print(f"\n--- Démarrage du scraping pour {ville.upper()} ---")

        # 1. Collecte des liens avec pagination
        try:
            page = requests.get(base_url_list, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(page.content, "html.parser")
            
            # Tente de trouver le nombre total de pages
            v_nb_de_pages = soup.find('p', {"class": "fSize11 centered"})
            nb_pages_estime = 1
            if v_nb_de_pages:
                # Cherche le nombre avant "pages" (ex: 178 pages)
                match = re.search(r'(\d+)(?=\s*pages)', v_nb_de_pages.text.strip())
                nb_pages_estime = int(match.group(1)) if match else 1
            
            # LOGIQUE V12: Utiliser le MAX_PAGES_FORCE comme valeur minimale de parcours.
            # On prend le minimum entre l'estimation, la limite absolue, et la limite forcée si l'estimation est trop basse.
            max_pages = max(nb_pages_estime, MAX_PAGES_FORCE)
            max_pages = min(max_pages, MAX_PAGES_ABSOLUE)
            
            print(f"Estimation des pages: {nb_pages_estime}. Forçage du scraping jusqu'à {max_pages} pages.")
            
            # Boucle à travers toutes les pages (1 à max_pages)
            # La boucle s'arrêtera d'elle-même quand elle atteindra une page vide (sans liens)
            for k in range(1, max_pages + 1):
                url_page = f"https://www.mubawab.ma/fr/ct/{ville}/immobilier-a-vendre-all:p:{k}"
                page = requests.get(url_page, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(page.content, "html.parser")
                
                # Récupère tous les liens d'annonces sur cette page
                var_de_annonce = soup.find_all('h2', {"class": "listingTit"})
                
                if not var_de_annonce:
                    # Si aucun lien n'est trouvé, cela signifie que nous avons atteint la dernière page
                    print(f"Arrêt de la pagination pour {ville} à la page {k-1} (page {k} vide).")
                    break 
                    
                for h2 in var_de_annonce:
                    a_tag = h2.find("a")
                    if a_tag and a_tag.attrs.get("href"):
                        lien_complet = a_tag.attrs["href"] if a_tag.attrs["href"].startswith("http") else "https://www.mubawab.ma" + a_tag.attrs["href"]
                        liens.append(lien_complet)
                
                time.sleep(0.5) # Pause entre les pages

            print(f"Total de {len(liens)} liens d'annonces collectés pour {ville}.")

        except Exception as e:
            print(f"Erreur lors de la collecte des liens pour {ville}: {e}")
            continue

        # 2. Extraction des détails de chaque annonce (Logique inchangée)
        for i, lien in enumerate(liens):
            try:
                page = requests.get(lien, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(page.content, "html.parser")
                
                details = extract_details(soup, lien)
                details['Ville_Boucle'] = ville
                all_data.append(details)
                
                if (i + 1) % 500 == 0:
                     print(f"  -> {i+1} annonces traitées pour {ville}")
                     save_checkpoint(all_data, i+1)

                time.sleep(0.5) # Pause entre les annonces

            except Exception as e:
                print(f"Erreur (détails) au lien n°{i+1} ({lien}): {e}. Annonce ignorée.")
                default_data = {
                    'Ville_Boucle': ville, 'Lien': lien, 'Prix': 'Nan', 'Type de Bien': 'Nan', 'Quartier': 'Nan',
                    'Surface': 'Nan', 'Nombre de Pièces': 'Nan', 'Nombre de Chambres': 'Nan', 
                    'Nombre de Salles de Bain': 'Nan', 'Étage': 'Nan', 'État': 'Nan',
                    'Terrasse': 'Non', 'Garage': 'Non', 'Ascenseur': 'Non', 'Piscine': 'Non', 'Sécurité': 'Non',
                }
                all_data.append(default_data)


    # 3. Finalisation du DataFrame (Logique inchangée)
    df = pd.DataFrame(all_data)
    
    df['Ville'] = df['Ville_Reelle'].apply(lambda x: x if x != 'Nan' and x is not None else np.nan)
    df['Ville'] = df['Ville'].fillna(df['Ville_Boucle'])
    df = df.drop(columns=['Ville_Reelle', 'Ville_Boucle', 'Lien'])
    
    colonnes_finales = [
        'Ville', 'Quartier', 'Prix', 'Type de Bien', 'Surface', 
        'Nombre de Pièces', 'Nombre de Chambres', 'Nombre de Salles de Bain', 
        'Étage', 'État', 
        'Terrasse', 'Garage', 'Ascenseur', 'Piscine', 'Sécurité'
    ]
    
    df = df.reindex(columns=colonnes_finales)

    df.to_csv("Mubawab_Vente_Data_scraped_FINAL.csv", index=False, encoding='utf-8-sig')
    
    end_time = time.time()
    print(f"\n Scraping terminé. Total de {len(df)} annonces enregistrées dans 'Mubawab_Vente_Data_scraped_FINAL.csv'.")
    print(f"Durée totale: {(end_time - start_time)/60:.2f} minutes.")
    
    return df

if __name__ == '__main__':
    data_scraped = scrape_mubawab_immo_v12()
    print("\nExtraction des premières lignes du DataFrame :")
    print(data_scraped.head())
