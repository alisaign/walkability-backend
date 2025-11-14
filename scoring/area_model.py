"""
area_model.py — Neighborhood-level walkability analysis.

Builds category-specific vector layers with distance-based scores, 
then combines them into one overlay for gradient map visualization.
"""

import logging
import geopandas as gpd
from shapely.geometry import box
import numpy as np

from scoring.utils import (
    convert_to_geo_crs,
    convert_to_metric_crs,
    linear_decay,
    load_neighborhoods,
    LOCAL_EPSG
)

logger = logging.getLogger(__name__)


def calculate_distance_scores(pois_category_m, polygon_m, threshold, spacing_m=100):
    """
    Create a vector layer of walkability scores within a neighborhood
    for one category, using linear decay with distance from nearest POI.
    """
    # Generate grid of square cells across the neighborhood (100m spacing)
    minx, miny, maxx, maxy = polygon_m.total_bounds
    xs = np.arange(minx, maxx, spacing_m)
    ys = np.arange(miny, maxy, spacing_m)

    cells = []
    scores = []

    for x in xs:
        for y in ys:
            # create square cell
            cell = box(x, y, x + spacing_m, y + spacing_m)
            if not cell.intersects(polygon_m.unary_union):
                continue

            # measure distance from the cell's center to the nearest POI
            center_pt = cell.centroid
            if pois_category_m.empty:
                score = 0.0
            else:
                dist = pois_category_m.distance(center_pt).min()
                score = linear_decay(dist, threshold)

            cells.append(cell)
            scores.append(score)

    # create GeoDataFrame of polygons with scores
    grid_gdf = gpd.GeoDataFrame({"score": scores, "geometry": cells}, crs=LOCAL_EPSG)
    return grid_gdf


def combine_category_layers(category_layers, weights):
    """
    Overlay and combine all category score layers into one weighted layer.
    Uses mean of scores weighted by category weights.
    """
    if not category_layers:
        return gpd.GeoDataFrame(columns=["score", "geometry"], crs=LOCAL_EPSG)

    # Join all grids on geometry index (assumes same sampling grid)
    combined = category_layers[0][["geometry"]].copy()
    combined["score_sum"] = 0.0
    combined["weight_sum"] = 0.0

    for i, layer in enumerate(category_layers):
        w = float(weights[i])
        combined = combined.join(layer["score"], rsuffix=f"_{i}")
        combined["score_sum"] += layer["score"] * w
        combined["weight_sum"] += w

    combined["score"] = np.where(combined["weight_sum"] > 0,
                                 combined["score_sum"] / combined["weight_sum"],
                                 0)
    combined = combined[["geometry", "score"]]
    return combined

def get_polygon_geometry(neighborhood_name):
    neighborhoods = load_neighborhoods()
    polygon = neighborhoods[neighborhoods["NOM"] == neighborhood_name]
    if polygon.empty:
        logger.error(f"Neighborhood '{neighborhood_name}' not found")
        return None
    return convert_to_metric_crs(polygon)
    

def analyze_walkability_by_neighborhood(neighborhood_name:str, pois:gpd.GeoDataFrame, categories:list, thresholds:list, weights:list):
    """
    Compute vector-based walkability score layer for a neighborhood polygon.

    Steps:
      1. Clip POIs to the neighborhood.
      2. For each category, compute a distance-decay score layer.
      3. Overlay and weight all layers into one composite layer.
      4. Convert back to EPSG:4326 for map rendering.
    """
    logger.info(f"Analyzing neighborhood: {neighborhood_name}")

    pois_m = convert_to_metric_crs(pois)
    neighborhood_polygon = get_polygon_geometry(neighborhood_name)
    # clip pois by neighborhood
    pois_neighborhood = pois_m[pois_m.within(neighborhood_polygon.unary_union)]

    # Build per-category layers
    category_layers = []
    for i, category in enumerate(categories):
        threshold = thresholds[i]
        pois_category = pois_neighborhood[pois_neighborhood["category"] == category]
        score_layer = calculate_distance_scores(pois_category, neighborhood_polygon, threshold)
        category_layers.append(score_layer)
        logger.info(f"Built layer for '{category}' ({len(score_layer)} points)")

    # 4. Combine weighted layers
    combined_layer_m = combine_category_layers(category_layers, weights)
    combined_layer_geo = convert_to_geo_crs(combined_layer_m)

    logger.info(f"Neighborhood walkability layer complete — {len(combined_layer_geo)} points total")
    return combined_layer_geo