import os
import cv2
import pytesseract
import numpy as np
import json
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


# Windows users must specify the correct path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


app = FastAPI(title="Statistical Chart Analyzer")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration for Open-WebUI API
WEBUI_ENABLED = True  # Set to True to use Open-WebUI API
WEBUI_BASE_URL = "https://chat.ivislabs.in/api"
API_KEY = "sk-d85003c7fe494d7c972b43be7d3d3e8e"  # Replace with your actual API key if needed
DEFAULT_MODEL = "gemma2:2b"  # Update to one of the available models

# Fallback to local Ollama API if needed
OLLAMA_ENABLED = True
OLLAMA_HOST = "localhost"
OLLAMA_PORT = "11434"
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api"

class TextAnalysisRequest(BaseModel):
    text: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """
    Extract text from an uploaded statistical chart image and generate a summary.
    """
    try:
        # Read the uploaded image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Convert image to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply OCR to extract text
        extracted_text = pytesseract.image_to_string(gray)

        if not extracted_text.strip():
            return {"error": "No text detected in the image"}

        # Generate AI summary of extracted text
        summary_response = await generate_ai_summary(extracted_text)

        return {"extracted_text": extracted_text, "summary": summary_response}

    except Exception as e:
        return {"error": str(e)}

async def generate_ai_summary(text: str):
    """
    Use Open-WebUI API or Ollama to generate a plain-language summary.
    """
    prompt = f"Summarize the following statistical chart information in simple terms:\n\n{text}"
    messages = [{"role": "user", "content": prompt}]

    if WEBUI_ENABLED:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{WEBUI_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={"model": DEFAULT_MODEL, "messages": messages},
                )
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "Summary not available.")
        except Exception as e:
            print(f"Error fetching summary from Open-WebUI: {str(e)}")

    if OLLAMA_ENABLED:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_API_URL}/generate",
                    json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
                )
            result = response.json()
            return result.get("response", "Summary not available.")
        except Exception as e:
            print(f"Error fetching summary from Ollama: {str(e)}")

    return "AI summary generation failed."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
