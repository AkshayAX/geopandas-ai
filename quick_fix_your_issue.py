#!/usr/bin/env python3
"""
Quick fix for your issue: Getting a plot instead of data.

THE PROBLEM: You got a GeoDataFrame (data) instead of a plot
THE SOLUTION: Specify return_type=Figure
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')

print("="*70)
print("FIXED VERSION - Getting a Plot Instead of Data")
print("="*70)

# Configure Ollama
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",  # or whatever model you're using
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)

# Load data
print("\nLoading data...")
base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
gdf = gpd.read_file(base_url + query_params)
print(f"✓ Loaded {len(gdf)} features")

# Create AI GeoDataFrame
gdfai = GeoDataFrameAI(gdf)

# THE FIX: Add return_type=Figure to force a plot output
print("\n" + "="*70)
print("Creating plot with return_type=Figure...")
print("="*70)

try:
    # ⭐ THE KEY CHANGE: return_type=Figure
    fig = gdfai.chat(
        "Using matplotlib, create a plot of the administrative boundaries "
        "colored by DISTRICTENG. Include a legend.",
        return_type=Figure  # ← THIS IS THE FIX!
    )

    print(f"\n✓ Success! Got a {type(fig).__name__} object")

    # Save the plot
    fig.savefig('abu_dhabi_districts_FIXED.png', dpi=300, bbox_inches='tight')
    print("✓ Plot saved to 'abu_dhabi_districts_FIXED.png'")

    # Show the generated code
    print("\n" + "="*70)
    print("Generated Code:")
    print("="*70)
    print(gdfai.code)

    print("\n" + "="*70)
    print("EXPLANATION")
    print("="*70)
    print("""
Without return_type=Figure, the LLM might interpret "plot" as:
  - "Show me the data" → Returns GeoDataFrame
  - "Filter and display" → Returns GeoDataFrame

With return_type=Figure, the LLM MUST return a matplotlib Figure object,
so it generates code that creates an actual visualization.

LESSON: Always specify return_type when you want a specific output!
""")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*70)
    print("FALLBACK: Manual plot (without AI)")
    print("="*70)

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12, 10))
    gdf.plot(column='DISTRICTENG', ax=ax, legend=True, cmap='tab20',
             legend_kwds={'bbox_to_anchor': (1.05, 1), 'loc': 'upper left'})
    ax.set_title('Abu Dhabi Administrative Boundaries by District', fontsize=16)
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.savefig('abu_dhabi_districts_MANUAL.png', dpi=300, bbox_inches='tight')
    print("✓ Manual plot saved to 'abu_dhabi_districts_MANUAL.png'")
    plt.close()
