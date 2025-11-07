#!/usr/bin/env python3
"""
Fixed Streamlit App - Ensures zoom, summary, and data table work

Usage:
    streamlit run app_fixed.py
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

st.set_page_config(page_title="GeoPandas-AI", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI Chat")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    model = st.text_input("Model", value="openai/qwen2.5-coder:14b")

    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# Initialize
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'gdfai' not in st.session_state:
    with st.spinner("Loading Abu Dhabi data..."):
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
        st.session_state.gdf = gdf
        st.session_state.gdfai = GeoDataFrameAI(gdf)
        st.session_state.count = 0

        districts = sorted(gdf['DISTRICTENG'].dropna().unique())

        st.sidebar.success(f"✓ {len(gdf)} features loaded")
        with st.sidebar.expander("📋 Districts"):
            for d in districts[:20]:
                st.text(d)

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["text"])
        else:
            # Assistant message
            st.success(msg["text"])

            if "summary" in msg:
                st.info(msg["summary"])

            if "html" in msg:
                st.components.v1.html(msg["html"], height=600)

            if "table" in msg:
                st.markdown("---")
                st.markdown("### 📋 Filtered Results")
                st.dataframe(msg["table"], use_container_width=True)

# Chat
user_input = st.chat_input("Ask about a district...")

if user_input:
    # Save user message
    st.session_state.messages.append({"role": "user", "text": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate response
    with st.chat_message("assistant"):
        status = st.empty()
        status.info("🤖 Generating response (30-60 seconds)...")

        try:
            # Step 1: Get filtered data first
            data_prompt = f"""
{user_input}

Return the filtered GeoDataFrame that matches this query.
Filter df_1 based on the query and return ONLY matching rows.

Example:
If query is "Show me AL NAHYAN", filter like:
filtered = df_1[df_1['DISTRICTENG'].str.contains('AL NAHYAN', case=False, na=False)]
return filtered
"""

            filtered_data = st.session_state.gdfai.chat(data_prompt)
            st.session_state.count += 1

            # Check if we got data
            if not isinstance(filtered_data, gpd.GeoDataFrame):
                status.empty()
                st.error("❌ Could not get filtered data")
                st.info("Try: 'Show me AL NAHYAN' (check sidebar for exact names)")
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": "Error getting data. Try rephrasing."
                })
                st.stop()

            if len(filtered_data) == 0:
                status.empty()
                st.warning(f"❌ No results found for '{user_input}'")
                st.info("Check sidebar for available district names")
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": f"No results found for '{user_input}'"
                })
                st.stop()

            status.empty()

            # Prepare response message
            response = {
                "role": "assistant",
                "text": f"✓ Found {len(filtered_data)} feature(s)"
            }

            # Generate summary
            num_districts = filtered_data['DISTRICTENG'].nunique() if 'DISTRICTENG' in filtered_data.columns else 0
            summary = f"📊 **Summary:** Found {len(filtered_data)} feature(s)"

            if num_districts > 0:
                summary += f" across {num_districts} district(s)"

                if num_districts == 1:
                    district_name = filtered_data['DISTRICTENG'].iloc[0]
                    summary += f" ({district_name})"

            response["summary"] = summary
            st.info(summary)

            # Create map manually (not using AI for map creation to ensure it works)
            st.markdown("### 🗺️ Interactive Map")

            # Calculate bounds and center
            bounds = filtered_data.total_bounds  # [minx, miny, maxx, maxy]
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2

            # Calculate zoom level based on bounds size
            lat_diff = abs(bounds[3] - bounds[1])
            lon_diff = abs(bounds[2] - bounds[0])
            max_diff = max(lat_diff, lon_diff)

            if max_diff < 0.01:
                zoom = 15
            elif max_diff < 0.05:
                zoom = 13
            elif max_diff < 0.1:
                zoom = 12
            else:
                zoom = 10

            # Create map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )

            # Add filtered data
            folium.GeoJson(
                filtered_data,
                style_function=lambda x: {
                    'fillColor': '#ff7800',
                    'color': '#000000',
                    'weight': 2,
                    'fillOpacity': 0.5,
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['DISTRICTENG', 'COMMUNITYENG'],
                    aliases=['District:', 'Community:'],
                    localize=True
                )
            ).add_to(m)

            # Add fullscreen
            plugins.Fullscreen(
                position='topright',
                title='Fullscreen',
                title_cancel='Exit fullscreen',
                force_separate_button=True
            ).add_to(m)

            # Display map
            map_html = m._repr_html_()
            response["html"] = map_html
            st.components.v1.html(map_html, height=600, scrolling=True)

            st.caption("💡 Hover over features for details | 📐 Click fullscreen button (top-right)")

            # Show data table
            st.markdown("---")
            st.markdown("### 📋 Filtered Results")

            # Select columns to show
            cols_to_show = ['DISTRICTENG', 'COMMUNITYENG']
            if 'PLOTNUMBER' in filtered_data.columns:
                cols_to_show.append('PLOTNUMBER')

            cols_available = [c for c in cols_to_show if c in filtered_data.columns]

            if cols_available:
                table = filtered_data[cols_available].head(50)
                response["table"] = table
                st.dataframe(table, use_container_width=True)

                if len(filtered_data) > 50:
                    st.caption(f"Showing first 50 of {len(filtered_data)} rows")
            else:
                st.dataframe(filtered_data.head(50), use_container_width=True)

            # Save message
            st.session_state.messages.append(response)

        except Exception as e:
            status.empty()
            st.error(f"❌ Error: {str(e)}")

            import traceback
            with st.expander("Debug info"):
                st.code(traceback.format_exc())

            st.info("💡 Try: 'Show me AL NAHYAN' or check sidebar for district names")

# Footer
st.markdown("---")
with st.expander("💡 How to use"):
    st.markdown("""
    **Try these:**
    - "Show me AL NAHYAN"
    - "Find AL BATEEN district"
    - "Show districts with AL"

    **Features:**
    - ✅ Auto-zoom to results
    - ✅ Summary of what was found
    - ✅ Data table below map
    - ✅ Tooltips on hover
    - ✅ Fullscreen button

    **Note:** District names are UPPERCASE (check sidebar)
    """)
