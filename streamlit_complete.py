#!/usr/bin/env python3
"""
Complete Streamlit Chat - With Summary and Data Table

Features:
- Smart filtering and zooming
- Auto-summary of results
- Data table showing filtered results
- Tooltips and fullscreen
- Configurable display options

Usage:
    streamlit run streamlit_complete.py
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

st.set_page_config(page_title="GeoPandas-AI Complete", page_icon="🗺️", layout="wide")

st.title("🗺️ GeoPandas-AI Complete Chat")
st.markdown("Ask about specific locations - get map + summary + data!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    ollama_model = st.text_input("Ollama Model", value="openai/qwen2.5-coder:14b")

    output_type = st.radio("Output Type", ["Interactive Map", "Static Plot", "Data Analysis"])

    st.markdown("### Display Options")

    show_summary = st.checkbox(
        "📝 Show summary",
        value=True,
        help="Display 1-2 line summary of results"
    )

    show_data_table = st.checkbox(
        "📊 Show data table",
        value=True,
        help="Display filtered data as table below map"
    )

    table_columns = st.multiselect(
        "Table columns to show",
        ["DISTRICTENG", "COMMUNITYENG", "DISTRICTARA", "COMMUNITYARA", "PLOTNUMBER", "geometry"],
        default=["DISTRICTENG", "COMMUNITYENG", "PLOTNUMBER"],
        help="Choose which columns to display in data table"
    )

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

        unique_districts = sorted(gdf['DISTRICTENG'].dropna().unique())
        st.session_state.districts = unique_districts

        st.sidebar.success(f"✓ Loaded {len(gdf_sample)} features")
        st.sidebar.info(f"📍 {len(unique_districts)} unique districts")

# Show available districts
with st.sidebar:
    with st.expander("📋 Available Districts"):
        if 'districts' in st.session_state:
            for district in st.session_state.districts[:20]:
                st.text(f"• {district}")
            if len(st.session_state.districts) > 20:
                st.text(f"... and {len(st.session_state.districts) - 20} more")

def generate_summary(result, user_query, output_type):
    """Generate a 1-2 line summary of the result"""
    try:
        if output_type == "Interactive Map":
            # For maps, we don't have the data directly, so make a general summary
            return f"🗺️ **Summary:** Generated interactive map for query: '{user_query}'. Hover over features for details, click fullscreen for better view."

        elif output_type == "Data Analysis":
            if isinstance(result, gpd.GeoDataFrame):
                num_features = len(result)
                if num_features == 0:
                    return "📊 **Summary:** No features found matching your query."

                # Get some stats
                districts = result['DISTRICTENG'].nunique() if 'DISTRICTENG' in result.columns else 0

                summary = f"📊 **Summary:** Found {num_features} feature{'s' if num_features != 1 else ''}"
                if districts > 0:
                    summary += f" across {districts} district{'s' if districts != 1 else ''}"

                # Add top district if available
                if 'DISTRICTENG' in result.columns and num_features > 0:
                    top_district = result['DISTRICTENG'].value_counts().index[0]
                    count = result['DISTRICTENG'].value_counts().iloc[0]
                    summary += f". Most common: {top_district} ({count} features)"

                return summary
            else:
                return f"📊 **Summary:** Query completed successfully. Result shown below."

        else:
            return f"📊 **Summary:** Generated visualization for query: '{user_query}'"

    except Exception as e:
        return f"📊 **Summary:** Results generated for query: '{user_query}'"

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["text"])

        # Show summary if available
        if "summary" in msg and msg.get("show_summary", True):
            st.markdown(msg["summary"])

        # Show visualization
        if "map_html" in msg:
            st.components.v1.html(msg["map_html"], height=600, scrolling=True)
        elif "plot_path" in msg:
            st.image(msg["plot_path"])
        elif "dataframe" in msg:
            st.dataframe(msg["dataframe"], use_container_width=True)

        # Show data table if available
        if "data_table" in msg and msg.get("show_table", True):
            st.markdown("---")
            st.markdown("### 📋 Filtered Data")
            st.dataframe(msg["data_table"], use_container_width=True)

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
            # Create smart prompt
            enhanced_prompt = user_input
            query_lower = user_input.lower()

            # Detect if this is a location query
            filter_keywords = ['show', 'find', 'where', 'which', 'locate', 'highlight']
            location_keywords = ['district', 'area', 'block', 'community', 'zone']
            is_location_query = any(kw in query_lower for kw in filter_keywords + location_keywords)

            if output_type == "Interactive Map" and is_location_query and st.session_state.chat_counter == 0:
                enhanced_prompt = f"""
{user_input}

