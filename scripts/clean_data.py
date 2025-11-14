import geopandas as gpd
from pathlib import Path

def convert_to_geojson(shp_path: str, out_name: str, out_dir: str = "data/processed"):
    """
    Convert a shapefile dataset to GeoJSON in WGS84.
    
    Parameters
    ----------
    shp_path : str
        Path to the .shp file.
    out_name : str
        Output filename without extension (e.g. "stm_stops").
    out_dir : str
        Directory where GeoJSON should be saved.
    
    Returns
    -------
    str : Path to the created GeoJSON file.
    """
    
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    gdf = gpd.read_file(shp_path)

    # Reproject to WGS84 if needed
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    out_path = out_dir / f"{out_name}.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    print(f"Saved {out_path} with {len(gdf)} features")
    return str(out_path)

def prepare_transit_data():
    """Convert shapefile, clean, and save processed GeoJSON."""

    raw_metro_bus_path = Path("data/raw/stm_sig/stm_arrets_sig.shp")
    geojson_path=Path("data/processed/metro_bus.geojson")
    if not geojson_path.exists():
        geojson_path = convert_to_geojson(raw_metro_bus_path, "metro_bus")


    gdf = gpd.read_file(geojson_path)

    gdf = gdf[["stop_id", "stop_name", "route_id", "geometry"]]

    gdf = gdf.drop_duplicates(subset=["stop_id"])

    gdf["stop_name"] = gdf["stop_name"].astype(str).str.strip()
    gdf["route_id"] = gdf["route_id"].astype(str).str.strip()

    gdf = gdf[gdf["route_id"].notna()]  # remove NaN
    gdf = gdf[gdf["route_id"].astype(str).str.lower() != "none"]  # remove literal "None"
    gdf = gdf.rename(columns={"route_id":"routes"})
    gdf["routes"] = gdf["routes"].apply(lambda x: [r.strip() for r in str(x).split(",")])
    metro_lines = {"1", "2", "4", "5"}
    def classify_route(route_list):
        if any(route in metro_lines for route in route_list):
            return "metro"
        return "bus"
    gdf["category"] = gdf["routes"].apply(classify_route)
    
    gdf = gdf[["category", "stop_name", "geometry"]]

    out_dir = Path("data/processed")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "metro_bus_clean.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    
    print(gdf["category"].value_counts())

    print(f"Cleaned dataset saved to {out_path}")
    return out_path


prepare_transit_data()
