# Using GeoPandas-AI with Ollama

This guide explains how to get GeoPandas-AI working reliably with local Ollama models.

## TL;DR - Quick Fix

The issue with `llama3.1:8b` is that it's not good at following code generation instructions. Use a **code-specialized model** instead:

```bash
# Install a better model for code generation
ollama pull qwen2.5-coder:14b

# Then use it
python main_qwen_coder.py
```

## Why Smaller Models Fail

Models like `llama3.1:8b` often:
- Forget to import libraries (causing `NameError: name 'folium' is not defined`)
- Generate invalid Python syntax
- Don't follow the function signature requirements
- Hallucinate library names

## Recommended Ollama Models (Best to Worst)

### Excellent (14B+ parameters, code-specialized)
```bash
ollama pull qwen2.5-coder:14b      # ⭐ Best for Python/geospatial code
ollama pull deepseek-coder:33b     # Excellent but requires more RAM
ollama pull codellama:34b          # Meta's code-focused model
```

### Good (7B-13B parameters)
```bash
ollama pull qwen2.5-coder:7b       # Good balance of speed/quality
ollama pull deepseek-coder:6.7b    # Fast and decent quality
ollama pull codellama:13b          # Reasonable for simple tasks
```

### Unreliable (General purpose, not code-focused)
```bash
ollama pull llama3.1:8b            # ⚠️ Not recommended for code gen
ollama pull llama3:latest          # ⚠️ Better for chat, not code
ollama pull mistral:latest         # ⚠️ Inconsistent with imports
```

## Configuration Examples

### Option 1: Code-Specialized Model (Recommended)

```python
from geopandasai import update_geopandasai_config

update_geopandasai_config(
    lite_llm_config={
        "model": "openai/qwen2.5-coder:14b",
        "api_base": "http://127.0.0.1:11434/v1",
        "api_key": "ollama",
        "temperature": 0.0,  # More deterministic
    }
)
```

### Option 2: Cloud Model (Most Reliable)

If you need 100% reliability, use a cloud model like the examples do:

```python
import os

# OpenAI GPT-4 (best quality)
update_geopandasai_config(
    lite_llm_config={
        "model": "gpt-4o",
        "api_key": os.environ["OPENAI_API_KEY"],
    }
)

# OR Google Gemini (free tier available)
update_geopandasai_config(
    lite_llm_config={
        "model": "gemini/gemini-1.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
    }
)
```

## Troubleshooting

### Error: `name 'folium' is not defined`

**Cause**: LLM generated code using folium without importing it

**Solutions**:
1. Use a better code-focused model (qwen2.5-coder, deepseek-coder)
2. Exclude folium from libraries:
   ```python
   update_geopandasai_config(
       libraries=["pandas", "matplotlib.pyplot", "geopandas"],
       lite_llm_config={...}
   )
   ```
3. Use a more explicit prompt: "Use matplotlib.pyplot to create a plot..."

### Error: `Expected return type X, but got Y`

**Cause**: LLM returned wrong type

**Solution**: Explicitly specify return type:
```python
result = gdfai.chat("Plot the map", return_type=Figure)
```

## What Works Best

| Use Case | Recommended Model | Speed | Quality |
|----------|------------------|-------|---------|
| Production | gpt-4o (cloud) | Fast | ⭐⭐⭐⭐⭐ |
| Development | qwen2.5-coder:14b | Medium | ⭐⭐⭐⭐ |
| Testing | gemini-1.5-flash (cloud) | Very Fast | ⭐⭐⭐⭐⭐ |
| Budget/Offline | deepseek-coder:6.7b | Fast | ⭐⭐⭐ |
| Not Recommended | llama3.1:8b | Fast | ⭐⭐ |

## Hardware Requirements

| Model | Minimum RAM | Recommended |
|-------|------------|-------------|
| qwen2.5-coder:7b | 8 GB | 16 GB |
| qwen2.5-coder:14b | 16 GB | 32 GB |
| deepseek-coder:6.7b | 8 GB | 16 GB |
| deepseek-coder:33b | 32 GB | 64 GB |
| codellama:13b | 16 GB | 32 GB |
| codellama:34b | 32 GB | 64 GB |

## Testing Your Setup

Run the simple test to verify everything works:

```bash
python test_simple.py
```

This tests Ollama + geopandas-ai with minimal data before trying complex queries.

## Example Scripts

- `main_qwen_coder.py` - Uses qwen2.5-coder (recommended)
- `main_no_folium.py` - Matplotlib-only (works with any model)
- `main_simple.py` - Load from URL example
- `test_simple.py` - Simple test to verify setup
- `check_dependencies.py` - Check installation

## Still Having Issues?

1. Check Ollama is running: `ollama list`
2. Verify model is available: `ollama pull qwen2.5-coder:14b`
3. Test Ollama directly: `ollama run qwen2.5-coder:14b "Write a Python function to add two numbers"`
4. Consider using a cloud model for guaranteed reliability

## Bottom Line

**For "regular working" of the repo with Ollama:**
1. Install `qwen2.5-coder:14b` or `deepseek-coder:6.7b`
2. Use the configuration shown above
3. Be patient with local models (they're slower than cloud APIs)

**For best experience (like the examples):**
- Use a cloud model (GPT-4, Gemini, Claude)
- Local models work but require more powerful hardware and patience
