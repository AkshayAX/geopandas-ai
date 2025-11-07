#!/usr/bin/env python3
"""
Debug why the PNG is blank.
This script shows the generated code and creates comparison plots.
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
from matplotlib.figure import Figure
import warnings
import requests
import json
import urllib3
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("="*70)
print("DEBUGGING BLANK PNG ISSUE")
print("="*70)

# Load data
print("\n1. Fetching data...")
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
response = requests.get(url, params=params, verify=False)
geojson_data = response.json()

with open('temp.geojson', 'w') as f:
    json.dump(geojson_data, f)

gdf = gpd.read_file('temp.geojson')
print(f"✓ Loaded {len(gdf)} features")
print(f"✓ CRS: {gdf.crs}")
print(f"✓ Bounds: {gdf.total_bounds}")
print(f"✓ Columns: {list(gdf.columns)}")

# Test 1: Direct matplotlib plot (no AI)
print("\n" + "="*70)
print("TEST 1: Direct matplotlib plot (baseline)")
print("="*70)

fig, ax = plt.subplots(figsize=(12, 10))
gdf.plot(ax=ax, column='DISTRICTENG', legend=True, cmap='tab20')
ax.set_title('Direct Plot - No AI')
plt.savefig('DEBUG_direct_plot.png', dpi=150, bbox_inches='tight')
print("✓ Saved: DEBUG_direct_plot.png")
plt.close()

# Configure AI
print("\n2. Configuring Ollama...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)

gdfai = GeoDataFrameAI(gdf)

# Test 2: AI-generated plot
print("\n" + "="*70)
print("TEST 2: AI-generated plot")
print("="*70)
print("Asking AI to create plot...")

try:
    fig = gdfai.chat(
        "Create a matplotlib plot showing the geometries colored by DISTRICTENG. "
        "Use figsize (12, 10), add a legend, and use colormap 'tab20'. "
        "Set title to 'AI Generated Plot'.",
        return_type=Figure
    )

    print(f"\n✓ Got: {type(fig)}")

    # IMPORTANT: Show the generated code
    print("\n" + "="*70)
    print("GENERATED CODE:")
    print("="*70)
    print(gdfai.code)
    print("="*70)

    # Save
    fig.savefig('DEBUG_ai_plot.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: DEBUG_ai_plot.png")

    # Analyze the figure
    print("\n" + "="*70)
    print("FIGURE ANALYSIS:")
    print("="*70)
    print(f"Figure size: {fig.get_size_inches()}")
    print(f"Number of axes: {len(fig.get_axes())}")

    if len(fig.get_axes()) > 0:
        ax = fig.get_axes()[0]
        print(f"Axes xlim: {ax.get_xlim()}")
        print(f"Axes ylim: {ax.get_ylim()}")
        print(f"Has legend: {ax.get_legend() is not None}")
        print(f"Number of children: {len(ax.get_children())}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Simpler prompt
print("\n" + "="*70)
print("TEST 3: Very simple prompt")
print("="*70)

try:
    gdfai.reset()

    fig = gdfai.chat(
        "Plot the data using gdf.plot()",
        return_type=Figure
    )

    print("\n✓ Got figure")
    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    fig.savefig('DEBUG_simple_prompt.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: DEBUG_simple_prompt.png")

except Exception as e:
    print(f"\n✗ Error: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
Compare these files to diagnose the issue:

1. DEBUG_direct_plot.png    - Baseline (matplotlib without AI)
2. DEBUG_ai_plot.png         - AI-generated with detailed prompt
3. DEBUG_simple_prompt.png   - AI-generated with simple prompt

Check:
- Are all files the same size?
- Is the AI plot actually blank or just different?
- Does the generated code look correct?
- Are there any obvious bugs in the generated code?

Common issues:
- LLM forgets to call plt.figure() or creates figure incorrectly
- LLM doesn't set axis limits properly
- LLM creates plot but doesn't add to figure
- Legend positioning covers the plot
""")

# Cleanup
import os
os.remove('temp.geojson')

print("\nNext steps:")
print("1. Open the DEBUG_*.png files and compare them")
print("2. Review the 'GENERATED CODE' above")
print("3. If AI code has bugs, try a different model or simpler prompt")
