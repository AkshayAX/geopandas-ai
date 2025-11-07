import requests
import json
from geopandasai import read_file, update_geopandasai_config
import urllib3
import warnings

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Step 1: Fetch Abu Dhabi boundaries data
print("Fetching data from API...")
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {
    'where': '1=1',
    'outFields': '*',
    'returnGeometry': 'true',
    'f': 'geojson',
    'spatialRel': 'esriSpatialRelIntersects'
}

response = requests.get(url, params=params, verify=False)

if response.status_code != 200:
    raise Exception(f"API request failed: {response.status_code}")

geojson_data = response.json()

# Validate response
if 'features' not in geojson_data:
    raise Exception("Invalid GeoJSON response - no features found")

print(f"✓ Fetched {len(geojson_data['features'])} features")

# Save to file
filename = 'admin_boundaries.geojson'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(geojson_data, f)
print(f"✓ Saved to {filename}")

# Step 2: Configure GeoPandas-AI to use Ollama
print("\nConfiguring Ollama...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)
print("✓ Ollama configured")

# Step 3: Read the file
print(f"\nReading {filename}...")
gdfai = read_file(filename)
print(f"✓ Loaded {len(gdfai)} features")
print(f"Columns: {list(gdfai.columns)[:10]}...")

# Step 4: Chat with AI
print("\n" + "="*60)
print("Asking AI to create visualization...")
print("="*60)
print("(Processing with local LLM - this may take a minute...)\n")

try:
    response = gdfai.chat(
        "Plot the administrative boundaries colored by DISTRICTENG"
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
        print("Plot created successfully!")

    # Save the plot
    import matplotlib.pyplot as plt
    plt.savefig('admin_boundaries_plot.png', dpi=300, bbox_inches='tight')
    print("\n✓ Plot saved to 'admin_boundaries_plot.png'")

except Exception as e:
    print(f"\n✗ Error during chat: {e}")
    import traceback
    traceback.print_exc()
