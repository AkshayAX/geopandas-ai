#!/usr/bin/env python3
"""Quick example: Create an interactive folium map with GeoPandas-AI"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
import warnings
import requests
import json
import urllib3

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Creating interactive map with GeoPandas-AI + Ollama...\n")

# Configure
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
    }
)

# Load data (with SSL workaround)
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
response = requests.get(url, params=params, verify=False)

with open('temp.geojson', 'w') as f:
    json.dump(response.json(), f)

gdf = gpd.read_file('temp.geojson')
print(f"✓ Loaded {len(gdf)} features")

# Take sample for better performance
gdf_sample = gdf.sample(n=100, random_state=42)
gdfai = GeoDataFrameAI(gdf_sample)

print("\nGenerating interactive map (this takes 1-2 minutes)...")

try:
    # ⭐ THE KEY: return_type=folium.Map
    m = gdfai.chat(
        "Create an interactive folium map with these polygons colored by DISTRICTENG",
        return_type=folium.Map
    )

    m.save('my_interactive_map.html')
    print("\n✓ SUCCESS! Interactive map saved to 'my_interactive_map.html'")
    print("  Open this file in your web browser to explore!")

    print("\nGenerated code:")
    print(gdfai.code)

except Exception as e:
    print(f"\n✗ Error: {e}\n")
    print("Creating manual fallback map...")

    # Simple fallback
    center = [gdf_sample.geometry.centroid.y.mean(), gdf_sample.geometry.centroid.x.mean()]
    m = folium.Map(location=center, zoom_start=10)
    folium.GeoJson(gdf_sample).add_to(m)
    m.save('my_interactive_map.html')
    print("✓ Fallback map saved to 'my_interactive_map.html'")

# Cleanup
import os
os.remove('temp.geojson')

print("\n" + "="*60)
print("COMPARISON:")
print("="*60)
print("Static matplotlib plot:  return_type=Figure     → PNG file")
print("Interactive folium map:  return_type=folium.Map → HTML file")
