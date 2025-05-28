from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.db_ahandler import AsyncDatabaseHandler
from src.lib.logger import logger, setup_logger
from src.routes.delete_routes import router as delete_router
from src.routes.fetch_routes import router as fetch_router
from src.routes.insert_routes import router as insert_router

load_dotenv(override=True)

# Set up the logger
setup_logger()


# Lifespan event handler for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    db_handler = AsyncDatabaseHandler()
    try:
        await db_handler._connect()
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise RuntimeError("Database setup failed, shutting down API.") from e
    app.state.db_handler = db_handler
    try:
        yield
    finally:
        await db_handler._disconnect()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Include the routers
app.include_router(fetch_router, prefix="/procedures")
app.include_router(insert_router, prefix="/procedures")
app.include_router(delete_router, prefix="/procedures")
