"""

"""

import logging
import geopandas as gpd
from shapely.geometry import Point

from scoring.utils import (
    convert_to_geo_crs,
    convert_to_metric_crs,
    linear_decay,
)

logger = logging.getLogger(__name__)



def calculate_category_score(pois_with_dist: gpd.GeoDataFrame, category: str, threshold: float):
    """Calculate a 0-1 score for given category."""
    subset_m = pois_with_dist[pois_with_dist["category"] == category]
    if subset_m.empty:
        logger.info(f"{category}: no POIs, score=0.000")
        return 0.0
    nearest = float(subset_m["distance"].min())
    score = linear_decay(nearest, threshold)
    logger.info(f"{category}: nearest={nearest:.1f} m, score={score:.3f}" if nearest is not None
                else f"{category}: no POIs, score=0.000")
    return score

def combine_scores(scores, weights):
    """Weighted mean of category scores (0–100)."""
    total_w = sum(weights)
    if not total_w:
        return 0.0
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    index = round(100 * weighted_sum / total_w, 1)
    logger.info(f"Combined index={index}")
    return index

def get_nearby_pois(pois_with_dist: gpd.GeoDataFrame, category: str, threshold: float):
    """Return list of POIs in geo crs within threshold meters of user_point."""
    nearby_pois_m = pois_with_dist[
        (pois_with_dist["category"] == category)
        & (pois_with_dist["distance"] <= threshold)
    ]
    if nearby_pois_m.empty:
        return []
    nearby_pois = convert_to_geo_crs(nearby_pois_m)
    nearby_pois_list = []
    for _, row in nearby_pois.iterrows():
        nearby_pois_list.append({
            "category": category,
            "name": row.get("name") or row.get("stop_name"),
            "distance": round(float(row["distance"]), 1),
            "geometry": row["geometry"].__geo_interface__,
        })
    logger.info(f"{category}: {len(nearby_pois_list)} nearby POIs ≤ {threshold} m")
    return nearby_pois_list


def find_nearest_pois(pois_with_dist: gpd.GeoDataFrame, categories: list):
    """Return nearest POI info (name + distance) for each category."""
    nearest_pois_names, nearest_pois_distances = [], []
    for category in categories:
        subset = pois_with_dist[pois_with_dist["category"] == category]
        if subset.empty:
            nearest_pois_names.append(None)
            nearest_pois_distances.append(None)
            continue
        nearest_row = subset.loc[subset["distance"].idxmin()]
        nearest_pois_names.append(nearest_row.get("name"))
        nearest_pois_distances.append(round(float(nearest_row["distance"]), 1))
    return nearest_pois_names, nearest_pois_distances


def analyze_walkability_at_location(lat:float, lon:float, categories:list, thresholds:list, weights:list, pois:gpd.GeoDataFrame):
    """Compute walkability index for a given location.
      1. Calculates category scores (linear decay).
      2. Finds nearby POIs for each category: 
        name and distance of the nearest poi, 
        and number of pois within the buffer.
      3. Calculates walkability score
      4. Returns parallel lists for all metrics
    """
    logger.info(f"Analyzing walkability for lat={lat}, lon={lon}")
    user_point = Point(lon, lat)
    
    # Adds one 'distance' column (meters) to POI dataset for this user point
    pois_m = convert_to_metric_crs(pois.copy())
    user_point_m = convert_to_metric_crs(user_point)
    pois_m["distance"] = pois_m.distance(user_point_m)
    
    category_scores = []
    nearest_pois_names = []
    nearest_pois_distances = []
    nearby_pois_counts = []
    all_pois_nearby = []

    for i, category in enumerate(categories):
        threshold = thresholds[i]
        weight = weights[i]
        if weight <= 0:
            category_scores.append(0.0)
            nearest_pois_names.append(None)
            nearest_pois_distances.append(None)
            nearby_pois_counts.append(0)
            continue

        score = calculate_category_score(pois_m, category, threshold)
        nearby_pois = get_nearby_pois(pois_m, category, threshold)
        
        category_scores.append(score)
        nearby_pois_counts.append(len(nearby_pois))
        all_pois_nearby.extend(nearby_pois)
        
    nearest_pois_names, nearest_pois_distances = find_nearest_pois(pois_m, categories)

    walkability_index = combine_scores(category_scores, weights)  

    result = {
        "walkability_index": walkability_index,
        "category_scores": category_scores,
        "nearest_pois_names_by_category": nearest_pois_names,
        "nearest_pois_distances_by_category": nearest_pois_distances,
        "nearby_pois_counts_by_category": nearby_pois_counts,
        "all_pois_nearby": all_pois_nearby
    }
    logger.info(f"Analysis complete: {len(all_pois_nearby)} total nearby POIs")
    return result
