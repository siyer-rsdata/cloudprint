import os

import uvicorn
from fastapi import FastAPI
from fastapi_utilities import repeat_every
from sqlmodel import SQLModel

from routers.cloudprint_methods import router
from setup import init
from database.cloudprint_db import db_engine
from backend.cron_methods import cloudprint_orders

app = FastAPI(title="Cloud Print Service - v2.0")

# Register router with the FastAPI app.
app.include_router(router)


@app.on_event('startup')
async def on_startup():
    init()

    # Create all database tables (SQLModels) during the startup, if they don't already exist.
    SQLModel.metadata.create_all(db_engine)

    # Fetch cloud print orders from the POTLAM backend
    await fetch_orders()


@repeat_every(seconds=30)
# @repeat_every(seconds=86400)
async def fetch_orders():
    await cloudprint_orders()

