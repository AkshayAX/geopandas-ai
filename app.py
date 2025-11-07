#!/usr/bin/env python3
"""
Clean Streamlit Chat - No code display errors

Usage:
    streamlit run app.py
"""

import streamlit as st
import geopandas as gpd
from geopandasai import GeoDataFrameAI, update_geopandasai_config
import folium
from folium import plugins
import warnings
import requests
import json
import urllib3

warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="GeoPandas-AI Chat", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI Chat")
st.markdown("Ask about Abu Dhabi districts and communities")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    model = st.text_input("Model", value="openai/qwen2.5-coder:14b")

    show_summary = st.checkbox("📝 Show summary", value=True)
    show_table = st.checkbox("📊 Show data table", value=True)

    if st.button("🔄 Reset Chat"):
        st.session_state.clear()
        st.rerun()

# Initialize
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'gdfai' not in st.session_state:
    with st.spinner("Loading data..."):
        update_geopandasai_config(
            lite_llm_config={
                "model": model,
                "api_base": "http://127.0.0.1:11434/v1",
                "api_key": "ollama",
            }
        )

        url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
        params = {'where': '1=1', 'outFields': '*', 'returnGeometry': 'true', 'f': 'geojson'}

        response = requests.get(url, params=params, verify=False)
        with open('temp.geojson', 'w') as f:
            json.dump(response.json(), f)

        gdf = gpd.read_file('temp.geojson').sample(n=100, random_state=42)

        st.session_state.gdfai = GeoDataFrameAI(gdf)
        st.session_state.gdf = gdf
        st.session_state.chat_count = 0

        districts = sorted(gdf['DISTRICTENG'].dropna().unique())
        st.sidebar.success(f"✓ Loaded {len(gdf)} features, {len(districts)} districts")

        with st.sidebar.expander("📋 Available Districts"):
            for d in districts[:15]:
                st.text(f"• {d}")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if "html" in msg:
            st.components.v1.html(msg["html"], height=600)

        if "table" in msg:
            st.markdown("### 📋 Data")
            st.dataframe(msg["table"])

# Chat input
user_msg = st.chat_input("e.g., 'Show me AL NAHYAN district'")

if user_msg:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_msg})

    with st.chat_message("user"):
        st.markdown(user_msg)

    # Generate response
    with st.chat_message("assistant"):
        status = st.empty()
        status.info("🤖 Generating (30-60 seconds)...")

        try:
            # Smart prompt
            prompt = f"""
{user_msg}

Instructions:
1. Filter df_1 to show ONLY features matching the query
2. If no matches, return empty GeoDataFrame
3. Create folium map:
   - Center on filtered data bounds
   - Add GeoJson with tooltips (DISTRICTENG, COMMUNITYENG)
   - Add fullscreen button
4. Return folium.Map object

Code template:
```python
import folium
from folium import plugins

def execute(df_1):
    # Filter
    filtered = df_1[df_1['DISTRICTENG'].str.contains('term', case=False, na=False)]

    if len(filtered) == 0:
        # Empty map with marker
        m = folium.Map(location=[24.45, 54.37], zoom_start=10)
        folium.Marker([24.45, 54.37], popup='No results').add_to(m)
        return m

    # Get center
    bounds = filtered.total_bounds
    lat = (bounds[1] + bounds[3]) / 2
    lon = (bounds[0] + bounds[2]) / 2

    # Create map
    m = folium.Map(location=[lat, lon], zoom_start=12)

    # Add data
    folium.GeoJson(
        filtered,
        tooltip=folium.GeoJsonTooltip(['DISTRICTENG', 'COMMUNITYENG'])
    ).add_to(m)

    # Add fullscreen
    plugins.Fullscreen().add_to(m)

    return m
```
"""

            # Call AI
            is_first = st.session_state.chat_count == 0

            if is_first:
                result = st.session_state.gdfai.chat(prompt, return_type=folium.Map)
            else:
                result = st.session_state.gdfai.improve(prompt, return_type=folium.Map)

            st.session_state.chat_count += 1
            status.empty()

            # Display result
            response = {"role": "assistant", "content": "✓ **Map generated!**"}

            # Summary
            if show_summary:
                summary = f"🗺️ Map for '{user_msg}'. Hover for info, click fullscreen (top-right)."
                response["content"] += f"\n\n{summary}"
                st.info(summary)
            else:
                st.success(response["content"])

            # Show map
            try:
                html = result._repr_html_()
                response["html"] = html
                st.components.v1.html(html, height=600)
            except Exception as e:
                st.error(f"Map error: {e}")
                st.info("Try: 'Show me AL NAHYAN' or check sidebar for available districts")

            # Show data table
            if show_table:
                try:
                    # Get filtered data
                    st.session_state.gdfai.reset()
                    data = st.session_state.gdfai.chat(f"{user_msg}. Return filtered GeoDataFrame.")

                    if isinstance(data, gpd.GeoDataFrame) and len(data) > 0:
                        cols = ['DISTRICTENG', 'COMMUNITYENG']
                        cols = [c for c in cols if c in data.columns]

                        if cols:
                            table = data[cols].head(50)
                            response["table"] = table

                            st.markdown("### 📋 Data")
                            st.dataframe(table)
                except:
                    pass  # Skip table if fails

            # Save message
            st.session_state.messages.append(response)

        except Exception as e:
            status.empty()
            st.error(f"❌ Error: {e}")
            st.info("💡 Try: 'Show me AL NAHYAN' or check sidebar for district names")

# Footer
with st.expander("💡 Tips"):
    st.markdown("""
    **Try these queries:**
    - "Show me AL NAHYAN"
    - "Find districts with AL"
    - "Show all districts"

    **Notes:**
    - District names are UPPERCASE
    - Check sidebar for available names
    - First query takes 30-60 seconds
    """)
