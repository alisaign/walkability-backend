from pathlib import Path
import geopandas as gpd

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