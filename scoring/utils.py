import logging
import geopandas as gpd
from shapely.geometry import Point

logger = logging.getLogger(__name__)

LOCAL_EPSG = 32188  # NAD83 / MTM zone 8 (Montréal)

def convert_to_metric_crs(data):
    """Convert a GeoDataFrame or Point to metric CRS (EPSG:32188)."""
    if isinstance(data, Point):
        return gpd.GeoSeries([data], crs=4326).to_crs(epsg=LOCAL_EPSG).iloc[0]
    return data.to_crs(epsg=LOCAL_EPSG)


def convert_to_geo_crs(gdf):
    """Convert GeoDataFrame back to geographic CRS (EPSG:4326)."""
    return gdf.to_crs(epsg=4326)


def linear_decay(distance, threshold):
    """Linear 0–1 score: 1 at distance=0, 0 at distance≥threshold."""
    if distance is None:
        return 0.0
    if distance >= threshold:
        return 0.0
    return 1 - (distance / threshold)

def get_neighborhood_for_location(lat, lon):
    user_point = Point(lon, lat)
    neighborhoods = load_neighborhoods()
    neighborhood_row = neighborhoods[neighborhoods.contains(user_point)]

    if not neighborhood_row.empty:
        return neighborhood_row.iloc[0]["NOM"]
    else:
        logger.warning(f"no neighborhood found for the location {user_point} (assumed CRS: EPSG:4326)")
        return "Unknown"

def load_neighborhoods():
    """Load neighborhood polygons for Montréal from GeoJSON."""
    path = "data\processed\quartierreferencehabitation.geojson"
    neighborhoods = gpd.read_file(path)
    if neighborhoods.crs is None or neighborhoods.crs.to_epsg() != 4326:
        neighborhoods = neighborhoods.to_crs(epsg=4326)
    return neighborhoods
