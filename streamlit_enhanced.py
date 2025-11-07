#!/usr/bin/env python3
"""
Enhanced Streamlit Chat with Tooltips and Fullscreen

Features:
- Automatic tooltips on maps
- Fullscreen button
- Better default prompts

Usage:
    streamlit run streamlit_enhanced.py
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

# Page config
st.set_page_config(
    page_title="GeoPandas-AI Chat",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ GeoPandas-AI Interactive Chat")
st.markdown("Chat with your geospatial data using natural language!")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    ollama_model = st.text_input(
        "Ollama Model",
        value="openai/qwen2.5-coder:14b",
    )

    output_type = st.radio(
        "Output Type",
        ["Interactive Map", "Static Plot", "Data Analysis"],
    )

    sample_size = st.slider(
        "Sample Size",
        min_value=10,
        max_value=200,
        value=50,
    )

    add_tooltips = st.checkbox(
        "Auto-add tooltips to maps",
        value=True,
        help="Automatically request tooltips with district names"
    )

    add_fullscreen = st.checkbox(
        "Add fullscreen button",
        value=True,
        help="Add fullscreen control to maps"
    )

    if st.button("🔄 Reset Conversation"):
        if 'gdfai' in st.session_state:
            st.session_state.gdfai.reset()
            st.session_state.messages = []
            st.session_state.chat_counter = 0
            st.success("✓ Conversation reset!")
            st.rerun()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'chat_counter' not in st.session_state:
    st.session_state.chat_counter = 0

if 'gdfai' not in st.session_state:
    with st.spinner("📥 Loading data..."):
        # Configure Ollama
        update_geopandasai_config(
            lite_llm_config={
                "model": ollama_model,
                "api_base": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
                "temperature": 0.0,
            }
        )

        # Load data
        url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
        params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}

        try:
            response = requests.get(url, params=params, verify=False)
            with open('temp_st.geojson', 'w') as f:
                json.dump(response.json(), f)

            gdf = gpd.read_file('temp_st.geojson')
            gdf_sample = gdf.sample(n=min(sample_size, len(gdf)), random_state=42)

            st.session_state.gdfai = GeoDataFrameAI(gdf_sample)
            st.session_state.gdf = gdf_sample

            st.sidebar.success(f"✓ Loaded {len(gdf_sample)} features")

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            st.stop()

def enhance_map(folium_map, add_fullscreen_btn=True):
    """Add enhancements to folium map"""
    if add_fullscreen_btn:
        # Add fullscreen button
        plugins.Fullscreen(
            position='topright',
            title='Enter fullscreen mode',
            title_cancel='Exit fullscreen mode',
            force_separate_button=True,
        ).add_to(folium_map)

    # Add layer control if multiple layers
    folium.LayerControl().add_to(folium_map)

    return folium_map

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
user_input = st.chat_input("Type your request here...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "text": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        status_placeholder.markdown("🤖 Thinking... (30-60 seconds with local LLM)")

        try:
            # Enhance prompt for maps with tooltips
            enhanced_prompt = user_input

            if output_type == "Interactive Map" and add_tooltips:
                # Add tooltip instructions to prompt
                if st.session_state.chat_counter == 0:
                    # First message - be explicit about tooltips
                    enhanced_prompt = (
                        f"{user_input}. "
                        "IMPORTANT: Add tooltips using folium.GeoJsonTooltip that show "
                        "the DISTRICTENG field when hovering over features. "
                        "Use folium.GeoJson to add the data with proper tooltip configuration."
                    )
                else:
                    # Improvement - check if asking for tooltips
                    if 'tooltip' not in user_input.lower():
                        enhanced_prompt = f"{user_input}. Also ensure tooltips show DISTRICTENG on hover."

            # Determine return type
            if output_type == "Interactive Map":
                return_type = folium.Map
            elif output_type == "Static Plot":
                return_type = Figure
            else:
                return_type = None

            # Use chat or improve
            is_first = st.session_state.chat_counter == 0

            if is_first:
                result = st.session_state.gdfai.chat(enhanced_prompt, return_type=return_type)
            else:
                result = st.session_state.gdfai.improve(enhanced_prompt, return_type=return_type)

            st.session_state.chat_counter += 1

            status_placeholder.empty()

            # Prepare response message
            response_msg = {
                "role": "assistant",
                "text": f"✓ **Generated {output_type}!**"
            }

            # Handle different output types
            if output_type == "Interactive Map":
                # Enhance the map
                if add_fullscreen:
                    result = enhance_map(result, add_fullscreen_btn=True)

                # Save map to HTML string
                map_html = result._repr_html_()
                response_msg["map_html"] = map_html

                # Display immediately
                st.markdown(response_msg["text"])
                if add_tooltips:
                    st.info("💡 Hover over features to see district names (if LLM added tooltips correctly)")
                if add_fullscreen:
                    st.info("🔍 Click the fullscreen button (top-right of map) to expand")

                st.components.v1.html(map_html, height=600, scrolling=True)

            elif output_type == "Static Plot":
                # Save plot
                plot_path = f'chat_plot_{st.session_state.chat_counter}.png'
                result.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close()

                response_msg["plot_path"] = plot_path

                # Display immediately
                st.markdown(response_msg["text"])
                st.image(plot_path)

            else:  # Data Analysis
                response_msg["dataframe"] = result

                # Display immediately
                st.markdown(response_msg["text"])
                st.dataframe(result, use_container_width=True)

            # Add code viewer
            with st.expander("🔍 View Generated Code"):
                st.code(st.session_state.gdfai.code, language="python")

            # Save to history
            st.session_state.messages.append(response_msg)

        except Exception as e:
            status_placeholder.empty()
            error_text = f"❌ **Error:** {str(e)}"
            st.error(error_text)

            st.session_state.messages.append({
                "role": "assistant",
                "text": error_text
            })

            # Show traceback in expander
            with st.expander("🐛 Debug Info"):
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
with st.expander("💡 Tips & Examples"):
    st.markdown("""
    **How to use:**
    1. Choose output type in sidebar (Interactive Map, Static Plot, or Data Analysis)
    2. Type your request in the chat box
    3. Press Enter and wait 30-60 seconds
    4. See your result displayed above!
    5. Type another request to improve it

    **Map features:**
    - ✅ Tooltips enabled: Hover over features to see district names
    - ✅ Fullscreen button: Top-right corner of map
    - ✅ Zoom: Mouse wheel or +/- buttons
    - ✅ Pan: Click and drag

    **Example conversation:**
    - YOU: "Create a map showing the districts"
    - AI: [displays map with tooltips and fullscreen]
    - YOU: "Color them by district name"
    - AI: [displays improved map]
    - YOU: "Make the colors more vibrant"
    - AI: [displays even better map]

    **Example prompts:**
    - "Create an interactive map"
    - "Add different colors for each district"
    - "Make the polygons semi-transparent"
    - "Add a legend"
    - "Show me statistics about the districts"
    """)

# Sidebar status
with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown(f"**AI requests:** {st.session_state.chat_counter}")

    if st.button("📋 Show Current Code"):
        if st.session_state.chat_counter > 0:
            st.code(st.session_state.gdfai.code, language="python")
        else:
            st.info("No code generated yet")

    st.markdown("---")
    st.markdown("**🎯 Quick Tips:**")
    st.markdown("""
    - Check **Auto-add tooltips** for hover info
    - Check **Add fullscreen button** for better view
    - Adjust **Sample Size** for speed vs detail
    - Use **Reset** to start fresh
    """)
