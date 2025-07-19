import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler

# --- Configuration ---
MASTER_DATA_FILE = '../data_processing/MasterDataset.csv'
OUTPUT_FILE = 'SocioeconomicStats.csv'

def feature_engineering(df):
    """
    Engineers new features from the raw data to improve model performance.
    """
    print("Starting feature engineering...")
    
    crime_types = ['ASSAULT', 'AUTOTHEFT', 'ROBBERY', 'BREAKENTER']
    years = np.arange(5)
    
    for crime in crime_types:
        rate_cols = [f'{crime}_RATE_{year}' for year in range(2019, 2024)]
        def get_slope(row):
            rates = pd.to_numeric(row[rate_cols], errors='coerce').fillna(0)
            if rates.isnull().all(): return 0
            return np.polyfit(years, rates, 1)[0]
        df[f'{crime}_rate_5yr_trend'] = df.apply(get_slope, axis=1)

    df['safety_score_2023'] = (df['ASSAULT_RATE_2023'] * 0.4 +
                               df['ROBBERY_RATE_2023'] * 0.3 +
                               df['BREAKENTER_RATE_2023'] * 0.2 +
                               df['AUTOTHEFT_RATE_2023'] * 0.1)
                               
    epsilon = 1e-6
    df['businesses_per_1000_capita'] = (df['business_count'] / (df['POPULATION_2024'] + epsilon)) * 1000
    df['schools_per_1000_capita'] = (df['school_count'] / (df['POPULATION_2024'] + epsilon)) * 1000
    df['construction_per_1000_capita'] = (df['construction_project_count'] / (df['POPULATION_2024'] + epsilon)) * 1000

    print("Feature engineering complete.")
    return df

def train_and_predict_growth():
    """
    Main function to calculate both a 'Current Vibrancy Score' and a predicted 'Growth Potential Score'.
    """
    df = pd.read_csv(MASTER_DATA_FILE)
    df = feature_engineering(df)
    
    # ==================================================================
    # ** NEW SECTION: Create the "Current Vibrancy Score" **
    # ==================================================================
    print("\nCalculating the 'Current Vibrancy Score'...")
    
    # 1. Normalize the component features to a 0-1 scale
    scaler = MinMaxScaler()
    # Note: For safety, lower is better, so we will invert its normalized score later.
    df['safety_norm'] = scaler.fit_transform(df[['safety_score_2023']])
    df['schools_norm'] = scaler.fit_transform(df[['schools_per_1000_capita']])
    df['businesses_norm'] = scaler.fit_transform(df[['businesses_per_1000_capita']])
    
    # Invert the safety score (a low crime score should equal a high safety rating)
    df['safety_norm'] = 1 - df['safety_norm']
    
    # 2. Calculate the weighted average
    vibrancy_score = (df['safety_norm'] * 0.50 +      # 50% weight for safety
                      df['schools_norm'] * 0.30 +     # 30% weight for schools
                      df['businesses_norm'] * 0.20)   # 20% weight for businesses
                      
    # 3. Scale the final score to be out of 100
    df['current_vibrancy_score'] = vibrancy_score * 100
    
    # --- Machine Learning for the "Growth Potential Score" ---
    print("\nSimulating historical property value data for training...")
    np.random.seed(42)
    safety_norm_sim = df['safety_score_2023'].fillna(df['safety_score_2023'].mean())
    schools_norm_sim = df['schools_per_1000_capita'].fillna(df['schools_per_1000_capita'].mean())
    construction_norm_sim = df['construction_per_1000_capita'].fillna(df['construction_per_1000_capita'].mean())
    
    simulated_growth = (
        -0.05 * safety_norm_sim / safety_norm_sim.mean() +
        0.10 * schools_norm_sim / schools_norm_sim.mean() +
        0.15 * construction_norm_sim / construction_norm_sim.mean() +
        np.random.normal(0, 0.05, len(df))
    )
    df['property_value_growth_3yr'] = 0.15 + simulated_growth
    
    features = [
        'ASSAULT_rate_5yr_trend', 'AUTOTHEFT_rate_5yr_trend',
        'ROBBERY_rate_5yr_trend', 'BREAKENTER_rate_5yr_trend',
        'safety_score_2023', 'businesses_per_1000_capita',
        'schools_per_1000_capita', 'construction_per_1000_capita',
        'POPULATION_2024'
    ]
    
    X = df[features].fillna(0)
    y = df['property_value_growth_3yr']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nTraining the XGBoost Regressor model...")
    xgbr = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='rmse',               
        early_stopping_rounds=50          
    )

    xgbr.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    
    print("\nEvaluating model performance...")
    preds = xgbr.predict(X_test)
    print(f"Test Set RMSE: {np.sqrt(mean_squared_error(y_test, preds)):.4f}")
    print(f"Test Set R-squared: {r2_score(y_test, preds):.4f}")
    
    print("\n--- Top 10 Most Important Features ---")
    feature_importances = pd.DataFrame({'feature': features, 'importance': xgbr.feature_importances_}).sort_values('importance', ascending=False)
    print(feature_importances.head(10))
    
    print("\nGenerating final 'Growth Potential Score' for all neighborhoods...")
    raw_predictions = xgbr.predict(X)
    min_score = raw_predictions.min()
    max_score = raw_predictions.max()
    df['growth_potential_score'] = 100 * (raw_predictions - min_score) / (max_score - min_score)
    
    # --- Save the Final Output for the App ---
    output_cols = [
        'HOOD_ID', 'AREA_NAME', 
        'current_vibrancy_score',   # The "Present" score
        'growth_potential_score',   # The "Future" score
        'geometry'
    ]
    
    final_df = df[output_cols]
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nSuccess! Final data with both scores saved to '{OUTPUT_FILE}'")
    print("\n--- Sample of Final App Data ---")
    print(final_df[['AREA_NAME', 'current_vibrancy_score', 'growth_potential_score']].sort_values('growth_potential_score', ascending=False).head())

if __name__ == '__main__':
    train_and_predict_growth()