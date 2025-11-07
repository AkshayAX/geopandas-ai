# GeoPandas-AI with Ollama Testing Report

## How the Repo Works

### Basic Architecture
1. User asks a question in natural language
2. LLM generates Python code based on the question
3. Code is executed on your GeoDataFrame
4. Result is returned (map, plot, or data)

### Key Methods
- `gdfai.chat(prompt)` - Start a new conversation
- `gdfai.improve(prompt)` - Refine previous result
- `gdfai.code` - View generated Python code
- `gdfai.reset()` - Clear conversation history

### What It Returns
- **Maps**: Folium interactive maps (HTML)
- **Plots**: Matplotlib figures (PNG)
- **Data**: GeoDataFrame results

**Important**: The repo does NOT automatically generate summaries or data tables - it only returns what the LLM generates.

---

## What We Tested

### 1. Setup with Ollama ✅
- Installed `qwen2.5-coder:14b`
- Configured GeoPandas-AI to use local model
- Loaded Abu Dhabi administrative boundaries (100 features sample)

### 2. Basic Map Creation ⚠️
**Query**: "Create an interactive map"

**Result**: Generated a map but:
- Showed ALL features (no filtering)
- No tooltips by default
- No zoom to specific area

### 3. Location-Specific Queries ❌

#### Query 1: "Show me AL NAHYAN district"
**What should happen**: Filter to AL NAHYAN, zoom to it, highlight it

**What actually happened**:
- Map showed all districts (no filtering)
- Used hardcoded coordinates instead of calculating from data
- Didn't zoom to the queried location

**Generated code had issues**:
```python
# LLM generated this (WRONG):
m = folium.Map(location=[25.276987, 55.296249])  # Random coordinates!
for _, row in df_1.iterrows():  # Loops through ALL data
    folium.GeoJson(row['geometry']).add_to(m)
```

#### Query 2: "Show me areas in ZAYED CITY"
**What happened**:
- No filtering applied
- Same hardcoded coordinates
- Showed entire dataset

### 4. Tooltips ❌
**Issue**: LLM often forgot to add tooltips or added them incorrectly

**Sometimes generated**:
```python
# Missing folium import!
def execute(df_1):
    m = folium.Map()  # ❌ NameError: name 'folium' is not defined
```

### 5. Empty Results ❌
**Query**: District that doesn't exist

**Problem**: Generated map code even with 0 results, causing:
```
KeyError: 'features'
```

---

## What Went Wrong

### Issue 1: No Data Filtering
**Problem**: LLM plots all data instead of filtering

**Expected**:
```python
# Filter first
filtered = df_1[df_1['DISTRICTENG'].str.contains('ZAYED', case=False)]

# Then create map
m = folium.Map(...)
folium.GeoJson(filtered).add_to(m)
```

**Got**:
```python
# No filtering!
m = folium.Map(location=[hardcoded])
for _, row in df_1.iterrows():  # All data!
    folium.GeoJson(row['geometry']).add_to(m)
```

### Issue 2: Wrong Zoom/Center
**Problem**: Uses random coordinates instead of calculating from data

**Should calculate**:
```python
bounds = filtered_data.total_bounds
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2
```

**Instead uses**:
```python
location=[25.276987, 55.296249]  # Where did this come from?
```

### Issue 3: Missing Imports
**Problem**: Uses libraries without importing them

```python
def execute(df_1):
    m = folium.Map()  # folium never imported!
```

**Error**: `NameError: name 'folium' is not defined`

### Issue 4: No Validation
**Problem**: Generates map code even when filter returns 0 results

**Result**: Crashes with `KeyError: 'features'`

---

## Why Small Local Models Fail

### 1. Code Generation Quality
**Spatial code requires**:
- Data filtering (pandas operations)
- Coordinate calculations
- Bounds calculations
- Library-specific syntax (folium, matplotlib)

**qwen2.5-coder:14b (14B parameters)**:
- ❌ Forgets to filter data
- ❌ Hardcodes coordinates
- ❌ Misses import statements
- ❌ Doesn't handle empty results

### 2. Instruction Following
**GeoPandas-AI needs**:
- Multi-step operations (filter → calculate → create map)
- Following specific formats
- Using correct column names from data

**Small models**:
- ⚠️ Skip filtering steps
- ⚠️ Ignore bounds calculation
- ⚠️ Generate generic code that doesn't match request

### 3. Context Understanding
**User says**: "Show me ZAYED CITY"

**Model should understand**: Filter data → Calculate center from filtered → Zoom to filtered area

**Model actually does**: Show everything → Use random coordinates

---

## Our Workaround: Hardcoded Approach

Since the LLM generates unreliable code, we built a hardcoded solution:

