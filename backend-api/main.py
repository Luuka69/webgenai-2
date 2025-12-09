import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:5005")
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8011"))

app = FastAPI(title="WebGen AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/generate")
async def generate(request: Request):
    data = await request.json()
    description = data.get("description", "").strip()

    if not description:
        return {"error": "Description is required"}

    timeout = httpx.Timeout(600.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{AI_ENGINE_URL}/process",
                json={"description": description},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"AI engine returned {exc.response.status_code}: {exc.response.text}"
            }
        except httpx.RequestError as exc:
            return {"error": f"Backend could not reach AI engine: {exc}"}

    try:
        return response.json()
    except ValueError:
        return {"error": "AI engine returned invalid JSON"}


@app.get("/")
def root():
    return {"message": "WebGen AI Backend running", "ai_engine_url": AI_ENGINE_URL}


@app.get("/api/screens")
async def list_screens():
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{AI_ENGINE_URL}/screens")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"AI engine returned {exc.response.status_code}: {exc.response.text}"
            }
        except httpx.RequestError as exc:
            return {"error": f"Backend could not reach AI engine: {exc}"}
    try:
        return response.json()
    except ValueError:
        return {"error": "AI engine returned invalid JSON"}


from fastapi import Request


@app.get("/api/screens/{screen_id}")
async def get_screen(screen_id: str, request: Request):
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{AI_ENGINE_URL}/screens/{screen_id}", params=request.query_params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"AI engine returned {exc.response.status_code}: {exc.response.text}"
            }
        except httpx.RequestError as exc:
            return {"error": f"Backend could not reach AI engine: {exc}"}
    try:
        return response.json()
    except ValueError:
        return {"error": "AI engine returned invalid JSON"}


@app.get("/api/workflows")
async def list_workflows():
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{AI_ENGINE_URL}/workflows")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"AI engine returned {exc.response.status_code}: {exc.response.text}"
            }
        except httpx.RequestError as exc:
            return {"error": f"Backend could not reach AI engine: {exc}"}
    try:
        return response.json()
    except ValueError:
        return {"error": "AI engine returned invalid JSON"}


@app.get("/api/workflows/{wf_id}/screens")
async def list_workflow_screens(wf_id: str):
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(f"{AI_ENGINE_URL}/workflows/{wf_id}/screens")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return {
                "error": f"AI engine returned {exc.response.status_code}: {exc.response.text}"
            }
        except httpx.RequestError as exc:
            return {"error": f"Backend could not reach AI engine: {exc}"}
    try:
        return response.json()
    except ValueError:
        return {"error": "AI engine returned invalid JSON"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)
