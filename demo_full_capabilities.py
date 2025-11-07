#!/usr/bin/env python3
"""
Comprehensive example showing ALL capabilities of GeoPandas-AI with Ollama.

This demonstrates:
1. Data filtering and analysis
2. Visualization creation
3. Iterative refinement with .improve()
4. Spatial operations
5. Multi-dataframe queries
6. Code inspection
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')

# Configure Ollama with a code-specialized model
print("="*70)
print("GeoPandas-AI Full Capabilities Demo")
print("="*70)

update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",  # Better than llama3.1
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    }
)
print("✓ Configured with qwen2.5-coder:14b")

# Load data
print("\nLoading Abu Dhabi administrative boundaries...")
base_url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
query_params = "?where=1=1&outFields=*&returnGeometry=true&f=geojson"
gdf = gpd.read_file(base_url + query_params)
print(f"✓ Loaded {len(gdf)} features")
print(f"✓ Columns include: {', '.join(list(gdf.columns)[:8])}...")

# Create AI-enabled GeoDataFrame
gdfai = GeoDataFrameAI(gdf, description="Abu Dhabi administrative boundaries with districts and communities")

print("\n" + "="*70)
print("CAPABILITY 1: Data Analysis & Filtering")
print("="*70)

# Example 1: Filter data (returns GeoDataFrame)
print("\nQuery: 'Find the top 5 largest districts by area'")
try:
    top5 = gdfai.chat("Calculate the area of each feature and return the top 5 largest districts")
    print(f"\n✓ Result type: {type(top5).__name__}")
    print(f"✓ Returned {len(top5)} features")
    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("CAPABILITY 2: Visualization (EXPLICIT return_type)")
print("="*70)

# Example 2: Create a plot - MUST specify return_type=Figure
print("\nQuery: 'Create a matplotlib plot colored by district'")
print("(Forcing return_type=Figure to ensure we get a plot)")

try:
    # Reset state for new query
    gdfai.reset()

    fig = gdfai.chat(
        "Using matplotlib, create a plot showing the boundaries colored by DISTRICTENG. "
        "Add a legend and title 'Abu Dhabi Districts'.",
        return_type=Figure  # ⭐ CRITICAL: Specify we want a Figure, not data!
    )

    print(f"\n✓ Result type: {type(fig).__name__}")
    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    # Save the plot
    fig.savefig('districts_plot.png', dpi=300, bbox_inches='tight')
    print("\n✓ Plot saved to 'districts_plot.png'")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("CAPABILITY 3: Iterative Refinement with .improve()")
print("="*70)

# Example 3: Improve the previous result
print("\nUsing .improve() to refine the plot...")

try:
    improved_fig = gdfai.improve(
        "Make the figure bigger (15x12 inches) and use a better colormap",
        return_type=Figure
    )

    print(f"\n✓ Improved! Result type: {type(improved_fig).__name__}")
    print("\nImproved code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

    improved_fig.savefig('districts_plot_improved.png', dpi=300, bbox_inches='tight')
    print("\n✓ Improved plot saved to 'districts_plot_improved.png'")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("CAPABILITY 4: Code Inspection & Reuse")
print("="*70)

# Example 4: Inspect and inject generated code
print("\nInspect the conversation history:")
gdfai.inspect()

print("\nInject generated code as a reusable function:")
try:
    gdfai.inject("plot_districts", ai_module="my_geo_functions")
    print("✓ Code injected! You can now use:")
    print("  from my_geo_functions import plot_districts")
    print("  result = plot_districts(gdf)")
except Exception as e:
    print(f"Note: {e}")

print("\n" + "="*70)
print("CAPABILITY 5: Spatial Analysis")
print("="*70)

# Example 5: Spatial calculations
print("\nQuery: 'Calculate the total area covered by each district'")

try:
    gdfai.reset()  # Start fresh

    area_summary = gdfai.chat(
        "Group by DISTRICTENG and calculate the total area in square kilometers. "
        "Return a GeoDataFrame with DISTRICTENG and total_area_km2 columns, sorted by area descending."
    )

    print(f"\n✓ Result type: {type(area_summary).__name__}")
    print(f"✓ Shape: {area_summary.shape}")
    print("\nTop 5 districts by area:")
    print(area_summary.head())

    print("\nGenerated code:")
    print("-" * 60)
    print(gdfai.code)
    print("-" * 60)

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "="*70)
print("KEY LESSONS")
print("="*70)
print("""
1. **Specify return_type** to control output:
   - return_type=Figure → Get a matplotlib plot
   - return_type=GeoDataFrame → Get filtered/processed data (default)
   - return_type=int/float/str → Get calculations

2. **Use .improve()** for iterative refinement:
   - Don't start over, refine what you have
   - Builds on previous context

3. **Use .inspect()** to see the conversation history

4. **Use .inject()** to save generated code as reusable functions

5. **Use .reset()** to start a fresh conversation

6. **The LLM generates Python code** - you can see it with gdfai.code

7. **For plots, be explicit**:
   - Good: "Using matplotlib, create a plot...", return_type=Figure
   - Bad: "Plot the data" (might return data instead)
""")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"""
GeoPandas-AI is a CONVERSATIONAL INTERFACE to geospatial analysis.

It generates Python code based on natural language, allowing you to:
- Ask questions about your data
- Create visualizations without writing matplotlib code
- Perform spatial analysis without remembering GeoPandas syntax
- Iterate and refine results conversationally
- Reuse generated code in your projects

The key is using the right prompts and specifying return_type!
""")

print("\nCheck the generated plots:")
print("  - districts_plot.png")
print("  - districts_plot_improved.png")
