import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import xgboost as xgb
import warnings
warnings.filterwarnings("ignore")

# ============================================
# 1️⃣ CHARGEMENT DES DONNÉES
# ============================================
print("="*70)
print("🏠 PIPELINE DE PRÉDICTION DES PRIX IMMOBILIERS")
print("="*70)

df = pd.read_csv(
    "data_final.csv",
    sep=None,
    engine="python"
)


# ============================================
# 2️⃣ NETTOYAGE & OUTLIERS
# ============================================
print("\n📊 Préparation des données")

# Clipping percentile (plus robuste que IQR)
low, high = df['prix'].quantile([0.01, 0.99])
df = df[(df['prix'] >= low) & (df['prix'] <= high)].copy()

print(f"✓ Outliers supprimés")

# Log-transform de la cible
df['prix_log'] = np.log1p(df['prix'])

# ============================================
# 3️⃣ ENCODAGE CATÉGORIEL
# ============================================
le_ville = LabelEncoder()
df['ville_encoded'] = le_ville.fit_transform(df['ville'])

# ============================================
# 4️⃣ FEATURES ENGINEERING
# ============================================
df['prix_m2'] = df['prix'] / df['surface']

df['surface_villa'] = df['surface'] * df['bien_villa'].astype(int)
df['surface_appartement'] = df['surface'] * df['bien_appartement'].astype(int)

# ============================================
# 5️⃣ SÉLECTION DES FEATURES
# ============================================
numeric_features = [
    'surface', 'nombre_de_chambres',
    'nombre_de_salles_de_bain', 'etage',
    'score_commodites', 'prix_m2',
    'surface_villa', 'surface_appartement'
]

binary_features = [
    'terrasse', 'garage', 'ascenseur',
    'piscine', 'securite'
]

type_bien_features = [
    'bien_appartement', 'bien_bureau',
    'bien_local_commercial',
    'bien_maison', 'bien_riad',
    'bien_terrain', 'bien_villa'
]

encoded_features = ['ville_encoded']

all_features = numeric_features + binary_features + type_bien_features + encoded_features

for col in type_bien_features:
    df[col] = df[col].astype(int)

# ============================================
# 6️⃣ SPLIT TRAIN / TEST
# ============================================
X = df[all_features].copy()
y = df['prix_log']


X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ============================================
# 7️⃣ TARGET ENCODING (SANS DATA LEAKAGE)
# ============================================
quartier_mean = df.loc[X_train.index].groupby('quartier')['prix'].mean()
df['quartier_target_encoded'] = df['quartier'].map(quartier_mean)
df['quartier_target_encoded'].fillna(quartier_mean.mean(), inplace=True)

X_train['quartier_target_encoded'] = df.loc[X_train.index, 'quartier_target_encoded']
X_test['quartier_target_encoded'] = df.loc[X_test.index, 'quartier_target_encoded']

# ============================================
# 8️⃣ MODÈLES
# ============================================
models = {}

models['Random Forest'] = RandomForestRegressor(
    n_estimators=300,
    max_depth=25,
    min_samples_split=10,
    min_samples_leaf=3,
    max_features='sqrt',
    random_state=42,
    n_jobs=-1
)

models['XGBoost'] = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

models['Gradient Boosting'] = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    random_state=42
)

# ============================================
# 9️⃣ ENTRAÎNEMENT & ÉVALUATION
# ============================================
results = []

for name, model in models.items():
    print(f"\n🚀 Entraînement : {name}")
    model.fit(X_train, y_train)

    y_pred_log = model.predict(X_test)

    # Métriques en log
    rmse_log = np.sqrt(mean_squared_error(y_test, y_pred_log))
    mae_log = mean_absolute_error(y_test, y_pred_log)

    # Métriques réelles
    y_test_real = np.expm1(y_test)
    y_pred_real = np.expm1(y_pred_log)

    r2 = r2_score(y_test_real, y_pred_real)
    rmse = np.sqrt(mean_squared_error(y_test_real, y_pred_real))
    mae = mean_absolute_error(y_test_real, y_pred_real)

    results.append({
        'Modèle': name,
        'R²': r2,
        'RMSE': rmse,
        'MAE': mae,
        'RMSE_log': rmse_log,
        'MAE_log': mae_log
    })

results_df = pd.DataFrame(results).sort_values('R²', ascending=False)

print("\n🏆 CLASSEMENT FINAL\n")
print(results_df.to_string(index=False))

best_model_name = results_df.iloc[0]['Modèle']
best_model = models[best_model_name]

print(f"\n🥇 Meilleur modèle : {best_model_name}")

# ============================================
# 🔟 FEATURE IMPORTANCE
# ============================================
if hasattr(best_model, "feature_importances_"):
    importances = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\n🔍 Top 15 Features\n")
    print(importances.head(15).to_string(index=False))

    plt.figure(figsize=(10,6))
    plt.barh(importances.head(15)['feature'], importances.head(15)['importance'])
    plt.gca().invert_yaxis()
    plt.title(f"Feature Importance - {best_model_name}")
    plt.tight_layout()
    plt.show()

    import joblib

joblib.dump(best_model, "best_price_model.pkl")
print("✅ Modèle sauvegardé : best_price_model.pkl")
