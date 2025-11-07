import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Fetch Abu Dhabi boundaries data
url = "https://onwani.abudhabi.ae/arcgis/rest/services/MSSI/ADMINBOUNDARIES/FeatureServer/0/query"
params = {
    'where': '1=1',
    'outFields': '*',
    'returnGeometry': 'true',
    'f': 'geojson',
    'spatialRel': 'esriSpatialRelIntersects'
}

print("Fetching data from API...")
response = requests.get(url, params=params, verify=False)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
print(f"Response Length: {len(response.text)} characters")
print("\nFirst 500 characters of response:")
print(response.text[:500])

try:
    geojson_data = response.json()
    print("\n✓ Response is valid JSON")
    print(f"Keys in response: {list(geojson_data.keys())}")

    # Check if it's proper GeoJSON
    if 'type' in geojson_data:
        print(f"GeoJSON type: {geojson_data['type']}")

    if 'features' in geojson_data:
        print(f"Number of features: {len(geojson_data['features'])}")
        if len(geojson_data['features']) > 0:
            print(f"First feature keys: {list(geojson_data['features'][0].keys())}")

    # Save to file
    with open('admin_boundaries.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)
    print("\n✓ Saved to admin_boundaries.geojson")

except json.JSONDecodeError as e:
    print(f"\n✗ Failed to parse JSON: {e}")
    print("Response is not valid JSON")
