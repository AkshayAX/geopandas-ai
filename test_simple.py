#!/usr/bin/env python3
"""Simple test to verify Ollama + geopandas-ai works with basic data."""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
from shapely.geometry import Point
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

print("="*60)
print("Simple Test: Ollama + geopandas-ai")
print("="*60)

# Create a simple test GeoDataFrame
print("\n1. Creating test data...")
data = {
    'name': ['Point A', 'Point B', 'Point C'],
    'value': [10, 20, 30],
    'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)]
}
gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")
print(f"✓ Created GeoDataFrame with {len(gdf)} points")
print(gdf)

# Configure Ollama WITHOUT folium
print("\n2. Configuring Ollama (matplotlib only)...")
update_geopandasai_config(
    lite_llm_config={
        "model": "openai/llama3.1:8b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,
    },
    libraries=["pandas", "matplotlib.pyplot", "geopandas"],  # NO folium!
)
print("✓ Configured")

# Create AI-enabled GeoDataFrame
print("\n3. Creating GeoDataFrameAI...")
gdfai = GeoDataFrameAI(gdf)
print("✓ Created")

# Simple test: filter data
print("\n4. Testing with simple query...")
print("Prompt: 'Filter rows where value > 15 and return the result'")
print("(This may take 30-60 seconds...)\n")

try:
    result = gdfai.chat(
        "Filter rows where value > 15 and return the result as a GeoDataFrame"
    )

    print("\n" + "="*60)
    print("SUCCESS!")
    print("="*60)
    print("\nGenerated Code:")
    print("-"*60)
    print(gdfai.code)
    print("-"*60)

    print("\nResult:")
    print(result)

    print("\n✓ Test passed! Ollama integration is working.")

except Exception as e:
    print("\n" + "="*60)
    print("ERROR")
    print("="*60)
    print(f"\nError: {e}")

    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

    print("\n" + "="*60)
    print("DEBUGGING INFO")
    print("="*60)
    print("\nThis error might be caused by:")
    print("1. LLM generating invalid Python code")
    print("2. LLM forgetting to import libraries")
    print("3. LLM returning wrong return type")
    print("\nTry:")
    print("- Using a different model (e.g., llama3:latest)")
    print("- Simplifying the prompt")
    print("- Checking Ollama logs")
