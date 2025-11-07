#!/usr/bin/env python3
"""Check if all required dependencies for geopandas-ai are installed."""

import sys

def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False

def main():
    print("="*60)
    print("Checking geopandas-ai dependencies...")
    print("="*60)

    required = [
        ("geopandas", "geopandas"),
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("geopandasai", "geopandasai"),
    ]

    optional = [
        ("folium", "folium"),
        ("contextily", "contextily"),
        ("litellm", "litellm"),
    ]

    print("\nRequired packages:")
    required_ok = all(check_package(name, imp) for name, imp in required)

    print("\nOptional packages:")
    optional_results = {name: check_package(name, imp) for name, imp in optional}

    print("\n" + "="*60)
    print("Summary:")
    print("="*60)

    if required_ok:
        print("✓ All required packages are installed")
    else:
        print("✗ Some required packages are missing")
        print("\nInstall missing packages with:")
        print("  pip install geopandas pandas matplotlib geopandasai")

    if not optional_results.get("folium", False):
        print("\n⚠ Folium is not installed")
        print("  - To create interactive maps, install it: pip install folium")
        print("  - OR use matplotlib for static plots (already configured)")

    if not optional_results.get("contextily", False):
        print("\n⚠ Contextily is not installed (optional)")
        print("  - For basemap tiles, install it: pip install contextily")

    print("\n" + "="*60)
    print("Ollama Configuration:")
    print("="*60)

    import subprocess
    try:
        result = subprocess.run(
            ['curl', '-s', 'http://127.0.0.1:11434/api/tags'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            print("✓ Ollama server is running")
            import json
            try:
                data = json.loads(result.stdout)
                if 'models' in data:
                    print(f"  Available models: {len(data['models'])}")
                    for model in data['models'][:5]:
                        print(f"    - {model.get('name', 'unknown')}")
            except:
                pass
        else:
            print("✗ Ollama server is not responding")
            print("  Start it with: ollama serve")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Cannot connect to Ollama")
        print("  Make sure Ollama is installed and running")
        print("  Start with: ollama serve")
        print("  Check with: ollama list")

    print("="*60)

if __name__ == "__main__":
    main()
