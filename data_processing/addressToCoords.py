import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import re
import json
from tqdm import tqdm

# --- Configuration ---
BUSINESS_FILE = 'Business.csv'
STREETS_FILE = 'IntersectionLookup.csv'
# New output filename to reflect that it's a clean, filtered dataset
OUTPUT_FILE = 'Business_Geocoded_Interpolation_Clean.csv'

# --- Helper Functions (unchanged) ---

def parse_address(address_line_1):
    """Parses a street address string to extract the number and name."""
    if not isinstance(address_line_1, str): return None, None
    match = re.match(r'^\s*(\d+)\s+(.*)', address_line_1)
    if match:
        number = int(match.group(1))
        name = match.group(2).strip()
        return number, name
    return None, None

def parse_city_from_address(address_str):
    """Extracts a known city name from a full address string."""
    if not isinstance(address_str, str): return None
    cities = ['TORONTO', 'MISSISSAUGA', 'RICHMOND HILL', 'MILTON', 'VAUGHAN', 'MARKHAM']
    for city in cities:
        if re.search(r'\b' + city + r'\b', address_str, re.IGNORECASE):
            return city.upper()
    return None

def standardize_street_name(name):
    """Converts a street name to a standard format (UPPERCASE, abbreviated)."""
    if not isinstance(name, str): return ""
    replacements = {
        'STREET': 'ST', 'AVENUE': 'AVE', 'BOULEVARD': 'BLVD', 'ROAD': 'RD',
        'DRIVE': 'DR', 'LANE': 'LN', 'COURT': 'CT', 'SQUARE': 'SQ',
        'PARKWAY': 'PKWY', 'CIRCLE': 'CIR', 'WEST': 'W', 'EAST': 'E',
        'NORTH': 'N', 'SOUTH': 'S'
    }
    name = name.upper()
    for full, abbr in replacements.items():
        name = re.sub(r'\b' + full + r'\b', abbr, name)
    name = name.replace('.', '').strip()
    return name

def geocode_with_interpolation():
    """Main function to perform address interpolation and save a clean output."""
    print("--- Starting Local Address Geocoding (with City Logic & Cleanup) ---")

    # Steps 1, 2, 3, and 4 are identical to the previous script
    # ... (Loading, Preparing Business Data, Preparing Street Data, Geocoding) ...
    
    # --- 1. Load Data ---
    print("Step 1: Loading datasets...")
    licenses_df = pd.read_csv(BUSINESS_FILE)
    streets_df = pd.read_csv(STREETS_FILE)

    # --- 2. Prepare Business Data ---
    print("Step 2: Parsing and standardizing business addresses...")
    licenses_df[['address_number', 'street_name_raw']] = licenses_df['Licence Address Line 1'].apply(lambda x: pd.Series(parse_address(x)))
    licenses_df['street_name_std'] = licenses_df['street_name_raw'].apply(standardize_street_name)
    licenses_df['full_address_str'] = licenses_df['Licence Address Line 1'].fillna('') + ' ' + licenses_df['Licence Address Line 2'].fillna('') + ' ' + licenses_df['Licence Address Line 3'].fillna('')
    licenses_df['city_std'] = licenses_df['full_address_str'].apply(parse_city_from_address)
    licenses_df['city_street_key'] = licenses_df['city_std'].fillna('') + '_' + licenses_df['street_name_std'].fillna('')

    # --- 3. Prepare Street Centerline Data ---
    print("Step 3: Standardizing street centerline data...")
    streets_df['street_name_std'] = streets_df['LINEAR_NAME_FULL'].apply(standardize_street_name)
    streets_df['city_std'] = streets_df['JURISDICTION'].str.replace('CITY OF ', '').str.upper().fillna('')
    streets_df['city_street_key'] = streets_df['city_std'] + '_' + streets_df['street_name_std']
    addr_cols = ['LO_NUM_L', 'HI_NUM_L', 'LO_NUM_R', 'HI_NUM_R']
    for col in addr_cols: streets_df[col] = pd.to_numeric(streets_df[col], errors='coerce')
    def parse_geom(geom_str):
        try: return LineString(json.loads(geom_str)['coordinates'][0])
        except: return None
    streets_df['geometry_obj'] = streets_df['geometry'].apply(parse_geom)
    streets_df.dropna(subset=['geometry_obj'] + addr_cols, inplace=True)
    streets_gdf = gpd.GeoDataFrame(streets_df, geometry='geometry_obj', crs="EPSG:4326")
    
    # --- 4. Geocoding with the New Key ---
    print("Step 4: Geocoding addresses using the city_street_key...")
    street_groups = streets_gdf.groupby('city_street_key')
    geocoded_points = []
    for _, business in tqdm(licenses_df.iterrows(), total=licenses_df.shape[0]):
        point = None
        addr_num, lookup_key = business['address_number'], business['city_street_key']
        if pd.notna(addr_num) and lookup_key in street_groups.groups:
            candidate_segments = street_groups.get_group(lookup_key)
            is_even = addr_num % 2 == 0
            for _, segment in candidate_segments.iterrows():
                if is_even and segment['PARITY_R'] == 'E' and segment['LO_NUM_R'] <= addr_num <= segment['HI_NUM_R']: side = 'R'
                elif not is_even and segment['PARITY_L'] == 'O' and segment['LO_NUM_L'] <= addr_num <= segment['HI_NUM_L']: side = 'L'
                else: continue
                low, high = segment[f'LO_NUM_{side}'], segment[f'HI_NUM_{side}']
                fraction = 0.5 if high == low else (addr_num - low) / (high - low)
                point = segment['geometry_obj'].interpolate(fraction, normalized=True)
                break
        geocoded_points.append(point)

    # --- 5. Finalize, CLEAN, and Save ---
    print("\nStep 5: Finalizing, cleaning, and saving results...")
    
    licenses_df['geometry'] = geocoded_points
    licenses_df['latitude'] = licenses_df['geometry'].apply(lambda p: p.y if p else None)
    licenses_df['longitude'] = licenses_df['geometry'].apply(lambda p: p.x if p else None)
    
    # Report on success rate before dropping records
    successful_count = licenses_df['latitude'].notna().sum()
    total_count = len(licenses_df)
    success_rate = (successful_count / total_count) * 100
    print(f"Successfully geocoded {successful_count} of {total_count} records ({success_rate:.2f}%).")
    
    # ==================================================================
    # ** NEW STEP: Drop all rows where geocoding failed (coords are NaN) **
    # ==================================================================
    records_to_drop = total_count - successful_count
    if records_to_drop > 0:
        print(f"Dropping {records_to_drop} records that could not be geocoded...")
    
    # Use .dropna() on the latitude column to filter the DataFrame
    geocoded_clean_df = licenses_df.dropna(subset=['latitude'])
    
    # Select and reorder columns for the final, clean output file
    output_columns = [
        '_id', 'Operating Name', 'Category', 'Issued', 'Licence Address Line 1',
        'city_std', 'latitude', 'longitude'
    ]
    final_df = geocoded_clean_df[output_columns]
    
    # Save the cleaned DataFrame
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nClean geocoded data saved to '{OUTPUT_FILE}'")
    print(f"The final file contains {len(final_df)} rows.")
    
    print("\n--- Sample of Final Clean Data ---")
    print(final_df.head())

if __name__ == '__main__':
    geocode_with_interpolation()