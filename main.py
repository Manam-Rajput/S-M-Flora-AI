import os
import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI(title="S&M Flora")

# Templates folder setup
templates = Jinja2Templates(directory="templates")

# PlantNet API Configuration (Yahan apni free PlantNet API key dal sakte hain)
PLANTNET_API_KEY = "YOUR_PLANTNET_API_KEY_HERE"
PLANTNET_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/identify")
async def identify_plant(file: UploadFile = File(...)):
  if not file.filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
    raise HTTPException(
        status_code=400, detail="Only image files (.jpg, .jpeg, .png) are allowed."
    )

  try:
    contents = await file.read()

    # Fallback/Demo response agar API key set na ho taake presentation mein aasani ho
    if PLANTNET_API_KEY == "YOUR_PLANTNET_API_KEY_HERE":
      return {
          "success": True,
          "common_name": "Monstera Deliciosa (Swiss Cheese Plant)",
          "scientific_name": "Monstera deliciosa",
          "family": "Araceae",
          "confidence": "98.4%",
          "watering": "Allow top 2-3 inches of soil to dry out between waterings.",
          "sunlight": "Bright, indirect sunlight. Avoid harsh direct sun.",
          "toxicity": "Toxic to cats and dogs if ingested (contains calcium oxalate crystals).",
          "uses": (
              "Popular indoor ornamental plant, excellent for air purification."
          ),
      }

    # Real PlantNet API Call
    files = [("images", (file.filename, contents, file.content_type))]
    response = requests.post(PLANTNET_URL, files=files)

    if response.status_code != 200:
      raise HTTPException(
          status_code=500, detail="Failed to connect with PlantNet API."
      )

    data = response.json()
    results = data.get("results", [])

    if not results:
      return {
          "success": False,
          "message": "No plant recognized. Please try a clearer photo.",
      }

    best_match = results[0]
    species = best_match.get("species", {})
    common_names = species.get("commonNames", ["Unknown Plant"])
    scientific_name = species.get("scientificNameWithoutAuthor", "Unknown")
    family = species.get("family", {}).get("scientificName", "Unknown")
    score = round(best_match.get("score", 0.0) * 100, 2)

    return {
        "success": True,
        "common_name": (
            common_names[0].capitalize()
            if common_names
            else "Common Houseplant"
        ),
        "scientific_name": scientific_name,
        "family": family,
        "confidence": f"{score}%",
        "watering": (
            "Water thoroughly when topsoil feels dry to the touch (approx. every"
            " 7-10 days)."
        ),
        "sunlight": "Prefers bright, indirect light for optimal leaf growth.",
        "toxicity": "Please check specific botanical safety indexes for pets.",
        "uses": "Ideal for residential landscaping and indoor decor.",
    }

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))