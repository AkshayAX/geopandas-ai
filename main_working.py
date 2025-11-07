import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Step 1: Load data directly from ArcGIS service
print("Loading data from ArcGIS service...")

base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
full_url = base_url + query_params

gdf = gpd.read_file(full_url)
print(f"✓ Successfully loaded {len(gdf)} features")
print(f"Columns: {list(gdf.columns)[:10]}...")  # Show first 10 columns

# Step 2: Configure Ollama
print("\n" + "="*60)
print("Configuring Ollama...")
print("="*60)

update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)
print("✓ Ollama configured with llama3.1:8b")

# Step 3: Create AI-enabled GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# Step 4: Ask AI to analyze
print("\n" + "="*60)
print("Asking AI to create a plot...")
print("="*60)
print("(This may take a minute as the local LLM processes the request...)\n")

try:
    response = gdfai.chat(
        "Create a plot showing the administrative boundaries colored by DISTRICTENG"
    )

    print("\n" + "="*60)
    print("GENERATED CODE:")
    print("="*60)
    print(gdfai.code)

    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    if response is not None:
        print(f"Type: {type(response)}")
        print(response)
    else:
        print("Plot was created successfully!")
        print("Check if a plot window opened or a file was saved.")

    # Optionally save the plot
    print("\n" + "="*60)
    print("Saving plot to 'output.png'...")
    print("="*60)
    import matplotlib.pyplot as plt
    plt.savefig('output.png', dpi=300, bbox_inches='tight')
    print("✓ Plot saved to output.png")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Make sure the model is available: ollama list")
    print("3. Try pulling the model: ollama pull llama3.1:8b")
