#!/usr/bin/env python3
"""
Practical Example: Interactive Workflow with GeoPandas-AI

This simulates a real-world workflow where you iteratively
refine a map through conversation, like chatting with an assistant.
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

# Configure once
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
    }
)

# Load your data
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
response = requests.get(url, params=params, verify=False)

with open('temp.geojson', 'w') as f:
    json.dump(response.json(), f)

gdf = gpd.read_file('temp.geojson').sample(n=50, random_state=42)

# Wrap with AI capabilities
gdfai = GeoDataFrameAI(gdf)

print("="*70)
print("INTERACTIVE WORKFLOW EXAMPLE")
print("="*70)
print("\nImagine you're exploring your data and want to create a map.")
print("You can refine it step-by-step through conversation:\n")

# Start simple
print("YOU: 'Show me a map of this data'")
print("-" * 70)

try:
    map_v1 = gdfai.chat(
        "Create an interactive map",
        return_type=folium.Map
    )
    map_v1.save('workflow_v1.html')
    print("✓ Created basic map\n")

    # Look at it, not satisfied, improve it
    print("YOU: 'Actually, can you color it by district?'")
    print("-" * 70)

    map_v2 = gdfai.improve(
        "Color polygons by DISTRICTENG",
        return_type=folium.Map
    )
    map_v2.save('workflow_v2.html')
    print("✓ Added district colors\n")

    # Still want more
    print("YOU: 'Add labels so I know which district is which'")
    print("-" * 70)

    map_v3 = gdfai.improve(
        "Add tooltips showing district names",
        return_type=folium.Map
    )
    map_v3.save('workflow_v3.html')
    print("✓ Added tooltips\n")

    # Final touch
    print("YOU: 'Make it look nicer'")
    print("-" * 70)

    map_v4 = gdfai.improve(
        "Improve styling with better colors and borders",
        return_type=folium.Map
    )
    map_v4.save('workflow_final.html')
    print("✓ Polished the map\n")

    print("="*70)
    print("FINAL RESULT")
    print("="*70)
    print("\n✓ Your final map: workflow_final.html")
    print("\nGenerated code:")
    print("-" * 70)
    print(gdfai.code)
    print("-" * 70)

    print("\n" + "="*70)
    print("WHAT JUST HAPPENED?")
    print("="*70)
    print("""
You had a CONVERSATION with your data:
  1. Started with a simple request
  2. Saw the result, wanted improvements
  3. Asked for each improvement naturally
  4. Got a polished map without writing any matplotlib/folium code!

This is the power of GeoPandas-AI:
  ✓ No need to know folium API
  ✓ No need to know matplotlib details
  ✓ Just describe what you want
  ✓ Iteratively refine until satisfied
  ✓ Save final code for reuse

Open workflow_final.html to see your interactive map!
""")

    # You can also save the code for later
    print("\n" + "="*70)
    print("SAVE THE CODE FOR REUSE")
    print("="*70)

    gdfai.inject("create_district_map", ai_module="my_maps")
    print("""
✓ Code saved as a function!

Now you can reuse it:
  from my_maps import create_district_map
  new_map = create_district_map(my_geodataframe)
""")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nNote: This workflow works best with good models (qwen2.5-coder, cloud APIs)")

# Cleanup
import os
os.remove('temp.geojson')

print("\n" + "="*70)
print("TIPS FOR CONTINUOUS CHAT")
print("="*70)
print("""
1. Start simple, improve iteratively
   ❌ Bad: "Create perfect map with colors, tooltips, legend, basemap"
   ✅ Good: Start basic, add features one by one with .improve()

2. Be specific in improvements
   ❌ "Make it better"
   ✅ "Add tooltips showing the district name"

3. Use .inspect() to see what the AI remembers
   gdfai.inspect()

4. Use .reset() if you want to start over
   gdfai.reset()

5. Local models are slower but you can iterate offline!
   - Each .improve() takes 30-60 seconds
   - But you maintain full control and privacy

6. The state persists across .improve() calls
   - Previous code is remembered
   - Previous prompts are in context
   - It's a real conversation!
""")
