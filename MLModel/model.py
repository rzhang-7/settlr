import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
# Import the scaler for our new scores
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
    Main function to load data, train the model, and predict future growth.
    """
    df = pd.read_csv(MASTER_DATA_FILE)
    df = feature_engineering(df)
    
    print("\nSimulating historical property value data for training...")
    np.random.seed(42)
    safety_norm = df['safety_score_2023'].fillna(df['safety_score_2023'].mean())
    schools_norm = df['schools_per_1000_capita'].fillna(df['schools_per_1000_capita'].mean())
    construction_norm = df['construction_per_1000_capita'].fillna(df['construction_per_1000_capita'].mean())
    
    simulated_growth = (
        -0.05 * safety_norm / safety_norm.mean() +
        0.10 * schools_norm / schools_norm.mean() +
        0.15 * construction_norm / construction_norm.mean() +
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
    
    # Using the older API structure that matches your environment
    xgbr = xgb.XGBRegressor(
        objective='reg:squarederror',
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        eval_metric='rmse',                # <- moved here
        early_stopping_rounds=50          # <- moved here
    )
    xgbr.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # --- Evaluation and Prediction ---
    print("\nEvaluating model performance...")
    preds = xgbr.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)
    print(f"Test Set RMSE: {rmse:.4f}")
    print(f"Test Set R-squared: {r2:.4f}")
    
    print("\n--- Top 10 Most Important Features ---")
    feature_importances = pd.DataFrame({
        'feature': features,
        'importance': xgbr.feature_importances_
    }).sort_values('importance', ascending=False)
    print(feature_importances.head(10))
    
    print("\nGenerating final 'Growth Potential Score' for all neighborhoods...")
    raw_predictions = xgbr.predict(X)
    min_score = raw_predictions.min()
    max_score = raw_predictions.max()
    df['growth_potential_score'] = 100 * (raw_predictions - min_score) / (max_score - min_score)
    
    # ==================================================================
    # ** NEW SECTION: Calculate Current Status Scores **
    # ==================================================================
    print("\nCalculating Current Status Scores (Safety, School, Business)...")
    
    # Initialize a scaler to put scores on a 0-100 range
    scaler = MinMaxScaler(feature_range=(0, 100))
    
    # --- Safety Score ---
    # A lower raw crime score is better. We will scale and then invert it.
    raw_safety_values = df[['safety_score_2023']].fillna(0)
    scaled_safety = scaler.fit_transform(raw_safety_values)
    df['safety_score'] = 100 - scaled_safety # Invert the score

    # --- School Score ---
    raw_school_values = df[['schools_per_1000_capita']].fillna(0)
    df['school_score'] = scaler.fit_transform(raw_school_values)

    # --- Business/Job Score (Amenity Score) ---
    raw_business_values = df[['businesses_per_1000_capita']].fillna(0)
    df['business_job_score'] = scaler.fit_transform(raw_business_values)
    
    # ==================================================================
    # ** FINAL STEP: Define Output Columns and Save **
    # ==================================================================
    
    # Define the clean, final columns for the app's use
    output_cols = [
        'HOOD_ID', 'AREA_NAME', 
        'growth_potential_score',   # The "Future" score
        'safety_score',             # The "Present" safety score
        'school_score',             # The "Present" school score
        'business_job_score',       # The "Present" business/amenity score
        'geometry'
    ]
    
    final_df = df[output_cols]
    final_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nSuccess! Final data with all scores saved to '{OUTPUT_FILE}'")
    print("\n--- Sample of Final App Data ---")
    print(final_df[['AREA_NAME', 'growth_potential_score', 'safety_score', 'school_score', 'business_job_score']].sort_values('growth_potential_score', ascending=False).head())

if __name__ == '__main__':
    train_and_predict_growth()