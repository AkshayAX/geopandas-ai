#!/usr/bin/env python3
"""
Command-Line Chat Interface for GeoPandas-AI

Simple terminal-based chat - no web browser needed!
Just type your prompts and see results.
"""

import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import warnings
import requests
import json
import urllib3
import webbrowser
import os

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_banner():
    print("="*70)
    print("🗺️  GeoPandas-AI Command-Line Chat")
    print("="*70)
    print("Type your requests and I'll generate maps/analysis for you!")
    print("\nCommands:")
    print("  - Type your request normally to chat")
    print("  - 'map' - switch to interactive map mode")
    print("  - 'plot' - switch to static plot mode")
    print("  - 'data' - switch to data analysis mode")
    print("  - 'code' - show generated code")
    print("  - 'reset' - start fresh conversation")
    print("  - 'quit' - exit")
    print("="*70)

def main():
    print_banner()

    # Load data
    print("\n📥 Loading data...")
    url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
    params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}

    response = requests.get(url, params=params, verify=False)
    with open('temp_cli.geojson', 'w') as f:
        json.dump(response.json(), f)

    gdf = gpd.read_file('temp_cli.geojson')
    gdf_sample = gdf.sample(n=50, random_state=42)
    print(f"✓ Loaded {len(gdf_sample)} features")

    # Configure
    update_geopandasai_config(
        lite_llm_config={
            "model": "openai/qwen2.5-coder:14b",
            "api_base": "http://127.0.0.1:11434/v1",
            "api_key": "ollama",
        }
    )

    gdfai = GeoDataFrameAI(gdf_sample)

    # Chat state
    output_mode = "map"  # map, plot, or data
    conversation_count = 0
    map_count = 0
    plot_count = 0

    print("\n✨ Ready! Current mode: Interactive Map")
    print("💬 Type your first request:\n")

    while True:
        try:
            # Get input
            user_input = input("YOU: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == 'quit':
                print("\n👋 Goodbye!")
                break

            elif user_input.lower() == 'map':
                output_mode = "map"
                print("✓ Switched to Interactive Map mode\n")
                continue

            elif user_input.lower() == 'plot':
                output_mode = "plot"
                print("✓ Switched to Static Plot mode\n")
                continue

            elif user_input.lower() == 'data':
                output_mode = "data"
                print("✓ Switched to Data Analysis mode\n")
                continue

            elif user_input.lower() == 'code':
                if hasattr(gdfai, 'code'):
                    print("\n" + "="*70)
                    print("Generated Code:")
                    print("="*70)
                    print(gdfai.code)
                    print("="*70 + "\n")
                else:
                    print("❌ No code generated yet. Make a request first!\n")
                continue

            elif user_input.lower() == 'reset':
                gdfai.reset()
                conversation_count = 0
                print("✓ Conversation reset!\n")
                continue

            # Process the request
            print(f"\n🤖 AI: Processing... (this may take 30-60 seconds)")

            try:
                # Determine return type
                if output_mode == "map":
                    return_type = folium.Map
                elif output_mode == "plot":
                    return_type = Figure
                else:
                    return_type = None

                # Use improve if this is a follow-up
                if conversation_count == 0:
                    result = gdfai.chat(user_input, return_type=return_type)
                else:
                    result = gdfai.improve(user_input, return_type=return_type)

                conversation_count += 1

                # Handle result based on type
                if output_mode == "map":
                    map_count += 1
                    filename = f'chat_map_{map_count}.html'
                    result.save(filename)
                    print(f"✓ Interactive map saved to '{filename}'")

                    # Try to open in browser
                    try:
                        webbrowser.open(f'file://{os.path.abspath(filename)}')
                        print("✓ Opening in browser...")
                    except:
                        print(f"  Open it manually: {os.path.abspath(filename)}")

                elif output_mode == "plot":
                    plot_count += 1
                    filename = f'chat_plot_{plot_count}.png'
                    result.savefig(filename, dpi=150, bbox_inches='tight')
                    print(f"✓ Plot saved to '{filename}'")
                    plt.close()

                else:  # data mode
                    print("\n" + "="*70)
                    print("Result:")
                    print("="*70)
                    print(result)
                    print("="*70)

                print()

            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Try rephrasing your request or switch output mode.\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break

        except EOFError:
            break

    # Cleanup
    if os.path.exists('temp_cli.geojson'):
        os.remove('temp_cli.geojson')

if __name__ == "__main__":
    main()
