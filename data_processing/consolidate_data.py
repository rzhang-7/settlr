import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
import json
import sys

# --- Configuration ---
BUSINESS_FILE = 'Business_Geocoded_Interpolation_Clean.csv'
CONSTRUCTION_FILE = 'Construction.csv'
SCHOOLS_FILE = 'torontoSchoolCoords.csv'
CRIME_STATS_FILE = 'CrimeStats.csv'
OUTPUT_FILE = 'MasterDataSet.csv'

# --- Helper Functions ---
def check_required_columns(df, required_cols, filename):
    """Checks if a DataFrame contains all required columns."""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: The file '{filename}' is missing required columns: {missing_cols}")
        sys.exit()

def parse_polygon_or_line_geometry(geom_str):
    """Safely parses a GeoJSON string for Polygons or LineStrings."""
    try:
        return shape(json.loads(geom_str))
    except (TypeError, json.JSONDecodeError, ValueError):
        return None

# <-- NEW, SPECIALIZED FUNCTION FOR POINTS -->
def parse_as_point(geom_str):
    """
    Robustly parses a geometry string, expecting a point.
    It handles 'MultiPoint' with a single coordinate by extracting it.
    """
    try:
        geom_json = json.loads(geom_str)
        # Directly access the first coordinate pair, ignoring the 'MultiPoint' type
        coords = geom_json['coordinates'][0]
        return Point(coords)
    except (TypeError, json.JSONDecodeError, ValueError, IndexError):
        return None

def create_master_dataset_final_corrected():
    """
    Correctly consolidates all data, using specialized parsers for each geometry type.
    """
    print("--- Starting FINAL CORRECTED Data Consolidation for Urban Bloom ---")

    # --- 1. Load Neighborhoods (Polygons) ---
    print("Step 1: Loading neighborhood boundaries...")
    try:
        neighborhoods_df = pd.read_csv(CRIME_STATS_FILE)
    except FileNotFoundError:
        print(f"FATAL ERROR: '{CRIME_STATS_FILE}' not found.")
        sys.exit()
    check_required_columns(neighborhoods_df, ['HOOD_ID', 'geometry'], CRIME_STATS_FILE)
    neighborhoods_df['geometry'] = neighborhoods_df['geometry'].apply(parse_polygon_or_line_geometry)
    neighborhoods_gdf = gpd.GeoDataFrame(neighborhoods_df, geometry='geometry', crs="EPSG:4326").dropna(subset=['geometry'])
    print(f"Loaded {len(neighborhoods_gdf)} valid neighborhood polygons.")

    # --- 2. Process Business Data (Points) ---
    print("\nStep 2: Processing business data...")
    try:
        businesses_df = pd.read_csv(BUSINESS_FILE)
        check_required_columns(businesses_df, ['latitude', 'longitude'], BUSINESS_FILE)
        businesses_gdf = gpd.GeoDataFrame(businesses_df, geometry=gpd.points_from_xy(businesses_df.longitude, businesses_df.latitude), crs="EPSG:4326")
        businesses_in_neighborhoods = gpd.sjoin(businesses_gdf, neighborhoods_gdf[['HOOD_ID', 'geometry']], how="inner", predicate="intersects")
        business_counts = businesses_in_neighborhoods.groupby('HOOD_ID').size().reset_index(name='business_count')
        print(f"Aggregated business counts for {len(business_counts)} neighborhoods.")
    except FileNotFoundError:
        business_counts = pd.DataFrame(columns=['HOOD_ID', 'business_count'])

    # --- 3. Process Construction Data (Lines) ---
    print("\nStep 3: Processing construction project data...")
    try:
        constructions_df = pd.read_csv(CONSTRUCTION_FILE)
        check_required_columns(constructions_df, ['geometry'], CONSTRUCTION_FILE)
        constructions_df['geometry'] = constructions_df['geometry'].apply(parse_polygon_or_line_geometry)
        constructions_gdf = gpd.GeoDataFrame(constructions_df, geometry='geometry', crs="EPSG:4326").dropna(subset=['geometry'])
        constructions_in_neighborhoods = gpd.sjoin(constructions_gdf, neighborhoods_gdf[['HOOD_ID', 'geometry']], how="inner", predicate="intersects")
        construction_counts = constructions_in_neighborhoods.groupby('HOOD_ID').size().reset_index(name='construction_project_count')
        print(f"Aggregated construction project counts for {len(construction_counts)} neighborhoods.")
    except FileNotFoundError:
        construction_counts = pd.DataFrame(columns=['HOOD_ID', 'construction_project_count'])

    # --- 4. Process School Data (Points - with the new parser) ---
    print("\nStep 4: Processing school data...")
    try:
        schools_df = pd.read_csv(SCHOOLS_FILE)
        check_required_columns(schools_df, ['geometry'], SCHOOLS_FILE)
        # <-- FIX: Use the new, specialized parse_as_point function -->
        schools_df['geometry'] = schools_df['geometry'].apply(parse_as_point)
        schools_gdf = gpd.GeoDataFrame(schools_df, geometry='geometry', crs="EPSG:4326").dropna(subset=['geometry'])
        
        schools_in_neighborhoods = gpd.sjoin(schools_gdf, neighborhoods_gdf[['HOOD_ID', 'geometry']], how="inner", predicate="intersects")
        school_counts = schools_in_neighborhoods.groupby('HOOD_ID').size().reset_index(name='school_count')
        print(f"Aggregated school counts for {len(school_counts)} neighborhoods.")
    except FileNotFoundError:
        school_counts = pd.DataFrame(columns=['HOOD_ID', 'school_count'])

    # --- 5. Merge All Data ---
    print("\nStep 5: Merging all data sources...")
    master_df = neighborhoods_df.copy()
    
    if not business_counts.empty: master_df = pd.merge(master_df, business_counts, on='HOOD_ID', how='left')
    if not construction_counts.empty: master_df = pd.merge(master_df, construction_counts, on='HOOD_ID', how='left')
    if not school_counts.empty: master_df = pd.merge(master_df, school_counts, on='HOOD_ID', how='left')
    
    count_cols = ['business_count', 'construction_project_count', 'school_count']
    for col in count_cols:
        if col not in master_df.columns: master_df[col] = 0
        else: master_df[col] = master_df[col].fillna(0).astype(int)
    
    # --- 6. Save Final Dataset ---
    print("\nStep 6: Saving the final master dataset...")
    master_df['geometry'] = master_df['geometry'].apply(lambda geom: geom.wkt if geom else None)
    master_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nSuccess! Master dataset created at: '{OUTPUT_FILE}'")
    print("\n--- Sample of Final Master Data ---")
    print(master_df[['AREA_NAME', 'HOOD_ID', 'business_count', 'construction_project_count', 'school_count']].head())

if __name__ == '__main__':
    create_master_dataset_final_corrected()