### How It Works
1. **LLM only filters data** (simple task it can handle)
2. **Python code creates the map** (reliable, not LLM)
3. **We manually add**: zoom calculation, tooltips, summaries, tables

### Example
```python
# Step 1: LLM filters (all it does)
filtered = gdfai.chat("Return rows where DISTRICTENG contains ZAYED")

# Step 2: We create the map (not LLM)
bounds = filtered.total_bounds
center = [(bounds[1]+bounds[3])/2, (bounds[0]+bounds[2])/2]

m = folium.Map(location=center, zoom_start=13)  # We calculate zoom
folium.GeoJson(filtered,
               tooltip=folium.GeoJsonTooltip(['DISTRICTENG'])).add_to(m)  # We add tooltips

# Step 3: We create summary (not LLM)
summary = f"Found {len(filtered)} features in {filtered['DISTRICTENG'].nunique()} districts"

# Step 4: We create table (not LLM)
table = filtered[['DISTRICTENG', 'COMMUNITYENG']]
```

### Pros
- ✅ Reliable - always works
- ✅ Correct zoom every time
- ✅ Tooltips always present
- ✅ Summaries and tables always shown

### Cons
- ❌ Hardcoded to Abu Dhabi dataset (uses `DISTRICTENG`, `COMMUNITYENG` columns)
- ❌ Won't work with other datasets
- ❌ Not generic - defeats GeoPandas-AI's purpose
- ❌ Need to update code if dataset structure changes

### Files Created
- `app_fixed.py` - Hardcoded version that works reliably
- `app_generic.py` - Original approach (unreliable with local models)

---

## Does the Repo Generate Summaries?

**No.** The repo returns whatever the LLM generates.

If you ask: "Create a map", you get ONLY a map.

The summaries and data tables we showed are **custom additions** we built to compensate for the LLM's shortcomings.

**Standard repo behavior**:
```python
result = gdfai.chat("Show me AL NAHYAN")
# Returns: folium.Map object (that's it - no summary, no table)
```

**Our enhanced version**:
```python
# We manually add:
summary = generate_summary(result)  # Our code
table = extract_data_table(result)   # Our code
```

---

## Comparison: What Works

| Feature | Tested? | Works with Local Model? | Notes |
|---------|---------|-------------------------|-------|
| Basic map creation | ✅ Yes | ⚠️ Partial | Creates map but no filtering |
| Location filtering | ✅ Yes | ❌ No | Doesn't filter, shows all data |
| Auto-zoom to results | ✅ Yes | ❌ No | Uses random coordinates |
| Tooltips | ✅ Yes | ❌ Often missing | Inconsistent |
| Empty result handling | ✅ Yes | ❌ No | Crashes |
| Summaries | ❌ Not tested | N/A | Repo doesn't do this |
| Data tables | ❌ Not tested | N/A | Repo doesn't do this |
| Static plots | ❌ Not tested | Unknown | - |
| .improve() refinement | ❌ Not tested | Unknown | - |
| Multiple datasets | ❌ Not tested | Unknown | - |

---

## Options for Using Local Models

### Option 1: Accept Limitations
- Use for simple "show all data" queries
- Don't expect filtering or zoom to work
- Manually verify results

### Option 2: Hardcode Everything (What We Did)
- LLM only does simple filtering
- Python handles visualization
- Works reliably BUT:
  - Not generic
  - Dataset-specific
  - Maintenance burden

### Option 3: Use Larger Models
```bash
ollama pull qwen2.5-coder:32b  # Requires 32GB+ RAM
ollama pull deepseek-coder:33b # Better code generation
```

**Tradeoff**: Better quality but slower (60-120 seconds per query)

### Option 4: Switch to Cloud Models
```python
update_geopandasai_config(
    lite_llm_config={
        "model": "gpt-4o-mini",
        "api_key": os.environ["OPENAI_API_KEY"],
    }
)
```

**Works as designed** - no hardcoding needed.

---

## Bottom Line

### What We Learned
1. **GeoPandas-AI works** - but needs capable LLMs
2. **Small local models (8-14B)** generate incorrect code for spatial queries
3. **Workaround exists** - hardcode the map creation, let LLM filter only
4. **Hardcoding works** - but defeats the "chat with any data" purpose
5. **Cloud models** - would work properly (but we didn't test them)

### Recommendations
**For generic geospatial chat**:
- Use cloud models (GPT-4, Claude)
- Local models can't reliably handle it

**For specific use case with local models**:
- Use hardcoded approach
- Accept it only works with your specific dataset
- Update code when dataset structure changes

### Reality Check
The repo is designed for **cloud LLMs**. Using it with small local models requires significant compromises that negate its main value proposition.
