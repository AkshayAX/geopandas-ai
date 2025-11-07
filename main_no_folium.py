import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import warnings
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Suppress warnings
warnings.filterwarnings('ignore')

# Step 1: Load data
print("Loading data from ArcGIS service...")
base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
full_url = base_url + query_params

gdf = gpd.read_file(full_url)
print(f"✓ Successfully loaded {len(gdf)} features")

# Step 2: Configure Ollama - EXCLUDE folium explicitly
print("\n" + "="*60)
print("Configuring Ollama...")
print("="*60)

update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    },
    # IMPORTANT: Explicitly remove folium from allowed libraries
    # This prevents the LLM from trying to use it
    libraries=["pandas", "matplotlib.pyplot", "geopandas"],
)
print("✓ Configured (matplotlib only - no folium)")

# Step 3: Create AI-enabled GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# Step 4: Very explicit prompt to use matplotlib
print("\n" + "="*60)
print("Generating code with LLM...")
print("="*60)
print("(This may take 30-60 seconds...)\n")

try:
    response = gdfai.chat(
        "Using ONLY matplotlib.pyplot (imported as plt), create a simple plot of the geometry. "
        "Color each polygon by DISTRICTENG column. "
        "Use gdf.plot(column='DISTRICTENG', legend=True, figsize=(12,10)). "
        "Return the matplotlib Figure object."
    )

    print("\n" + "="*60)
    print("SUCCESS! Generated Code:")
    print("="*60)
    print(gdfai.code)

    print("\n" + "="*60)
    print("Result:")
    print("="*60)
    print(f"Type: {type(response)}")

    # Save the figure
    import matplotlib.pyplot as plt
    if plt.get_fignums():
        plt.savefig('abu_dhabi_map.png', dpi=300, bbox_inches='tight')
        print("✓ Plot saved to 'abu_dhabi_map.png'")
        plt.close()

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*60)
    print("Trying simpler approach without AI...")
    print("="*60)

    # Fallback: just plot it directly
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(column='DISTRICTENG', ax=ax, legend=True, cmap='tab20')
    ax.set_title('Abu Dhabi Administrative Boundaries')
    plt.savefig('abu_dhabi_map_fallback.png', dpi=300, bbox_inches='tight')
    print("✓ Created fallback plot: abu_dhabi_map_fallback.png")
    plt.close()
