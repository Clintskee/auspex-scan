from fastapi import FastAPI

from app.calculator import calculate_expected_damage
from app.models import DamageRequest, DamageResponse

app = FastAPI(
    title="40K Expected Damage API",
    version="0.2.0",
    description="A minimal Warhammer 40,000 11th-edition expected-damage calculator.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/expected-damage", response_model=DamageResponse)
def expected_damage(request: DamageRequest) -> DamageResponse:
    return calculate_expected_damage(request)
