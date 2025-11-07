import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import warnings

warnings.filterwarnings('ignore')

# Load data
print("Loading Abu Dhabi boundaries...")
base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
gdf = gpd.read_file(base_url + query_params)
print(f"✓ Loaded {len(gdf)} features")

# Configure with Qwen2.5-Coder (better at code generation than llama3.1)
print("\nConfiguring Ollama with qwen2.5-coder...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)
print("✓ Configured")

# Create AI GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# Ask for visualization
print("\nGenerating visualization code...")
print("(This may take 30-60 seconds with local model...)\n")

try:
    response = gdfai.chat(
        "Plot the administrative boundaries colored by DISTRICTENG"
    )

    print("\n" + "="*60)
    print("Generated Code:")
    print("="*60)
    print(gdfai.code)

    print("\n✓ Success! Check for output file or display.")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nIf qwen2.5-coder:14b isn't installed:")
    print("  ollama pull qwen2.5-coder:14b")
    print("\nOr try a different model:")
    print("  ollama pull deepseek-coder:6.7b")
