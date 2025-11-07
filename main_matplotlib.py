import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import warnings
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Suppress warnings
warnings.filterwarnings('ignore')

# Step 1: Load data directly from ArcGIS service
print("Loading data from ArcGIS service...")

base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
full_url = base_url + query_params

gdf = gpd.read_file(full_url)
print(f"✓ Successfully loaded {len(gdf)} features")
print(f"Columns available: {list(gdf.columns)[:10]}...")

# Step 2: Configure Ollama with matplotlib-only libraries
print("\n" + "="*60)
print("Configuring Ollama with matplotlib...")
print("="*60)

update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    },
    # Only allow matplotlib, pandas, and geopandas (no folium)
    libraries=["pandas", "matplotlib.pyplot", "geopandas", "contextily"],
)
print("✓ Ollama configured (matplotlib mode)")

# Step 3: Create AI-enabled GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# Step 4: Ask AI with explicit matplotlib instruction
print("\n" + "="*60)
print("Asking AI to create a matplotlib plot...")
print("="*60)
print("(Processing with local LLM - this may take 30-60 seconds...)\n")

try:
    response = gdfai.chat(
        "Use matplotlib to create a static plot showing the administrative boundaries, "
        "with each district (DISTRICTENG) colored differently. Add a legend."
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
        if hasattr(response, 'shape'):
            print(f"Shape: {response.shape}")
        else:
            print(response)

    # Save the plot if one was created
    if plt.get_fignums():
        plt.savefig('abu_dhabi_districts.png', dpi=300, bbox_inches='tight')
        print("\n✓ Plot saved to 'abu_dhabi_districts.png'")
        plt.close()
    else:
        print("\nNote: No matplotlib figure was created")

except Exception as e:
    print(f"\n✗ Error during chat: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*60)
    print("TROUBLESHOOTING:")
    print("="*60)
    print("1. Check Ollama is running: ollama list")
    print("2. Check the model exists: ollama pull llama3.1:8b")
    print("3. Test Ollama: curl http://127.0.0.1:11434/api/tags")
    print("4. Try a simpler prompt")