IMPORTANT INSTRUCTIONS:
1. FILTER the GeoDataFrame to show ONLY features matching the query
2. Create a folium map centered on filtered results
3. Color filtered features in a BRIGHT distinctive color
4. Use .total_bounds of filtered data to zoom map correctly
5. Add tooltips showing DISTRICTENG and COMMUNITYENG
6. Add fullscreen button
7. Return ONLY the filtered GeoDataFrame if asked for data, or the Map if asked for visualization

Example filtering:
filtered = df_1[df_1['DISTRICTENG'].str.contains('query_term', case=False, na=False)]
"""
            elif output_type == "Interactive Map":
                enhanced_prompt = f"{user_input}. Include tooltips and fullscreen button."

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
            response_msg = {
                "role": "assistant",
                "text": f"✓ **{output_type} generated!**",
                "show_summary": show_summary,
                "show_table": show_data_table
            }

            # Generate summary
            if show_summary:
                summary = generate_summary(result, user_input, output_type)
                response_msg["summary"] = summary
                st.markdown(summary)

            # Display main result
            if output_type == "Interactive Map":
                # Add fullscreen
                try:
                    plugins.Fullscreen(position='topright', force_separate_button=True).add_to(result)
                except:
                    pass

                map_html = result._repr_html_()
                response_msg["map_html"] = map_html

                st.markdown(response_msg["text"])
                st.info("💡 Hover over features for details | 📐 Click fullscreen (top-right)")
                st.components.v1.html(map_html, height=600, scrolling=True)

                # Try to get the filtered data for the table
                if show_data_table:
                    st.markdown("---")
                    st.markdown("### 📋 Filtered Data")

                    # Try to extract filtered data from the generated code
                    # This is a best-effort attempt
                    try:
                        # Re-run the query to get the data
                        data_result = st.session_state.gdfai.chat(
                            f"{user_input}. Return the filtered GeoDataFrame.",
                            return_type=None
                        )

                        if isinstance(data_result, gpd.GeoDataFrame):
                            # Select only the columns user wants
                            display_cols = [col for col in table_columns if col in data_result.columns]
                            if display_cols:
                                table_data = data_result[display_cols].copy()
                                # Format geometry column
                                if 'geometry' in display_cols:
                                    table_data['geometry'] = table_data['geometry'].apply(lambda x: str(x)[:50] + '...' if x else '')

                                st.dataframe(table_data, use_container_width=True)
                                response_msg["data_table"] = table_data
                            else:
                                st.warning("Selected columns not found in data")
                    except Exception as e:
                        st.info("💡 Data table not available for this view. Try asking for specific data analysis.")

            elif output_type == "Static Plot":
                plot_path = f'plot_{st.session_state.chat_counter}.png'
                result.savefig(plot_path, dpi=150, bbox_inches='tight')
                plt.close()

                response_msg["plot_path"] = plot_path
                st.markdown(response_msg["text"])
                st.image(plot_path)

            else:  # Data Analysis
                response_msg["dataframe"] = result
                st.markdown(response_msg["text"])

                if isinstance(result, gpd.GeoDataFrame):
                    # Show main result
                    st.dataframe(result, use_container_width=True)

                    # Optionally show subset if table columns specified
                    if show_data_table and table_columns:
                        display_cols = [col for col in table_columns if col in result.columns]
                        if display_cols and len(display_cols) < len(result.columns):
                            st.markdown("---")
                            st.markdown("### 📋 Focused View (Selected Columns)")
                            subset = result[display_cols].copy()
                            if 'geometry' in display_cols:
                                subset['geometry'] = subset['geometry'].apply(lambda x: str(x)[:50] + '...' if x else '')
                            st.dataframe(subset, use_container_width=True)
                            response_msg["data_table"] = subset
                else:
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

# Examples
st.markdown("---")
with st.expander("💡 Example Queries"):
    st.markdown("""
    **Location queries (map + summary + table):**
    - "Show me the Al Nahyan district"
    - "Find all districts with 'East' in the name"
    - "Locate community E19_02"
    - "Highlight the largest district"

    **Data analysis:**
    - "How many features in each district?"
    - "Show me the top 5 largest areas"
    - "List all unique district names"

    **Improvements:**
    - "Make it bright red"
    - "Add a legend"
    - "Show more details"
    """)

with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown(f"**Queries:** {st.session_state.chat_counter}")
