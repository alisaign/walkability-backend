from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
import json

import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import geopandas as gpd
from scoring.point_model import analyze_walkability_at_location
from scoring.area_model import analyze_walkability_by_neighborhood
from scoring.utils import get_neighborhood_for_location

from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s:%(funcName)s — %(message)s",
    datefmt="%H:%M:%S"
)

# --- Initialize FastAPI ---
app = FastAPI()

# --- Enable CORS for your GitHub Pages frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alisaign.github.io",  # your GitHub Pages URL
        "http://127.0.0.1:8000",      # optional, for local testing
        "http://localhost:8000"       # optional, for local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception handlers (for debugging) ---
@app.exception_handler(Exception)
async def debug_exception_handler(request, exc):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
# @app.exception_handler(Exception)
# async def debug_exception_handler(request, exc):
#     print("\n=== FULL EXCEPTION TRACEBACK ===")
#     traceback.print_exc()
#     print("================================\n")
#     return JSONResponse(
#         status_code=500,
#         content={"detail": str(exc)},
#     )
    
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     print("\n=== VALIDATION ERROR DETAIL ===")
#     print(json.dumps(exc.errors(), indent=2))
#     print("Raw body:", await request.body())
#     print("================================\n")
#     return JSONResponse(
#         status_code=422,
#         content={"detail": exc.errors()},
#     )

# # --- Serve static and template files ---
# frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
# app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
# templates = Jinja2Templates(directory="frontend")
# frontend_dir = Path(__file__).resolve().parent / "frontend"
# app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
# templates = Jinja2Templates(directory=frontend_dir)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend")
# app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
# app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")

# --- Load your dataset once ---
pois_gdf = gpd.read_file("data/pois.geojson")

# --- Define the structure of input data coming from frontend ---
class Location(BaseModel):
    name: str
    lat: float
    lon: float
    
class WalkabilityInput(BaseModel):
    location: Location
    categories: list
    thresholds: list
    weights: list

# --- Routes ---

# 1. Show your index page
@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/result", response_class=HTMLResponse)
def read_result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})

# 2. Endpoint that runs your scoring logic
@app.post("/api/analyze")
def analyze_walkability_api(data: WalkabilityInput):
    print("received data: ", data)
    result_point = analyze_walkability_at_location(
        lat=data.location.lat,
        lon=data.location.lon,
        categories=data.categories,
        thresholds=data.thresholds,
        weights=data.weights,
        pois=pois_gdf
    )
    neighborhood_name = get_neighborhood_for_location(data.location.lat, data.location.lon)
    gradient_layer = analyze_walkability_by_neighborhood(
        neighborhood_name=neighborhood_name,
        pois=pois_gdf,
        categories=data.categories,
        thresholds=data.thresholds,
        weights=data.weights,
    )
    
    # --- build frontend JSON format ---
    breakdown = []
    for i, category in enumerate(data.categories):
        breakdown.append({
            "name": category,
            "score": result_point["category_scores"][i],
            "weight": data.weights[i],
            "buffer": data.thresholds[i],  
            "nearest_dist": result_point["nearest_pois_distances_by_category"][i],
            "nearest_name": result_point["nearest_pois_names_by_category"][i],
            "nearby_count": result_point["nearby_pois_counts_by_category"][i],
        })
    print("formatted breakdown: ", breakdown)
    formatted_output = {
        "location": neighborhood_name,                   # name of neighborhood you found earlier
        "center": {"lat": data.location.lat, "lon": data.location.lon},
        "index": result_point["walkability_index"],
        "breakdown": breakdown,
        "buffers_m": data.thresholds,
        "nearby": result_point["all_pois_nearby"],
        "neighborhood": neighborhood_name,
        "gradient_layer": gradient_layer.__geo_interface__,  # optional: if you return gradient map too
    }
    #print("formatted output: ", formatted_output)
    output_path = Path("sample_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_output, f, indent=2)
    return formatted_output
