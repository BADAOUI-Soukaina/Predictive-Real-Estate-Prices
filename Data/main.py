from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder

# =============================
# CHARGEMENT DES OBJETS
# =============================
model = joblib.load("best_price_model.pkl")
df_ref = pd.read_csv("data_final.csv", sep=None, engine="python")

# Encoder ville (identique entraînement)
le_ville = LabelEncoder()
le_ville.fit(df_ref["ville"])

# Statistiques nécessaires
prix_m2_ville = df_ref.groupby("ville")["prix"].mean() / df_ref.groupby("ville")["surface"].mean()
quartier_mean = df_ref.groupby("quartier")["prix"].mean()
quartier_global_mean = quartier_mean.mean()

# =============================
# FASTAPI
# =============================
app = FastAPI(title="Real Estate Price Prediction API")

# =============================
# INPUT UTILISATEUR
# =============================
class UserInput(BaseModel):
    surface: float
    nombre_de_pieces: int
    nombre_de_chambres: int
    nombre_de_salles_de_bain: int
    etage: int

    terrasse: int
    garage: int
    ascenseur: int
    piscine: int
    securite: int

    type_bien: str
    ville: str
    quartier: str

# =============================
# PREDICTION
# =============================
@app.post("/predict")
def predict_price(user: UserInput):
    # --- Encodage type de bien ---
    type_bien_cols = [
        'bien_appartement', 'bien_bureau', 'bien_ferme',
        'bien_local_commercial', 'bien_logement',
        'bien_maison', 'bien_riad',
        'bien_terrain', 'bien_villa'
    ]
    type_bien_data = {col: 0 for col in type_bien_cols}
    key = f"bien_{user.type_bien.lower()}"
    if key in type_bien_data:
        type_bien_data[key] = 1

    # --- Encodage ville ---
    ville_encoded = hash(user.ville.lower()) % 100

    # --- Target encoding quartier ---
    quartier_target_encoded = 12000.0  # fallback global mean

    # --- Features dérivées ---
    prix_m2 = 10000
    surface_villa = user.surface * type_bien_data['bien_villa']
    surface_appartement = user.surface * type_bien_data['bien_appartement']
    score_commodites = 0.5

    data = {
        "surface": user.surface,
        "nombre_de_pieces": user.nombre_de_pieces,
        "nombre_de_chambres": user.nombre_de_chambres,
        "nombre_de_salles_de_bain": user.nombre_de_salles_de_bain,
        "etage": user.etage,
        "score_commodites": score_commodites,
        "prix_m2": prix_m2,
        "surface_villa": surface_villa,
        "surface_appartement": surface_appartement,
        "terrasse": user.terrasse,
        "garage": user.garage,
        "ascenseur": user.ascenseur,
        "piscine": user.piscine,
        "securite": user.securite,
        **type_bien_data,
        "ville_encoded": ville_encoded,
        "quartier_target_encoded": quartier_target_encoded
    }

    df = pd.DataFrame([data])
    log_price = model.predict(df)[0]
    predicted_price = float(np.expm1(log_price))

    # --- Retourner la prédiction réelle ---
    return {
        "predicted_price_MAD": predicted_price,
        "formatted_price": f"{predicted_price:,.2f} MAD"
    }


# =============================
# HEALTH CHECK
# =============================
@app.get("/health")
def health():
    return {"status": "ok"}
