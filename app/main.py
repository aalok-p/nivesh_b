from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.schemas import FDInput, PreQualRequest, PreQualResponse, SimulateRequest, SimulateResponse
from app.scoring import LoanReadinessEngine
from app.services import BlostemRatesClient


settings= get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
rates_client = BlostemRatesClient(settings=settings)
engine = LoanReadinessEngine(rates_client=rates_client)


@app.get("/health", response_model=str)
async def health() ->str:
    return "ok"

@app.post("/api/v1/prequal", response_model=PreQualResponse)
async def prequal(payload: PreQualRequest) -> PreQualResponse:
    return await engine.evaluate(payload)


@app.post("/api/v1/simulate", response_model=SimulateResponse)
async def simulate(payload: SimulateRequest) -> SimulateResponse:
    base_result = await engine.evaluate(payload.base_request)

    simulated_fds = list(payload.base_request.fds)
    simulated_fds.append(
        FDInput(
            bank_name=payload.additional_fd_bank,
            bank_slug=None,
            institution_type=payload.additional_fd_type,
            principal=payload.additional_fd_amount,
            tenure_months=payload.additional_fd_tenure_months,
            remaining_months=payload.additional_fd_tenure_months,
            annual_rate=None,
            depositor_type="general",
        )
    )
    simulated_request = PreQualRequest(profile=payload.base_request.profile, fds=simulated_fds)
    new_result = await engine.evaluate(simulated_request)
    delta = round(new_result.eligible_loan_max - base_result.eligible_loan_max, 2)

    return SimulateResponse(
        base_score=base_result.readiness_score,
        new_score=new_result.readiness_score,
        base_eligible_loan_max=base_result.eligible_loan_max,
        new_eligible_loan_max=new_result.eligible_loan_max,
        delta_loan_amount=delta,
        message=f"Adding this FD can increase upper eligibility by INR {delta:,.0f}.",
    )
