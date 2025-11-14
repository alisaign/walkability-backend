import json
import geopandas as gpd
from pathlib import Path
from shapely.geometry import mapping

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(exist_ok=True)


# ----------------------------------------
# 1. CLEAN PARKS (GeoJSON polygons)
# ----------------------------------------
def clean_parks():
    gdf = gpd.read_file(RAW / "parks.geojson")

    # Keep only "Nom" → "name" and geometry
    gdf = gdf[["Nom", "geometry"]].rename(columns={"Nom": "name"})
    gdf["category"] = "park"

    gdf.to_file(OUT / "parks_clean.geojson", driver="GeoJSON")


# ----------------------------------------
# 2. CLEAN BIXI (JSON → GeoJSON)
# ----------------------------------------
def clean_bixi():
    with open(RAW / "bixi.json", "r", encoding="utf8") as f:
        data = json.load(f)

    features = []

    for station in data["stations"]:
        name = station["s"]
        lon, lat = station["lo"], station["la"]

        features.append({
            "type": "Feature",
            "properties": {
                "category": "bixi",
                "name": name
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(OUT / "bixi_clean.geojson", "w", encoding="utf8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)


# ----------------------------------------
# 3. CLASSIFY GROCERY / RESTAURANT
# ----------------------------------------
grocery_keywords = [
    "Épicerie",
    "Supermarché",
    "Boucherie",
    "Magasin",
    "dépanneur",
    "épicerie"
]

restaurant_keywords = [
    "Restaurant",
    "service rapide",
    "Brasserie",
    "Bistro",
    "Bar",
    "taverne"
]


def classify_food_type(t):
    if t is None:
        return None

    t_lower = t.lower()

    for kw in grocery_keywords:
        if kw.lower() in t_lower:
            return "grocery"

    for kw in restaurant_keywords:
        if kw.lower() in t_lower:
            return "restaurant"

    return None  # ignore non-food entries (garderie, centre d'accueil, etc)


# ----------------------------------------
# 4. CLEAN GROCERIES + RESTAURANTS
# ----------------------------------------
def clean_food():
    gdf = gpd.read_file(RAW / "groceries_restaurants.geojson")

    features = []

    for _, row in gdf.iterrows():
        cat = classify_food_type(row["type"])
        if cat is None:
            continue  # skip items outside grocery/restaurant categories

        name = row["name"]
        geom = row["geometry"]
        if geom is None:
            continue


        # Convert shapely geometry to dict
        geom_json = mapping(geom)

        features.append({
            "type": "Feature",
            "properties": {
                "category": cat,
                "name": name
            },
            "geometry": geom_json
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(OUT / "food_clean.geojson", "w", encoding="utf8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

# clean_parks()
clean_food()
# clean_bixi()
# ----------------------------------------
# RUN EVERYTHING
# ----------------------------------------
# if __name__ == "__main__":
#     clean_parks()
#     clean_bixi()
#     clean_food()
