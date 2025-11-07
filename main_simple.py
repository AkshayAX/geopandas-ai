import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config

# Step 1: Load data directly from ArcGIS REST API
print("Loading data from ArcGIS service...")

# Construct the query URL
base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
full_url = base_url + query_params

try:
    # Option 1: Try loading as GeoJSON
    gdf = gpd.read_file(full_url)
    print(f"✓ Successfully loaded {len(gdf)} features")
except Exception as e:
    print(f"GeoJSON failed: {e}")
    print("Trying ESRI JSON format...")

    # Option 2: Try loading as ESRI JSON
    query_params = "?where=1=1&outFields=*&returnGeometry=true&f=json"
    full_url = base_url + query_params
    gdf = gpd.read_file(full_url)
    print(f"✓ Successfully loaded {len(gdf)} features")

print(f"Shape: {gdf.shape}")
print(f"Columns: {list(gdf.columns)}")
print(f"\nFirst few rows:")
print(gdf.head())

# Step 2: Configure Ollama
print("\n" + "="*50)
print("Configuring Ollama...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,  # More deterministic
    }
)

# Step 3: Create AI-enabled GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# Step 4: Ask AI to analyze
print("\nAsking AI to plot the data...")
response = gdfai.chat(
    "Plot the administrative boundaries on a map"
)

print("\n" + "="*50)
print("Generated Code:")
print("="*50)
print(gdfai.code)

print("\n" + "="*50)
print("Result:")
print("="*50)
print(response)
