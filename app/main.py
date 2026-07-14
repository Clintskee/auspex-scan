"""FastAPI application and top-level service endpoints."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db_models  # noqa: F401
from app.calculator import calculate_expected_damage
from app.database import create_database
from app.models import DamageRequest, DamageResponse
from app.routers.calculations import router as calculations_router
from app.routers.units import router as units_router
from app.routers.weapons import router as weapons_router


@asynccontextmanager
async def lifespan(_application: FastAPI):
    """Create missing database tables when the application starts."""
    create_database()
    yield

app = FastAPI(
    title="40K Expected Damage API",
    version="0.2.0",
    description=(
        "A minimal Warhammer 40,000 11th-edition expected-damage calculator."
    ),
    lifespan=lifespan,
)

static_directory = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_directory), name="static")

app.include_router(units_router)
app.include_router(weapons_router)
app.include_router(calculations_router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the lightweight matchup calculator interface."""
    return FileResponse(static_directory / "index.html")


@app.get("/health", summary="Check service health")
def health() -> dict[str, str]:
    """Confirm that the API process can respond to requests."""
    return {"status": "ok"}


@app.post(
    "/v1/expected-damage",
    response_model=DamageResponse,
    summary="Calculate expected damage",
)
def expected_damage(request: DamageRequest) -> DamageResponse:
    """Calculate one weapon profile into one homogeneous defender."""
    return calculate_expected_damage(request)
