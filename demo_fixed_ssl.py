#!/usr/bin/env python3
"""
Fixed version that handles SSL certificate issues.
Uses requests library to fetch data first, then loads with geopandas.
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
from matplotlib.figure import Figure
import warnings
import requests
import json
import urllib3

# Suppress warnings
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("="*70)
print("GeoPandas-AI Demo - Fixed SSL Version")
print("="*70)

# Configure Ollama
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)

# Fetch data with requests (handles SSL properly)
print("\nFetching data from Abu Dhabi API...")
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {
    'where': '1=1',
    'outFields': '*',
    'returnGeometry': 'true',
    'f': 'geojson',
    'spatialRel': 'esriSpatialRelIntersects'
}

response = requests.get(url, params=params, verify=False)
geojson_data = response.json()

# Save temporarily
with open('temp_boundaries.geojson', 'w') as f:
    json.dump(geojson_data, f)

# Load with geopandas
gdf = gpd.read_file('temp_boundaries.geojson')
print(f"✓ Loaded {len(gdf)} features")
print(f"✓ Available columns: {', '.join(list(gdf.columns)[:8])}...")

# Create AI GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

print("\n" + "="*70)
print("TEST 1: Create a plot (with return_type=Figure)")
print("="*70)

try:
    fig = gdfai.chat(
        "Using matplotlib, create a plot of the geometries colored by DISTRICTENG column. "
        "Make the figure size 15x12 inches. Add a title 'Abu Dhabi Districts' and a legend.",
        return_type=Figure
    )

    print(f"\n✓ Success! Got {type(fig).__name__}")

    # Show the generated code
    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    # Save the figure
    fig.savefig('test1_districts.png', dpi=300, bbox_inches='tight')
    print("\n✓ Saved to 'test1_districts.png'")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST 2: Improve the plot")
print("="*70)

try:
    improved = gdfai.improve(
        "Use a better colormap (tab20) and make the legend more readable",
        return_type=Figure
    )

    print(f"\n✓ Improved! Got {type(improved).__name__}")
    print("\nImproved code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    improved.savefig('test2_improved.png', dpi=300, bbox_inches='tight')
    print("\n✓ Saved to 'test2_improved.png'")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("TEST 3: Data analysis (no plot)")
print("="*70)

try:
    gdfai.reset()  # Start fresh

    result = gdfai.chat(
        "Show me the unique district names (DISTRICTENG) and count how many features are in each district. "
        "Sort by count descending and return as a DataFrame."
    )

    print(f"\n✓ Got {type(result).__name__}")
    print("\nResult:")
    print(result.head(10))

    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "="*70)
print("DIAGNOSIS: Why was your PNG blank?")
print("="*70)
print("""
Possible reasons for blank PNG:

1. **Too many features (2000)** - Plot might be too dense to see
   Solution: Filter to fewer features first

2. **Wrong CRS/projection** - Geometries might be outside visible bounds
   Solution: Check with gdf.plot() directly first

3. **Legend overlapping** - Legend covers entire plot
   Solution: Adjust legend position or size

4. **LLM didn't set figure size** - Default size too small
   Solution: Explicitly request figure size in prompt

5. **Color mapping issue** - All features same color
   Solution: Check the generated code

Let's test with a simple direct plot to verify the data is OK:
""")

import matplotlib.pyplot as plt
print("\nCreating simple test plot without AI...")
fig, ax = plt.subplots(figsize=(15, 12))
gdf.plot(column='DISTRICTENG', ax=ax, legend=True, cmap='tab20',
         legend_kwds={'bbox_to_anchor': (1.15, 1), 'loc': 'upper left'})
ax.set_title('Abu Dhabi Districts - Direct Plot (No AI)', fontsize=16)
plt.tight_layout()
plt.savefig('test_direct_plot.png', dpi=300, bbox_inches='tight')
print("✓ Saved direct plot to 'test_direct_plot.png'")
plt.close()

print("\nCompare these files:")
print("  - test1_districts.png (AI generated)")
print("  - test2_improved.png (AI improved)")
print("  - test_direct_plot.png (direct matplotlib, no AI)")

# Cleanup
import os
if os.path.exists('temp_boundaries.geojson'):
    os.remove('temp_boundaries.geojson')
