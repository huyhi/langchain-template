from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from core.logging import setup_logging
from db.database import create_db_and_tables
from routes.chat import router as chat_router
from routes.health import router as health_router
from routes.threads import router as threads_router

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Rivus AI")
    create_db_and_tables()
    yield
    logger.info("Shutting down Rivus AI")


app = FastAPI(title="Rivus AI", version="0.1.0", lifespan=lifespan)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(threads_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
