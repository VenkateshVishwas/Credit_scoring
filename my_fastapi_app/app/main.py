from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agentRouter
from app.api.routes.knowledgebase import router as kbRouter
from app.api.routes.chat import router as chatRouter

app = FastAPI()

# ✅ Add this block to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Route registrations
app.include_router(agentRouter, prefix="/agent", tags=["Agent"])
app.include_router(kbRouter, prefix="/kb", tags=["Knowledgebase"])
app.include_router(chatRouter, prefix="/chat", tags=["Chat"])
