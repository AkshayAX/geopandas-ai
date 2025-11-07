#!/usr/bin/env python3
"""
Simplified Streamlit Chat App - No streamlit-folium required!

Maps are saved as HTML and displayed via iframe instead.

Usage:
    pip install streamlit
    streamlit run streamlit_chat_simple.py
"""

import streamlit as st
import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import warnings
import requests
import json
import urllib3
import os

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
        help="Make sure this model is installed: ollama pull qwen2.5-coder:14b"
    )

    output_type = st.selectbox(
        "Output Type",
        ["Interactive Map (folium)", "Static Plot (matplotlib)", "Data (GeoDataFrame)"],
        help="What kind of output do you want?"
    )

    sample_size = st.slider(
        "Sample Size",
        min_value=10,
        max_value=500,
        value=50,
        help="Number of features to use (smaller = faster)"
    )

    if st.button("🔄 Reset Conversation"):
        if 'gdfai' in st.session_state:
            st.session_state.gdfai.reset()
            st.session_state.messages = []
            st.success("Conversation reset!")
            st.rerun()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'map_counter' not in st.session_state:
    st.session_state.map_counter = 0

if 'gdfai' not in st.session_state:
    with st.spinner("Loading data..."):
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
            with open('temp_streamlit.geojson', 'w') as f:
                json.dump(response.json(), f)

            gdf = gpd.read_file('temp_streamlit.geojson')
            gdf_sample = gdf.sample(n=min(sample_size, len(gdf)), random_state=42)

            st.session_state.gdfai = GeoDataFrameAI(gdf_sample)
            st.session_state.gdf = gdf_sample

            st.sidebar.success(f"✓ Loaded {len(gdf_sample)} features")

        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if "result_file" in message:
            # Display map via iframe or image
            if message["result_type"] == "map":
                with open(message["result_file"], 'r') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=500, scrolling=True)

            elif message["result_type"] == "plot":
                st.image(message["result_file"])

        elif "result_data" in message:
            st.dataframe(message["result_data"])

# Chat input
if prompt := st.chat_input("Ask me anything about your geospatial data..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking... (this may take 30-60 seconds with local LLM)"):
            try:
                # Determine return type
                if output_type == "Interactive Map (folium)":
                    return_type = folium.Map
                    result_type = "map"
                elif output_type == "Static Plot (matplotlib)":
                    return_type = Figure
                    result_type = "plot"
                else:
                    return_type = None
                    result_type = "data"

                # Use .improve() if this is a follow-up, otherwise .chat()
                if len(st.session_state.messages) > 1:
                    result = st.session_state.gdfai.improve(
                        prompt,
                        return_type=return_type
                    )
                else:
                    result = st.session_state.gdfai.chat(
                        prompt,
                        return_type=return_type
                    )

                # Display result
                response_text = f"✓ Generated! Here's your {output_type.split('(')[0].strip().lower()}:"
                st.markdown(response_text)

                message_data = {
                    "role": "assistant",
                    "content": response_text
                }

                if result_type == "map":
                    # Save map to file
                    st.session_state.map_counter += 1
                    map_file = f'streamlit_map_{st.session_state.map_counter}.html'
                    result.save(map_file)

                    # Display via iframe
                    with open(map_file, 'r') as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=500, scrolling=True)

                    message_data["result_file"] = map_file
                    message_data["result_type"] = "map"

                elif result_type == "plot":
                    # Save plot to file
                    st.session_state.map_counter += 1
                    plot_file = f'streamlit_plot_{st.session_state.map_counter}.png'
                    result.savefig(plot_file, dpi=150, bbox_inches='tight')

                    # Display
                    st.image(plot_file)
                    plt.close()

                    message_data["result_file"] = plot_file
                    message_data["result_type"] = "plot"

                else:
                    st.dataframe(result)
                    message_data["result_data"] = result

                # Show generated code in expander
                with st.expander("🔍 View Generated Code"):
                    st.code(st.session_state.gdfai.code, language="python")

                # Add to chat history
                st.session_state.messages.append(message_data)

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Footer with tips
st.markdown("---")
st.markdown("""
### 💡 Tips:
- Start with simple requests like "Create a map" or "Show the data"
- Use follow-up messages to improve: "Add colors", "Add tooltips", etc.
- Click "Reset Conversation" to start fresh
- Each message builds on the previous ones!

### 📝 Example prompts:
- "Create an interactive map colored by district"
- "Add tooltips showing district names"
- "Show me the top 10 largest features"
- "Create a matplotlib plot with a legend"
""")

# Show conversation state
with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Conversation length:** {len(st.session_state.messages)} messages")

    if st.button("📋 Show Full Code"):
        if hasattr(st.session_state.gdfai, 'code'):
            st.code(st.session_state.gdfai.code, language="python")
