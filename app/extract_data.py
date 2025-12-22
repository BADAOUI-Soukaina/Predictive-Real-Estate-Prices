import pandas as pd
import json

# Charger les données
df = pd.read_csv("data_final.csv", sep=None, engine="python")

# Extraire les villes uniques
villes = sorted(df['ville'].unique().tolist())

# Extraire les quartiers par ville
quartiers_par_ville = {}
for ville in villes:
    quartiers = sorted(df[df['ville'] == ville]['quartier'].unique().tolist())
    quartiers_par_ville[ville] = quartiers

# Déterminer les types de biens disponibles
# Les colonnes commencent par "bien_"
colonnes_biens = [col for col in df.columns if col.startswith('bien_')]
types_biens = [col.replace('bien_', '').replace(' ', '_') for col in colonnes_biens]

print(f"Types de biens trouvés : {types_biens}")

# Équipements possibles (colonnes booléennes/binaires)
equipements_possibles = ['terrasse', 'garage', 'ascenseur', 'piscine', 'securite']

# Pour chaque type de bien, déterminer quels équipements sont pertinents
# Un équipement est pertinent si au moins 5% des biens de ce type l'ont
type_features = {}
types_sans_chambres = []
types_avec_etage = []

for idx, col_bien in enumerate(colonnes_biens):
    type_bien = types_biens[idx]
    
    # Filtrer les biens de ce type
    df_type = df[df[col_bien] == True]
    
    if len(df_type) == 0:
        continue
    
    # Déterminer les équipements pertinents
    features = []
    for equip in equipements_possibles:
        if equip in df.columns:
            # Calculer le pourcentage de biens avec cet équipement
            pourcentage = (df_type[equip].sum() / len(df_type)) * 100
            # Si plus de 5% des biens ont cet équipement, il est pertinent
            if pourcentage > 5:
                features.append(equip)
    
    type_features[type_bien] = features
    
    # Déterminer si ce type a généralement des chambres
    if 'nombre_de_chambres' in df.columns:
        avg_chambres = df_type['nombre_de_chambres'].mean()
        # Si en moyenne moins de 0.5 chambre, c'est un type sans chambres
        if avg_chambres < 0.5:
            types_sans_chambres.append(type_bien)
    
    # Déterminer si ce type a des étages
    if 'etage' in df.columns:
        avg_etage = df_type['etage'].mean()
        max_etage = df_type['etage'].max()
        # Si l'étage moyen > 0 ou max > 2, c'est un type avec étages
        if avg_etage > 0.5 or max_etage > 2:
            types_avec_etage.append(type_bien)

print(f"\nÉquipements par type de bien :")
for type_bien, features in type_features.items():
    print(f"  {type_bien}: {features}")

print(f"\nTypes sans chambres : {types_sans_chambres}")
print(f"Types avec étages : {types_avec_etage}")

# Créer un objet JSON
data = {
    "villes": villes,
    "quartiers_par_ville": quartiers_par_ville,
    "type_features": type_features,
    "types_sans_chambres": types_sans_chambres,
    "types_avec_etage": types_avec_etage,
    "types_biens_disponibles": types_biens
}

# Sauvegarder dans un fichier JavaScript
with open("data.js", "w", encoding="utf-8") as f:
    f.write("const DATA = ")
    f.write(json.dumps(data, ensure_ascii=False, indent=2))
    f.write(";")

print(f"\n Données extraites : {len(villes)} villes")
print(f" {len(types_biens)} types de biens")
print(f" Fichier data.js créé avec succès")