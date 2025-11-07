#!/usr/bin/env python3
"""
Continuous Chat Demo: Iteratively improve a map through conversation

This demonstrates the CORE feature of GeoPandas-AI:
- Stateful conversation
- .improve() method for iterative refinement
- Context is maintained across requests
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
print("CONTINUOUS CHAT DEMO: Iteratively Building a Map")
print("="*70)

# Configure
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)

# Load data
print("\nLoading data...")
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
response = requests.get(url, params=params, verify=False)

with open('temp.geojson', 'w') as f:
    json.dump(response.json(), f)

gdf = gpd.read_file('temp.geojson')
gdf_sample = gdf.sample(n=50, random_state=42)  # Small sample for speed
print(f"✓ Loaded {len(gdf_sample)} features")

gdfai = GeoDataFrameAI(gdf_sample)

print("\n" + "="*70)
print("CONVERSATION ROUND 1: Initial Request")
print("="*70)
print("User: 'Create a basic interactive map'\n")

try:
    m1 = gdfai.chat(
        "Create an interactive folium map showing these polygons",
        return_type=folium.Map
    )

    m1.save('conversation_step1_basic.html')
    print("✓ Created basic map → conversation_step1_basic.html")
    print(f"\nCode length: {len(gdfai.code)} characters")

except Exception as e:
    print(f"✗ Error: {e}")
    import sys
    sys.exit(1)

print("\n" + "="*70)
print("CONVERSATION ROUND 2: Add Colors")
print("="*70)
print("User: 'Color the polygons by district'\n")

try:
    m2 = gdfai.improve(
        "Color the polygons by DISTRICTENG column with different colors for each district",
        return_type=folium.Map
    )

    m2.save('conversation_step2_colored.html')
    print("✓ Added colors → conversation_step2_colored.html")
    print(f"Code length: {len(gdfai.code)} characters")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("CONVERSATION ROUND 3: Add Interactivity")
print("="*70)
print("User: 'Add tooltips showing district names'\n")

try:
    m3 = gdfai.improve(
        "Add tooltips that show the DISTRICTENG name when you hover over polygons",
        return_type=folium.Map
    )

    m3.save('conversation_step3_tooltips.html')
    print("✓ Added tooltips → conversation_step3_tooltips.html")
    print(f"Code length: {len(gdfai.code)} characters")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("CONVERSATION ROUND 4: Polish")
print("="*70)
print("User: 'Make it prettier with better styling'\n")

try:
    m4 = gdfai.improve(
        "Improve the styling: use better colors, adjust opacity to 0.6, and add borders",
        return_type=folium.Map
    )

    m4.save('conversation_step4_styled.html')
    print("✓ Styled map → conversation_step4_styled.html")
    print(f"Code length: {len(gdfai.code)} characters")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("CONVERSATION HISTORY")
print("="*70)
print("\nYou can inspect the full conversation:")
gdfai.inspect()

print("\n" + "="*70)
print("VIEW THE EVOLUTION")
print("="*70)
print("""
Open these files in your browser to see how the map improved:

1. conversation_step1_basic.html     - Basic map
2. conversation_step2_colored.html   - + colored by district
3. conversation_step3_tooltips.html  - + tooltips
4. conversation_step4_styled.html    - + better styling

Each step built on the previous one!
""")

print("\n" + "="*70)
print("HOW IT WORKS")
print("="*70)
print("""
The .improve() method:
  1. Keeps context from previous requests
  2. Shows the LLM what code was generated before
  3. Asks it to modify/improve that code
  4. Maintains state across the conversation

This is STATEFUL CONVERSATIONAL PROGRAMMING:
  - You don't start from scratch each time
  - The LLM sees your previous requests
  - It builds incrementally on what exists
  - You guide it conversationally

Compare to traditional coding:
  ❌ Old way: Write all requirements upfront, code entire solution
  ✅ AI way: Start simple, iteratively improve through conversation
""")

print("\n" + "="*70)
print("RESETTING THE CONVERSATION")
print("="*70)
print("""
To start fresh:
  gdfai.reset()  # Clears state and conversation history

Then you can start a new conversation:
  gdfai.chat("Create something completely different")
""")

# Example of reset
print("\nDemonstrating reset...")
gdfai.reset()
print("✓ State cleared")

print("\n" + "="*70)
print("NEW CONVERSATION: After Reset")
print("="*70)
print("User: 'Create a simple matplotlib plot instead'\n")

from matplotlib.figure import Figure

try:
    fig = gdfai.chat(
        "Create a simple matplotlib plot showing the geometries",
        return_type=Figure
    )

    fig.savefig('after_reset_matplotlib.png', dpi=150, bbox_inches='tight')
    print("✓ New conversation started → after_reset_matplotlib.png")
    print("Notice: This is a completely new request, previous map context is gone")

except Exception as e:
    print(f"✗ Error: {e}")

# Cleanup
import os
os.remove('temp.geojson')

print("\n" + "="*70)
print("KEY TAKEAWAYS")
print("="*70)
print("""
1. ✅ YES - Continuous chat is THE main feature!

2. Use .chat() to start, .improve() to continue:
   result = gdfai.chat("initial request")
   result = gdfai.improve("make it better")
   result = gdfai.improve("add more details")
   ...

3. The LLM maintains context across the conversation

4. Use .reset() to start a fresh conversation

5. Use .inspect() to see the conversation history

6. This works for ANY return type:
   - Folium maps (interactive HTML)
   - Matplotlib plots (static PNG)
   - GeoDataFrames (data)
   - Numbers, strings, etc.

7. Each .improve() call:
   - Sees previous code
   - Sees previous prompts
   - Builds on what exists
   - Maintains your conversational context

This is what makes GeoPandas-AI special - it's not just
"run LLM once", it's "have a conversation to build what you want"!
""")
