#!/usr/bin/env python3
"""
Robust Streamlit Chat - Handles errors and edge cases gracefully

Features:
- Smart filtering with validation
- Error handling for empty results
- Summary and data table
- Fallback for invalid maps

Usage:
    streamlit run streamlit_app.py
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

st.set_page_config(page_title="GeoPandas-AI Chat", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI Interactive Chat")
st.markdown("Ask about districts, communities, and locations in Abu Dhabi")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    ollama_model = st.text_input("Ollama Model", value="openai/qwen2.5-coder:14b")

    output_type = st.radio("Output Type", ["Interactive Map", "Static Plot", "Data Analysis"])

    st.markdown("### Display Options")

    show_summary = st.checkbox("📝 Show summary", value=True)
    show_data_table = st.checkbox("📊 Show data table", value=True)

    table_columns = st.multiselect(
        "Table columns",
        ["DISTRICTENG", "COMMUNITYENG", "DISTRICTARA", "PLOTNUMBER"],
        default=["DISTRICTENG", "COMMUNITYENG"],
    )

    sample_size = st.slider("Sample Size", 10, 500, 100)

    if st.button("🔄 Reset"):
        for key in ['gdfai', 'messages', 'chat_counter']:
            if key in st.session_state:
                if key == 'gdfai':
                    st.session_state.gdfai.reset()
                del st.session_state[key]
        st.rerun()

# Initialize
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_counter' not in st.session_state:
    st.session_state.chat_counter = 0

if 'gdfai' not in st.session_state:
    with st.spinner("📥 Loading Abu Dhabi data..."):
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

        # Get unique values for search
        districts = sorted(gdf['DISTRICTENG'].dropna().unique())
        communities = sorted(gdf['COMMUNITYENG'].dropna().unique()) if 'COMMUNITYENG' in gdf.columns else []

        st.session_state.districts = districts
        st.session_state.communities = communities

        st.sidebar.success(f"✓ Loaded {len(gdf_sample)} features")
        st.sidebar.info(f"📍 {len(districts)} districts, {len(communities)} communities")

# Show available locations
with st.sidebar:
    with st.expander("📋 Available Locations"):
        st.markdown("**Districts:**")
        for d in st.session_state.districts[:10]:
            st.text(f"• {d}")
        if len(st.session_state.districts) > 10:
            st.text(f"... and {len(st.session_state.districts) - 10} more")

        if st.session_state.communities:
            st.markdown("**Communities (sample):**")
            for c in st.session_state.communities[:5]:
                st.text(f"• {c}")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

        if "summary" in msg:
            st.info(msg["summary"])

        if "map_html" in msg:
            st.components.v1.html(msg["map_html"], height=600, scrolling=True)
        elif "plot_path" in msg:
            st.image(msg["plot_path"])
        elif "dataframe" in msg:
            st.dataframe(msg["dataframe"], use_container_width=True)

        if "data_table" in msg:
            st.markdown("---")
            st.markdown("### 📋 Data Table")
            st.dataframe(msg["data_table"], use_container_width=True)

# Chat input
user_input = st.chat_input("e.g., 'Show me Al Nahyan district' or 'Find districts with AL in the name'")

if user_input:
    st.session_state.messages.append({"role": "user", "text": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        status = st.empty()
        status.markdown("🤖 Processing your query...")

        try:
            # Smart prompt enhancement
            enhanced_prompt = user_input
            query_lower = user_input.lower()

            filter_keywords = ['show', 'find', 'where', 'which', 'locate', 'highlight', 'display']
            is_location_query = any(kw in query_lower for kw in filter_keywords)

            if output_type == "Interactive Map" and is_location_query:
                enhanced_prompt = f"""
{user_input}

CRITICAL INSTRUCTIONS:
1. Filter df_1 to ONLY include features matching the query
2. CHECK if filtered result is empty - if so, return a message saying "No features found"
3. If data exists, create folium map:
   - Get bounds: bounds = filtered_df.total_bounds
   - Center: center_lat = (bounds[1] + bounds[3]) / 2, center_lon = (bounds[0] + bounds[2]) / 2
   - Create map: m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
   - Add GeoJson with proper structure and tooltips
   - Add fullscreen: folium.plugins.Fullscreen().add_to(m)
4. Return the folium.Map object

