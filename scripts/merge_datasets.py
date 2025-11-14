import geopandas as gpd
import pandas as pd

base = "data/processed/"

files = [
    base + "pois_all.geojson",
    base + "parks_clean.geojson",
    base + "bixi_clean.geojson",
    base + "food_clean.geojson"
]

gdfs = [gpd.read_file(f) for f in files]

merged = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)

merged.to_file(base + "pois_merged.geojson", driver="GeoJSON", encoding="utf-8")

print("Merged successfully into pois_merged.geojson")
