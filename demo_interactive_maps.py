#!/usr/bin/env python3
"""
GeoPandas-AI Interactive Map Demo with Ollama

This shows how to create INTERACTIVE folium maps (not just static matplotlib plots).
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
import warnings
import requests
import json
import urllib3

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("="*70)
print("GeoPandas-AI: Interactive Map Demo")
print("="*70)

# Configure Ollama
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    },
    # Make sure folium is in allowed libraries
    libraries=["pandas", "matplotlib.pyplot", "geopandas", "folium", "contextily"],
)

# Load data
print("\nLoading Abu Dhabi boundaries...")
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
response = requests.get(url, params=params, verify=False)
geojson_data = response.json()

with open('temp.geojson', 'w') as f:
    json.dump(geojson_data, f)

gdf = gpd.read_file('temp.geojson')
print(f"✓ Loaded {len(gdf)} features")

# Take a smaller sample for better performance
print("\nTaking sample of 100 features for better map performance...")
gdf_sample = gdf.sample(n=min(100, len(gdf)), random_state=42)

gdfai = GeoDataFrameAI(gdf_sample)

print("\n" + "="*70)
print("Creating INTERACTIVE folium map")
print("="*70)
print("(This may take 1-2 minutes with local LLM...)\n")

try:
    # ⭐ KEY: Specify return_type=folium.Map for interactive maps!
    interactive_map = gdfai.chat(
        "Create an interactive folium map showing these administrative boundaries. "
        "Color the polygons by DISTRICTENG. Add tooltips showing the district name. "
        "Center the map appropriately.",
        return_type=folium.Map  # ⭐ THIS creates an interactive map!
    )

    print(f"\n✓ Success! Got {type(interactive_map).__name__}")

    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    # Save the interactive map
    interactive_map.save('interactive_map.html')
    print("\n✓ Interactive map saved to 'interactive_map.html'")
    print("  Open this file in your web browser to explore the map!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*70)
    print("FALLBACK: Creating interactive map manually")
    print("="*70)

    # Manual fallback
    center_lat = gdf_sample.geometry.centroid.y.mean()
    center_lon = gdf_sample.geometry.centroid.x.mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

    # Add GeoDataFrame to map
    folium.GeoJson(
        gdf_sample,
        name='Districts',
        style_function=lambda x: {
            'fillColor': 'blue',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.3,
        },
        tooltip=folium.GeoJsonTooltip(fields=['DISTRICTENG'], aliases=['District:'])
    ).add_to(m)

    m.save('interactive_map_manual.html')
    print("✓ Manual interactive map saved to 'interactive_map_manual.html'")

print("\n" + "="*70)
print("Improving the map")
print("="*70)

try:
    improved_map = gdfai.improve(
        "Add a layer control and make the colors more distinct",
        return_type=folium.Map
    )

    print(f"\n✓ Improved! Got {type(improved_map).__name__}")
    improved_map.save('interactive_map_improved.html')
    print("✓ Improved map saved to 'interactive_map_improved.html'")

except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "="*70)
print("COMPARISON: Static vs Interactive")
print("="*70)

from matplotlib.figure import Figure

print("\nCreating static matplotlib plot for comparison...")

try:
    gdfai.reset()

    static_fig = gdfai.chat(
        "Create a static matplotlib plot colored by DISTRICTENG",
        return_type=Figure
    )

    static_fig.savefig('static_plot_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Static plot saved to 'static_plot_comparison.png'")

except Exception as e:
    print(f"✗ Static plot error: {e}")

print("\n" + "="*70)
print("SUMMARY: Two Types of Maps")
print("="*70)
print("""
GeoPandas-AI supports TWO types of visualizations:

1. STATIC PLOTS (matplotlib):
   - return_type=Figure
   - Saved as PNG/PDF
   - Good for reports, papers, presentations
   - Example: gdfai.chat("Plot the data", return_type=Figure)

2. INTERACTIVE MAPS (folium):
   - return_type=folium.Map
   - Saved as HTML
   - Zoomable, pannable, clickable
   - Good for web apps, exploration, dashboards
   - Example: gdfai.chat("Create interactive map", return_type=folium.Map)

Files created:
  📊 static_plot_comparison.png  - Static image
  🗺️  interactive_map.html        - Interactive web map (OPEN IN BROWSER!)
  🗺️  interactive_map_improved.html - Improved version

To view the interactive maps:
  firefox interactive_map.html
  # or
  google-chrome interactive_map.html
  # or just double-click the .html file
""")

# Cleanup
import os
if os.path.exists('temp.geojson'):
    os.remove('temp.geojson')

print("\n" + "="*70)
print("TIPS for Interactive Maps")
print("="*70)
print("""
1. Always specify return_type=folium.Map for interactive maps

2. For better performance with large datasets:
   - Sample the data first: gdf.sample(n=100)
   - Or filter to specific areas

3. You can layer multiple datasets:
   gdfai.chat("Add highways layer", other_gdf, return_type=folium.Map)

4. Folium maps are HTML - can be embedded in web apps, Jupyter, etc.

5. If the LLM has trouble with folium:
   - qwen2.5-coder and deepseek-coder are best
   - Use very explicit prompts
   - Or use a cloud model for complex maps
""")