Example code structure:
```python
import folium
from folium import plugins

def execute(df_1):
    # Filter
    filtered = df_1[df_1['DISTRICTENG'].str.contains('search_term', case=False, na=False)]

    if len(filtered) == 0:
        # Create empty map with message
        m = folium.Map(location=[24.4539, 54.3773], zoom_start=10)
        folium.Marker([24.4539, 54.3773],
                     popup='No features found matching query').add_to(m)
        return m

    # Calculate center
    bounds = filtered.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    # Add data
    folium.GeoJson(
        filtered,
        tooltip=folium.GeoJsonTooltip(fields=['DISTRICTENG', 'COMMUNITYENG'])
    ).add_to(m)

    # Add fullscreen
    plugins.Fullscreen().add_to(m)

    return m
```
"""

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

            # Prepare response
            response_msg = {"role": "assistant", "text": f"✓ **Result generated!**"}

            # Handle result based on type
            if output_type == "Interactive Map":
                # Try to render the map
                try:
                    map_html = result._repr_html_()
                    response_msg["map_html"] = map_html

                    st.markdown(response_msg["text"])

                    # Generate summary
                    if show_summary:
                        summary = f"🗺️ **Summary:** Interactive map generated for '{user_input}'. Hover for details, click fullscreen (top-right) to expand."
                        response_msg["summary"] = summary
                        st.info(summary)

                    st.components.v1.html(map_html, height=600, scrolling=True)

                    # Try to get data for table
                    if show_data_table:
                        try:
                            # Ask for the filtered data
                            st.session_state.gdfai.reset()
                            data_result = st.session_state.gdfai.chat(
                                f"{user_input}. Return ONLY the filtered GeoDataFrame, not a map."
                            )

                            if isinstance(data_result, gpd.GeoDataFrame) and len(data_result) > 0:
                                display_cols = [c for c in table_columns if c in data_result.columns]
                                if display_cols:
                                    table_data = data_result[display_cols].head(50)  # Limit to 50 rows
                                    response_msg["data_table"] = table_data

                                    st.markdown("---")
                                    st.markdown(f"### 📋 Data Table ({len(data_result)} features, showing first 50)")
                                    st.dataframe(table_data, use_container_width=True)
                        except:
                            pass  # Silently skip table if it fails

                except Exception as map_error:
                    # Fallback: map rendering failed
                    st.error(f"⚠️ Map rendering failed: {str(map_error)}")
                    st.info("💡 The query may have returned no results or generated invalid map code.")

                    # Show the code to debug
                    st.markdown("**Generated code:**")
                    st.code(st.session_state.gdfai.code, language="python")

                    # Try to show what was actually found
                    st.markdown("Let me try to show you the raw data instead:")
                    try:
                        st.session_state.gdfai.reset()
                        data_result = st.session_state.gdfai.chat(f"{user_input}. Return the filtered GeoDataFrame.")

                        if isinstance(data_result, gpd.GeoDataFrame):
                            if len(data_result) == 0:
                                st.warning(f"❌ No features found matching '{user_input}'")
                                st.markdown("**Available districts:**")
                                st.write(st.session_state.districts)
                            else:
                                st.success(f"✓ Found {len(data_result)} features")
                                st.dataframe(data_result.head(20), use_container_width=True)
                    except:
                        st.warning("Could not retrieve data. Try rephrasing your query.")

            elif output_type == "Static Plot":
                plot_path = f'plot_{st.session_state.chat_counter}.png'
                result.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close()

                response_msg["plot_path"] = plot_path
                st.markdown(response_msg["text"])

                if show_summary:
                    summary = f"📊 **Summary:** Generated plot for '{user_input}'"
                    response_msg["summary"] = summary
                    st.info(summary)

                st.image(plot_path)

            else:  # Data Analysis
                response_msg["dataframe"] = result
                st.markdown(response_msg["text"])

                if isinstance(result, gpd.GeoDataFrame):
                    num_features = len(result)

                    if show_summary:
                        summary = f"📊 **Summary:** Found {num_features} feature{'s' if num_features != 1 else ''}"
                        if 'DISTRICTENG' in result.columns:
                            num_districts = result['DISTRICTENG'].nunique()
                            summary += f" across {num_districts} district{'s' if num_districts != 1 else ''}"
                        response_msg["summary"] = summary
                        st.info(summary)

                    st.dataframe(result, use_container_width=True)

                else:
                    if show_summary:
                        st.info(f"📊 **Summary:** Query result for '{user_input}'")
                    st.write(result)

            # Show code
            with st.expander("🔍 View Generated Code"):
                st.code(st.session_state.gdfai.code, language="python")

            st.session_state.messages.append(response_msg)

        except Exception as e:
            status.empty()
            st.error(f"❌ **Error:** {str(e)}")

            st.markdown("**Suggestions:**")
            st.markdown("- Check the available districts in the sidebar")
            st.markdown("- Try a different query")
            st.markdown("- Use exact district names (e.g., 'Show me AL NAHYAN')")

            with st.expander("🐛 Debug Info"):
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
with st.expander("💡 Tips & Examples"):
    st.markdown("""
    **Working examples:**
    - "Show me AL NAHYAN district"
    - "Find districts with AL in the name"
    - "Display MASNOUAH ISLAND community"
    - "Show me all districts"

    **Available districts** - check sidebar →

    **If you get no results:**
    - District names are in CAPS (e.g., "AL NAHYAN" not "Al Nahyan")
    - Check spelling against the sidebar list
    - Try broader searches like "districts with AL"
    """)

with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown(f"**Queries:** {st.session_state.chat_counter}")
