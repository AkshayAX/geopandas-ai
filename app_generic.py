#!/usr/bin/env python3
"""
Generic GeoPandas-AI Chat - Works with ANY geospatial data

This version:
- No hardcoded column names
- LLM decides what to show based on your data
- Works with any GeoDataFrame
- Lets you ask any question

Usage:
    streamlit run app_generic.py
"""

import streamlit as st
import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
from matplotlib.figure import Figure
import warnings
import requests
import json
import urllib3
import os

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GeoPandas-AI Generic Chat", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI: Chat with Your Geospatial Data")
st.markdown("Ask **any question** about your data - the AI figures out the rest!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # Model selection
    use_cloud = st.checkbox("Use cloud model (better quality)", value=False)

    if use_cloud:
        cloud_provider = st.selectbox("Provider", ["OpenAI", "Anthropic", "Google"])

        if cloud_provider == "OpenAI":
            model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"])
            api_key = st.text_input("API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
        elif cloud_provider == "Anthropic":
            model = "claude-3-5-sonnet-20241022"
            api_key = st.text_input("API Key", type="password", value=os.environ.get("ANTHROPIC_API_KEY", ""))
        else:
            model = "gemini/gemini-1.5-flash"
            api_key = st.text_input("API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    else:
        model = st.text_input("Ollama Model", value="openai/qwen2.5-coder:14b")
        api_key = "ollama"

    output_type = st.radio(
        "Default Output Type",
        ["Auto-detect", "Interactive Map", "Static Plot", "Data/Analysis"],
        help="Let AI decide, or force a specific output type"
    )

    if st.button("🔄 Reset Chat"):
        st.session_state.clear()
        st.rerun()

# Initialize
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'gdfai' not in st.session_state:
    with st.spinner("Loading geospatial data..."):
        # Configure AI
        if use_cloud and not api_key:
            st.error("❌ Please provide an API key")
            st.stop()

        config = {
            "model": model,
            "api_key": api_key,
        }

        if not use_cloud:
            config["api_base"] = "http://127.0.0.1:11434/v1"

        update_geopandasai_config(lite_llm_config=config)

        # Load data (example - you can modify to load any data)
        url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
        params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}
        response = requests.get(url, params=params, verify=False)

        with open('temp.geojson', 'w') as f:
            json.dump(response.json(), f)

        gdf = gpd.read_file('temp.geojson').sample(n=100, random_state=42)

        # Create AI-enabled GeoDataFrame
        st.session_state.gdfai = GeoDataFrameAI(
            gdf,
            description="Geospatial data with administrative boundaries, districts, and communities"
        )
        st.session_state.gdf = gdf

        # Show dataset info
        st.sidebar.success(f"✓ Loaded {len(gdf)} features")
        st.sidebar.info(f"📊 {len(gdf.columns)} columns available")

        with st.sidebar.expander("📋 Dataset Info"):
            st.text(f"Rows: {len(gdf)}")
            st.text(f"CRS: {gdf.crs}")
            st.text("\nColumns:")
            for col in gdf.columns[:15]:
                st.text(f"  • {col}")
            if len(gdf.columns) > 15:
                st.text(f"  ... and {len(gdf.columns) - 15} more")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if "map_html" in msg:
            st.components.v1.html(msg["map_html"], height=600)

        if "plot" in msg:
            st.pyplot(msg["plot"])

        if "data" in msg:
            st.dataframe(msg["data"], use_container_width=True)

# Chat input
user_input = st.chat_input("Ask anything about your data...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        status = st.empty()
        status.info("🤖 Thinking..." + (" (cloud models are faster!)" if not use_cloud else ""))

        try:
            # Determine return type
            if output_type == "Interactive Map":
                return_type = folium.Map
            elif output_type == "Static Plot":
                return_type = Figure
            elif output_type == "Data/Analysis":
                return_type = None
            else:
                # Auto-detect based on query
                query_lower = user_input.lower()
                if any(word in query_lower for word in ['map', 'show', 'display', 'plot', 'visualize']):
                    return_type = folium.Map
                else:
                    return_type = None  # Let it return data

            # Call AI (it decides everything!)
            is_first = len([m for m in st.session_state.messages if m["role"] == "assistant"]) == 0

            if is_first:
                result = st.session_state.gdfai.chat(user_input, return_type=return_type)
            else:
                result = st.session_state.gdfai.improve(user_input, return_type=return_type)

            status.empty()

            # Handle result
            response = {"role": "assistant", "content": "✓ **Result generated!**"}

            if isinstance(result, folium.Map):
                # Interactive map
                st.success("✓ Generated interactive map!")
                map_html = result._repr_html_()
                response["map_html"] = map_html
                st.components.v1.html(map_html, height=600)
                st.caption("💡 Hover for details | 📐 Fullscreen button (top-right)")

            elif isinstance(result, Figure):
                # Static plot
                st.success("✓ Generated plot!")
                response["plot"] = result
                st.pyplot(result)

            elif isinstance(result, (gpd.GeoDataFrame, type(None).__class__)):
                # Data result
                if result is not None and len(result) > 0:
                    st.success(f"✓ Found {len(result)} result(s)!")
                    response["data"] = result
                    st.dataframe(result, use_container_width=True)
                elif result is not None:
                    st.warning("No results found")
                else:
                    st.info("Query completed")

            else:
                # Other result
                st.success("✓ Result:")
                st.write(result)

            # Show generated code (optional)
            with st.expander("🔍 View Generated Code"):
                try:
                    st.code(st.session_state.gdfai.code, language="python")
                except:
                    st.text("Code not available")

            st.session_state.messages.append(response)

        except Exception as e:
            status.empty()
            st.error(f"❌ Error: {str(e)}")

            with st.expander("Debug Info"):
                import traceback
                st.code(traceback.format_exc())

            st.markdown("**Suggestions:**")
            st.markdown("- Try rephrasing your question")
            st.markdown("- Check dataset info in sidebar for column names")
            st.markdown("- Consider using a cloud model for better results")

# Examples
st.markdown("---")
with st.expander("💡 Example Questions (Generic - Works with ANY Dataset)"):
    st.markdown("""
    **Analysis questions:**
    - "How many unique values are in each column?"
    - "What are the top 5 largest features by area?"
    - "Show me statistics about the data"
    - "Which category has the most entries?"

    **Filtering:**
    - "Find all features where [column] contains [value]"
    - "Show me features with area greater than 1000"
    - "Filter to only [specific value]"

    **Visualization:**
    - "Create a map showing all features"
    - "Plot features colored by [column name]"
    - "Make a chart showing distribution of [column]"

    **Spatial analysis:**
    - "Find features within 1km of [location]"
    - "Which features overlap?"
    - "Calculate the total area by category"

    The AI figures out column names and operations from your data!
    """)

st.markdown("---")
st.caption("💡 **Tip:** For best results, use cloud models (GPT-4, Claude). Local models work but may be less reliable.")
