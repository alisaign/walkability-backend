import pandas as pd
import geopandas as gpd

all_layers = []
for path in ["data/processed/metro_bus_clean.geojson",
             #"data/processed/parks.geojson",
             #"data/processed/groceries.geojson"
]:
    gdf = gpd.read_file(path)
    all_layers.append(gdf)

pois_all = gpd.GeoDataFrame(pd.concat(all_layers, ignore_index=True))
pois_all.to_file("data/processed/pois_all.geojson", driver="GeoJSON")