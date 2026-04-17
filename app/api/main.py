# Purpose: Main API application for dashboard, allows for live weight updates and portfolio customization


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router


app = FastAPI(
    title="Portfolio Risk API",
    description="API for risk dashboard",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["portfolio"])
