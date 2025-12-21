import pandas as pd
import numpy as np
import re
from io import StringIO

# --- Configuration et variables ---
INPUT_FILENAME = "C:/Users/ELITEBOOK/Desktop/DevOps/Mubawab_Vente_Data_FINAL.csv" 
OUTPUT_FILENAME = "Mubawab_Vente_Data_FINAL_CLEANED.csv" 

def clean_data_ultra_robust(input_file, output_file):
    """
    Charge, nettoie et prépare le DataFrame Mubawab en conservant TOUTES les colonnes initiales.
    Effectue le nettoyage uniquement sur les colonnes spécifiées.
    """
    print(f"Tentative de chargement du fichier : {input_file}")
    
    try:
        # Essai de différents encodages et séparateurs
        encodings_to_try = [
            ('utf-8', None),
            ('latin-1', 'utf-8'),  # Lire en latin-1, puis décoder en utf-8
            ('iso-8859-1', 'utf-8'),
            ('cp1252', 'utf-8'),
            ('utf-8', 'latin-1')
        ]
        separators_to_try = [',', ';', '\t']
        df = None
        
        for encoding_pair in encodings_to_try:
            if isinstance(encoding_pair, tuple):
                read_encoding, decode_as = encoding_pair
            else:
                read_encoding, decode_as = encoding_pair, None
                
            for sep in separators_to_try:
                try:
                    # Méthode 1: Lecture directe
                    df = pd.read_csv(input_file, encoding=read_encoding, sep=sep, on_bad_lines='skip', low_memory=False)
                    
                    # Vérifier que le chargement a réussi (plus d'une colonne)
                    if len(df.columns) > 1:
                        print(f"✅ Chargement réussi avec encodage '{read_encoding}' et séparateur '{sep}' : {len(df)} lignes, {len(df.columns)} colonnes.")
                        
                        # Si un décodage spécial est nécessaire, corriger les colonnes et valeurs
                        if decode_as:
                            print(f"   Correction de l'encodage vers '{decode_as}'...")
                            # Corriger les noms de colonnes
                            df.columns = [col.encode(read_encoding).decode(decode_as, errors='ignore') if isinstance(col, str) else col for col in df.columns]
                            # Corriger les valeurs textuelles
                            for col in df.select_dtypes(include=['object']).columns:
                                df[col] = df[col].apply(lambda x: x.encode(read_encoding).decode(decode_as, errors='ignore') if isinstance(x, str) else x)
                        
                        break
                except Exception as e:
                    continue
                    
            if df is not None and len(df.columns) > 1:
                break
        
        if df is None or len(df.columns) <= 1:
            raise Exception("Impossible de charger le fichier avec les encodages et séparateurs testés")
        
    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_file} n'a pas été trouvé.")
        return None
    except Exception as e:
        print(f"Erreur fatale lors du chargement : {e}")
        return None

    # Sauvegarde des colonnes originales pour les conserver
    colonnes_originales = df.columns.tolist()
    print(f"\nColonnes détectées ({len(colonnes_originales)}) :")
    for i, col in enumerate(colonnes_originales, 1):
        print(f"  {i}. {col}")
    
    # =========================================================
    # 🎯 CORRECTION DES NOMS DE COLONNES CORROMPUS
    # =========================================================
    print("\nCorrection des noms de colonnes corrompus...")
    
    # Dictionnaire de correction des noms corrompus
    corrections_noms = {
        'Nombre de Pièces': 'Nombre de Pieces',
        'Nombre de Pi': 'Nombre de Pieces',
        'Nombre de Chambres': 'Nombre de Chambres',
        'Nombre de Ch': 'Nombre de Chambres',
        'Nombre de Salles de Bain': 'Nombre de Salles de Bain',
        'Nombre de S': 'Nombre de Salles de Bain',
        'Étage': 'Etage',
        'État': 'Etat',
        'Sécurité': 'Securite',
        'Sécurit': 'Securite',
        'SécuritÃ©': 'Securite',
        'SÃ©curitÃ©': 'Securite'
    }
    
    # Fonction pour corriger un nom de colonne
    def corriger_nom_colonne(nom):
        # Vérifier correspondance exacte
        if nom in corrections_noms:
            return corrections_noms[nom]
        
        # Vérifier avec normalize (pour gérer les caractères corrompus)
        for corrompu, correct in corrections_noms.items():
            # Comparer en enlevant les caractères spéciaux et corrompus
            nom_clean = re.sub(r'[^a-zA-Z0-9\s]', '', str(nom))
            corrompu_clean = re.sub(r'[^a-zA-Z0-9\s]', '', corrompu)
            if nom_clean.lower().strip() == corrompu_clean.lower().strip():
                return correct
            
            # Détecter les patterns de corruption UTF-8
            if 'curit' in nom.lower() or 'securit' in nom.lower():
                return 'Securite'
        
        return nom  # Garder le nom original si pas de correspondance
    
    # Appliquer les corrections
    df.columns = [corriger_nom_colonne(col) for col in df.columns]
    
    # Mettre à jour la liste des colonnes originales après correction
    colonnes_originales = df.columns.tolist()
    print(f"Colonnes après correction :")
    for i, col in enumerate(colonnes_originales, 1):
        print(f"  {i}. {col}")

    # =========================================================
    # 🎯 0. CRÉATION D'UN MAPPING POUR LES COLONNES À NETTOYER
    # =========================================================
    print("\nCréation du mapping des colonnes à nettoyer...")
    
    # Fonction pour normaliser et détecter les noms de colonnes même avec caractères corrompus
    def normalize_column_name(col_name):
        """Normalise le nom en gérant les caractères corrompus"""
        normalized = str(col_name).strip().lower()
        # Supprimer les caractères spéciaux et corrompus
        normalized = re.sub(r'[^a-z0-9_\s]+', '', normalized)
        # Remplacer espaces par underscore
        normalized = re.sub(r'\s+', '_', normalized)
        # Supprimer underscores multiples
        normalized = re.sub(r'_+', '_', normalized)
        normalized = normalized.strip('_')
        return normalized
    
    # Normalisation pour identifier les colonnes
    mapping = {}
    for orig in df.columns:
        norm = normalize_column_name(orig)
        mapping[norm] = orig
    
    print(f"Mapping des colonnes créé:")
    for norm, orig in list(mapping.items())[:10]:  # Afficher les 10 premières
        print(f"  '{norm}' -> '{orig}'")
    
    # Identification des colonnes à nettoyer (par leur nom normalisé)
    def get_original_col(*possible_names):
        """Retourne le nom original de la colonne si elle existe (teste plusieurs variantes)"""
        for name in possible_names:
            if name in mapping:
                return mapping[name]
        return None
    
    COL_PRIX = get_original_col('prix')
    COL_SURFACE = get_original_col('surface')
    
    # Colonnes numériques - avec toutes les variantes possibles
    COLONNES_NUMERIQUES_MAP = {
        'surface': get_original_col('surface'),
        'nombre_de_pieces': get_original_col('nombre_de_pieces', 'nombre_de_pi'),
        'nombre_de_chambres': get_original_col('nombre_de_chambres', 'nombre_de_ch'),
        'nombre_de_salles_de_bain': get_original_col('nombre_de_salles_de_bain', 'nombre_de_s'),
        'etage': get_original_col('etage', 'tage')
    }
    COLONNES_NUMERIQUES = [v for v in COLONNES_NUMERIQUES_MAP.values() if v is not None]
    
    # Colonnes textuelles
    COLONNES_TEXTUELLES_MAP = {
        'ville': get_original_col('ville'),
        'quartier': get_original_col('quartier'),
        'type_de_bien': get_original_col('type_de_bien', 'type'),
        'etat': get_original_col('etat', 'tat')
    }
    COLONNES_TEXTUELLES = [v for v in COLONNES_TEXTUELLES_MAP.values() if v is not None]
    
    # Colonnes binaires - avec variantes
    binaires_possibles = [
        ('terrasse', ['terrasse']),
        ('garage', ['garage']),
        ('ascenseur', ['ascenseur']),
        ('piscine', ['piscine']),
        ('securite', ['securite', 'scurit']),
        ('jardin', ['jardin']),
        ('cheminee', ['cheminee', 'chemine']),
        ('concierge', ['concierge']),
        ('climatisation', ['climatisation']),
        ('chauffage', ['chauffage']),
        ('antenne_parabolique', ['antenne_parabolique', 'antenne'])
    ]
    
    COLONNES_BINAIRES = []
    for nom, variantes in binaires_possibles:
        col = get_original_col(*variantes)
        if col:
            COLONNES_BINAIRES.append(col)

    print(f"Colonnes à nettoyer identifiées:")
    print(f"  - Prix: {COL_PRIX}")
    print(f"  - Surface: {COL_SURFACE}")
    print(f"  - Numériques: {COLONNES_NUMERIQUES}")
    print(f"  - Textuelles: {COLONNES_TEXTUELLES}")
    print(f"  - Binaires: {COLONNES_BINAIRES}")

    # --- 1. Nettoyage du Prix ---
    print("\nÉtape 1: Nettoyage et conversion du Prix...")
    if COL_PRIX:
        df['_temp_prix'] = df[COL_PRIX].replace('Nan', np.nan) 
        df['_temp_prix'] = df['_temp_prix'].astype(str).str.replace(r'[\s\xa0DH]', '', regex=True)
        df['_temp_prix'] = df['_temp_prix'].str.replace(r'(\d+),(\d{3})', r'\1\2', regex=True)
        df[COL_PRIX] = pd.to_numeric(df['_temp_prix'], errors='coerce')
        df = df.drop(columns=['_temp_prix'], errors='ignore')

    # --- 2. Nettoyage des Caractéristiques Numériques ---
    print("Étape 2: Nettoyage des caractéristiques numériques...")
    for col in COLONNES_NUMERIQUES:
        if col in df.columns:
            df[col] = df[col].replace('Nan', np.nan)
            df['_temp_' + col] = df[col].astype(str).str.extract(r'(\d+)', expand=False)
            df[col] = pd.to_numeric(df['_temp_' + col], errors='coerce')
            df = df.drop(columns=['_temp_' + col], errors='ignore')
    
    # Traitement spécial pour 'etage'
    col_etage = COLONNES_NUMERIQUES_MAP.get('etage')
    if col_etage and col_etage in df.columns:
        df[col_etage] = df[col_etage].astype(str).str.lower().str.extract(r'(\d+)', expand=False).fillna(df[col_etage])
        df[col_etage] = df[col_etage].astype(str).str.lower().replace({'rez-de-chaussée': 0, 'sous-sol': -1, '1er': 1})
        df[col_etage] = pd.to_numeric(df[col_etage], errors='coerce')
    
    # --- 3. Nettoyage des Caractéristiques Textuelles ---
    print("Étape 3: Nettoyage et standardisation des catégories...")
    
    # Fonction de nettoyage des caractères corrompus UTF-8
    def nettoyer_caracteres_corrompus(texte):
        """Nettoie tous les caractères UTF-8 mal encodés"""
        if pd.isna(texte) or texte == 'nan':
            return np.nan
        
        texte = str(texte)
        
        # Dictionnaire de remplacement des caractères corrompus
        replacements = {
            'Ã©': 'e',   # é
            'Ã¨': 'e',   # è
            'Ãª': 'e',   # ê
            'Ã«': 'e',   # ë
            'Ã ': 'a',   # à
            'Ã¢': 'a',   # â
            'Ã¤': 'a',   # ä
            'Ã¯': 'i',   # ï
            'Ã®': 'i',   # î
            'Ã´': 'o',   # ô
            'Ã¶': 'o',   # ö
            'Ã¹': 'u',   # ù
            'Ã»': 'u',   # û
            'Ã¼': 'u',   # ü
            'Ã§': 'c',   # ç
            'Å"': 'oe',  # œ
            'Ã†': 'ae',  # æ
            '©': '',     # ©
            'Ã': '',     # Ã seul
            'â€™': "'",  # apostrophe
            'â€œ': '"',  # guillemet
            'â€': '"',   # guillemet
            'â€"': '-',  # tiret
        }
        
        # Appliquer tous les remplacements
        for corrompu, correct in replacements.items():
            texte = texte.replace(corrompu, correct)
        
        # Nettoyer les espaces multiples
        texte = re.sub(r'\s+', ' ', texte).strip()
        
        return texte
    
    # Appliquer le nettoyage sur toutes les colonnes textuelles
    for col in COLONNES_TEXTUELLES:
        if col in df.columns:
            df[col] = df[col].apply(nettoyer_caracteres_corrompus)
            df[col] = df[col].str.lower().str.strip()
            df[col] = df[col].replace({'nan': np.nan, 'n/a': np.nan, 'inconnu': np.nan})
    
    # Nettoyage aussi pour les colonnes Quartier (souvent avec caractères corrompus)
    col_quartier = COLONNES_TEXTUELLES_MAP.get('quartier')
    if col_quartier and col_quartier in df.columns:
        df[col_quartier] = df[col_quartier].apply(nettoyer_caracteres_corrompus)
        df[col_quartier] = df[col_quartier].str.lower().str.strip()
    
    # Correction spécifique pour la colonne Etat
    col_etat = COLONNES_TEXTUELLES_MAP.get('etat')
    if col_etat and col_etat in df.columns:
        # Corrections spécifiques
        df[col_etat] = df[col_etat].replace({
            'finalis': 'finalise',
            'en cours de c': 'en cours de construction',
            'en cours de co': 'en cours de construction'
        })
    
    # Correction spécifique pour la colonne Quartier
    col_quartier = COLONNES_TEXTUELLES_MAP.get('quartier')
    if col_quartier and col_quartier in df.columns:
        # Standardisation des quartiers
        df[col_quartier] = df[col_quartier].replace({
            'an seba': 'ain sebaa',
            'an sebaa': 'ain sebaa',
            'ain seba': 'ain sebaa',
            'aïn sebaa': 'ain sebaa',
            'ain sbaa': 'ain sebaa',
            'guliz': 'gueliz',
            'guéliz': 'gueliz',
            'gueliz': 'gueliz',
            'geliz': 'gueliz',
            'longchamps (': 'longchamps',
            'bourgogne es': 'bourgogne',
            'cil (hay salam': 'cil hay salam',
            'anfa suprieur': 'anfa superieur',
            'anfa superieur': 'anfa superieur',
            'route amizmiz': 'route amizmiz',
            'riad zitoun': 'riad zitoun',
            'hay targa': 'hay targa',
            'route casabla': 'route casablanca',
            'hay magbrouka': 'hay mabrouka'
        })
        
        # Nettoyage supplémentaire pour enlever les parenthèses et espaces en trop
        df[col_quartier] = df[col_quartier].str.replace(r'\s*\(.*?\)\s*', '', regex=True)
        df[col_quartier] = df[col_quartier].str.strip()
        
    if 'type_de_bien' in df.columns:
        df['type_de_bien'] = df['type_de_bien'].replace({
            'duplex': 'appartement', 
            'bureau': 'commercial/bureau', 
            'commerce': 'commercial/bureau', 
            'plateau de bureau': 'commercial/bureau'
        })
        
    # --- 4. Nettoyage des Caractéristiques Binaires ---
    print("Étape 4: Conversion des caractéristiques binaires...")
    for col in COLONNES_BINAIRES:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip().replace({'oui': 1, 'non': 0, 'nan': 0, 'en cours de c': 0})
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int) 

    # --- 5. Gestion des valeurs manquantes et Outliers ---
    print("Étape 5: Suppression des lignes invalides...")
    if COL_PRIX:
        df = df.dropna(subset=[COL_PRIX])
        df = df[df[COL_PRIX] > 1000] 
    
    if COL_SURFACE:
        df = df.dropna(subset=[COL_SURFACE])
        df = df[df[COL_SURFACE] > 10] 
    
    print(f"Après suppression des NaNs pour Prix/Surface: {len(df)} lignes restantes.")
    
    # Imputation par la médiane pour les caractéristiques numériques
    for col in [c for c in COLONNES_NUMERIQUES if c not in [COL_PRIX, COL_SURFACE]]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    # Suppression des outliers
    if COL_PRIX:
        df = df[df[COL_PRIX].between(df[COL_PRIX].quantile(0.005), df[COL_PRIX].quantile(0.995))]
    if COL_SURFACE:
        df = df[df[COL_SURFACE].between(df[COL_SURFACE].quantile(0.005), df[COL_SURFACE].quantile(0.995))]
    
    # --- 6. Remplissage des NaN catégoriels ---
    print("Étape 6: Remplacement des NaN catégoriels...")
    for col in COLONNES_TEXTUELLES:
        if col in df.columns:
            df[col] = df[col].fillna('inconnu') 
            
    print(f"Après gestion des Outliers: {len(df)} lignes finales.")
    
    # --- 7. Sauvegarde avec TOUTES les colonnes dans l'ordre original ---
    print("\nÉtape 7: Sauvegarde des données...")
    
    # Réorganisation pour garder l'ordre original
    df = df[colonnes_originales]
    
    df.to_csv(output_file, index=False, encoding='utf-8') 
    print(f"\n✅ Nettoyage terminé. Données sauvegardées dans '{output_file}'.")
    print(f"📊 Toutes les {len(colonnes_originales)} colonnes ont été conservées.")
    return df

if __name__ == '__main__':
    df_cleaned = clean_data_ultra_robust(INPUT_FILENAME, OUTPUT_FILENAME) 
    if df_cleaned is not None:
        print("\nRécapitulatif des NaN après le nettoyage :")
        print(df_cleaned.isnull().sum())
        print(f"\n✅ Le fichier '{OUTPUT_FILENAME}' est prêt avec toutes les colonnes originales.")