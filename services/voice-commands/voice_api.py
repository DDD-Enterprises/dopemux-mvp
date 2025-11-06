#!/usr/bin/env python3
"""
Voice Commands API Server
FastAPI server for voice-activated task decomposition
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
import asyncio
import uvicorn
import os

from voice_task_decomposer import VoiceTaskDecomposer
from conport_integration import VoiceConPortIntegration

app = FastAPI(title="Voice Commands API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VoiceCommandRequest(BaseModel):
    voice_input: str
    user_id: str = "default"

class VoiceCommandResponse(BaseModel):
    success: bool
    task_description: str = None
    decomposition: Dict[str, Any] = None
    voice_response: str = None
    sub_tasks: List[Dict[str, Any]] = None
    conport_result: Dict[str, Any] = None
    error: str = None

@app.post("/api/v1/decompose-task", response_model=VoiceCommandResponse)
async def decompose_task(request: VoiceCommandRequest):
    """Decompose a task using voice command processing and store in ConPort"""

    try:
        zen_url = os.getenv("ZEN_URL", "http://localhost:3003")
        conport_url = os.getenv("CONPORT_URL", "http://localhost:3004")
        workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

        async with VoiceTaskDecomposer(zen_url) as decomposer, VoiceConPortIntegration(conport_url) as conport:
            result = await decomposer.process_voice_command(
                request.voice_input,
                request.user_id
            )

            if result["success"]:
                # Store in ConPort
                conport_result = await conport.store_voice_decomposition(
                    user_id=request.user_id,
                    original_task=result["task_description"],
                    decomposition=result["decomposition"],
                    workspace_id=workspace_id
                )

                return VoiceCommandResponse(
                    success=True,
                    task_description=result["task_description"],
                    decomposition=result["decomposition"],
                    voice_response=result["voice_response"],
                    sub_tasks=result["sub_tasks"],
                    conport_result=conport_result
                )
            else:
                return VoiceCommandResponse(
                    success=False,
                    error=result["response"]
                )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice decomposition failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "voice-commands"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3007"))
    uvicorn.run(
        "voice_api:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True
    )