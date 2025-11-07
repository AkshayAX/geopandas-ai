import requests
import json
import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Step 1: Fetch Abu Dhabi boundaries data
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {
    'where': '1=1',
    'outFields': '*',
    'returnGeometry': 'true',
    'f': 'geojson',
    'spatialRel': 'esriSpatialRelIntersects'
}

print("Fetching data from API...")
response = requests.get(url, params=params, verify=False)

if response.status_code != 200:
    raise Exception(f"API request failed with status code: {response.status_code}")

geojson_data = response.json()

# Validate the response
if 'type' not in geojson_data or 'features' not in geojson_data:
    print("⚠ Warning: Response doesn't look like proper GeoJSON")
    print(f"Response keys: {list(geojson_data.keys())}")

    # Try to load directly with geopandas from_features or from the URL
    print("\nTrying alternative approach: loading directly with geopandas...")

    # Option 1: Try with 'json' format instead of 'geojson'
    params['f'] = 'json'
    response = requests.get(url, params=params, verify=False)

    # Save the raw response
    with open('admin_boundaries_raw.json', 'w', encoding='utf-8') as f:
        json.dump(response.json(), f, indent=2)

    # Try to read with geopandas using ESRI JSON driver
    try:
        gdf = gpd.read_file('admin_boundaries_raw.json')
        print(f"✓ Successfully loaded {len(gdf)} features")
    except Exception as e:
        print(f"✗ Failed to load with geopandas: {e}")
        print("\nTrying to load directly from URL...")
        # Try loading directly from the service
        gdf = gpd.read_file(url, driver="ESRIJSON")

else:
    # Proper GeoJSON - save and load
    print(f"✓ Valid GeoJSON with {len(geojson_data['features'])} features")
    with open('admin_boundaries.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)

    gdf = gpd.read_file('admin_boundaries.geojson')

# Convert to GeoDataFrameAI
print(f"\nData loaded successfully!")
print(f"Shape: {gdf.shape}")
print(f"CRS: {gdf.crs}")
print(f"Columns: {list(gdf.columns)}")

# Step 2: Configure GeoPandas-AI to use Ollama
print("\nConfiguring Ollama...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
    }
)

# Step 3: Create GeoDataFrameAI and chat
gdfai = GeoDataFrameAI(gdf)

print("\nAsking AI to plot the data...")
response = gdfai.chat(
    "Plot the administrative boundaries colored by district"
)

print("\n" + "="*50)
print("RESULT:")
print("="*50)
print(response)

print("\n" + "="*50)
print("GENERATED CODE:")
print("="*50)
print(gdfai.code)
