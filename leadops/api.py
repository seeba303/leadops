"""Local HTTP interface. Stateless qualification; no outreach or persistence."""

from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .core import EMAIL, score_lead

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class Lead(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: Text
    email: Text
    company: Text
    industry: Text
    company_size: Annotated[int, Field(ge=1, le=100_000_000)]
    job_title: Text
    source: Text

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.casefold()
        if not EMAIL.fullmatch(value):
            raise ValueError("invalid email")
        return value


class Batch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    leads: Annotated[list[Lead], Field(min_length=1, max_length=100)]


class Decision(Lead):
    score: int
    reasons: list[str]
    segment: Literal["HOT", "WARM", "COLD"]
    next_action: Literal["sales_review", "nurture_review", "research"]


class BatchResult(BaseModel):
    processed: int
    duplicates: int
    decisions: list[Decision]


def create_app() -> FastAPI:
    app = FastAPI(
        title="LeadOps",
        version="0.2.0",
        description="Explainable lead qualification. No external actions.",
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # FastAPI's default errors include input values. Omit contact data.
        return JSONResponse(
            status_code=422,
            content={
                "detail": [
                    {"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]}
                    for e in exc.errors()
                ]
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/qualify", response_model=BatchResult)
    def qualify(batch: Batch) -> BatchResult:
        seen: set[str] = set()
        decisions = []
        for lead in batch.leads:
            if lead.email in seen:
                continue
            seen.add(lead.email)
            decisions.append(Decision(**score_lead(lead.model_dump())))
        return BatchResult(
            processed=len(decisions),
            duplicates=len(batch.leads) - len(decisions),
            decisions=decisions,
        )

    return app


app = create_app()
