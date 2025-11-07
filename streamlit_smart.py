#!/usr/bin/env python3
"""
Smart Streamlit Chat - Filters and highlights query-specific results

This version ensures the LLM:
1. Filters data based on your query
2. Zooms to relevant areas
3. Highlights results differently from other data

Usage:
    streamlit run streamlit_smart.py
"""

import streamlit as st
import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
from folium import plugins
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import warnings
import requests
import json
import urllib3

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GeoPandas-AI Smart Chat", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI Smart Chat")
st.markdown("Ask about specific locations, districts, or areas!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    ollama_model = st.text_input("Ollama Model", value="openai/qwen2.5-coder:14b")

    output_type = st.radio("Output Type", ["Interactive Map", "Static Plot", "Data Analysis"])

    sample_size = st.slider("Sample Size", 10, 500, 100)

    if st.button("🔄 Reset"):
        if 'gdfai' in st.session_state:
            st.session_state.gdfai.reset()
            st.session_state.messages = []
            st.session_state.chat_counter = 0
            st.rerun()

# Initialize
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_counter' not in st.session_state:
    st.session_state.chat_counter = 0

if 'gdfai' not in st.session_state:
    with st.spinner("📥 Loading data..."):
        update_geopandasai_config(
            lite_llm_config={
                "model": ollama_model,
                "api_base": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
            }
        )

        url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
        params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}

        response = requests.get(url, params=params, verify=False)
        with open('temp_st.geojson', 'w') as f:
            json.dump(response.json(), f)

        gdf = gpd.read_file('temp_st.geojson')
        gdf_sample = gdf.sample(n=min(sample_size, len(gdf)), random_state=42)

        st.session_state.gdfai = GeoDataFrameAI(gdf_sample)
        st.session_state.gdf_full = gdf_sample

        # Get unique districts for reference
        unique_districts = sorted(gdf['DISTRICTENG'].dropna().unique())
        st.session_state.districts = unique_districts

        st.sidebar.success(f"✓ Loaded {len(gdf_sample)} features")
        st.sidebar.info(f"📍 {len(unique_districts)} unique districts")

# Show available districts
with st.sidebar:
    with st.expander("📋 Available Districts"):
        if 'districts' in st.session_state:
            for district in st.session_state.districts[:20]:  # Show first 20
                st.text(f"• {district}")
            if len(st.session_state.districts) > 20:
                st.text(f"... and {len(st.session_state.districts) - 20} more")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])
        if "map_html" in msg:
            st.components.v1.html(msg["map_html"], height=600, scrolling=True)
        elif "plot_path" in msg:
            st.image(msg["plot_path"])
        elif "dataframe" in msg:
            st.dataframe(msg["dataframe"], use_container_width=True)

# Chat input
user_input = st.chat_input("Ask about specific locations or districts...")

if user_input:
    st.session_state.messages.append({"role": "user", "text": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status = st.empty()
        status.markdown("🤖 Processing your query...")

        try:
            # Create smart prompt based on query type
            enhanced_prompt = user_input

            if output_type == "Interactive Map":
                # Check if asking about specific location/district
                query_lower = user_input.lower()

                # Keywords that suggest filtering
                filter_keywords = ['show', 'find', 'where', 'which', 'locate', 'highlight']
                location_keywords = ['district', 'area', 'block', 'community', 'zone']

                is_location_query = any(kw in query_lower for kw in filter_keywords + location_keywords)

                if is_location_query and st.session_state.chat_counter == 0:
                    # First message asking about specific location
                    enhanced_prompt = f"""
{user_input}

IMPORTANT INSTRUCTIONS:
1. FILTER the GeoDataFrame to show ONLY the features matching the query
2. Create a folium map centered on the filtered results
3. If showing specific districts, color them DIFFERENTLY from background
4. Zoom the map to fit ONLY the filtered features (use .total_bounds)
5. Add tooltips showing DISTRICTENG and COMMUNITYENG fields
6. Add a fullscreen control button

Example approach:
- Filter: filtered = df_1[df_1['DISTRICTENG'].str.contains('query', case=False, na=False)]
- Get bounds: bounds = filtered.total_bounds
- Center map on filtered area
- Show filtered features in bright color, rest in grey/transparent
"""
                elif is_location_query:
                    # Follow-up about location
                    enhanced_prompt = f"{user_input}. Remember to filter the data and zoom to the relevant area."
                else:
                    # General map request
                    enhanced_prompt = f"{user_input}. Add tooltips showing district and community names, and include a fullscreen button."

            # Determine return type
            if output_type == "Interactive Map":
                return_type = folium.Map
            elif output_type == "Static Plot":
                return_type = Figure
            else:
                return_type = None

            # Generate
            is_first = st.session_state.chat_counter == 0

            if is_first:
                result = st.session_state.gdfai.chat(enhanced_prompt, return_type=return_type)
            else:
                result = st.session_state.gdfai.improve(enhanced_prompt, return_type=return_type)

            st.session_state.chat_counter += 1
            status.empty()

            # Display result
            response_msg = {"role": "assistant", "text": f"✓ **{output_type} generated!**"}

            if output_type == "Interactive Map":
                # Add fullscreen if not present
                try:
                    plugins.Fullscreen(position='topright', force_separate_button=True).add_to(result)
                except:
                    pass

                map_html = result._repr_html_()
                response_msg["map_html"] = map_html

                st.markdown(response_msg["text"])
                st.info("💡 Hover over features for details | 📐 Click fullscreen button (top-right)")
                st.components.v1.html(map_html, height=600, scrolling=True)

            elif output_type == "Static Plot":
                plot_path = f'plot_{st.session_state.chat_counter}.png'
                result.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close()

                response_msg["plot_path"] = plot_path
                st.markdown(response_msg["text"])
                st.image(plot_path)

            else:
                response_msg["dataframe"] = result
                st.markdown(response_msg["text"])
                st.dataframe(result, use_container_width=True)

            # Show code
            with st.expander("🔍 View Generated Code"):
                st.code(st.session_state.gdfai.code, language="python")

            st.session_state.messages.append(response_msg)

        except Exception as e:
            status.empty()
            st.error(f"❌ Error: {str(e)}")
            with st.expander("Debug"):
                import traceback
                st.code(traceback.format_exc())

# Helper section
st.markdown("---")
with st.expander("💡 Example Queries"):
    st.markdown("""
    **Location-specific queries (will filter and zoom):**
    - "Show me the Al Nahyan district"
    - "Highlight all districts with 'AL' in the name"
    - "Find the largest district"
    - "Show me districts on the eastern side"
    - "Locate community E19_02"

    **General map queries:**
    - "Create a map of all districts"
    - "Show all boundaries colored by district"

    **Analysis queries:**
    - "How many features are in each district?"
    - "What are the unique district names?"
    - "Show me the top 5 largest areas"

    **Improvements (after first query):**
    - "Make it more colorful"
    - "Add a legend"
    - "Zoom in closer"
    - "Show only the top 3"
    """)

with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown(f"**Queries:** {st.session_state.chat_counter}")
