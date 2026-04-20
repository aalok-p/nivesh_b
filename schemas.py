from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class FDItem(BaseModel):
    fd_id: str
    banck_name: str
    principal: float
    interest_rate: float
    tenure_days: int
    maturity_days_left: int
    status: str = "active"

class Portfolio(BaseModel):
    rd_monthly_amount: float
    rd_on_time_count: int
    rd_total_installments: int

class Transaction(BaseModel):
    month: str
    inflow: float
    fd_topups: int = 0


class FeatureVector(BaseModel):
    fd_total_value: float
    weighted_tenure_remaining: float
    fd_count: int
    rd_consistency_score: float
    savings_streak_months: int
    topup_frequency: float
    txn_variance_coefficient: float
    maturity_concentration_risk: float


class ScoreBreakdown(BaseModel):
    collateral_strength: int
    savings_behaviour: int
    tenure_quality: int

class PreQualRequest(BaseModel):
    user_id: str


class PreQualResponse(BaseModel):
    pre_approved: bool
    fd_credit_score: float
    max_loan_amount: float
    ltv_applied: float
    interest_rate_band: str
    breakdown: ScoreBreakdown
    decision_ms: int
    explanation: str
    selected_lender_id: Optional[str] = None
    next_step: str = "trigger_vkyc"


class SimulateRequest(BaseModel):
    user_id: str
    additional_fd_amount: float = Field(ge=0, le=5000000)

class SimulateResponse(BaseModel):
    new_max_loan_amount: float
    delta_credit: float
    updated_ltv: float
    message: str


class ExplainRequest(BaseModel):
    user_id: str
    score: float
    top_positive: List[str]
    top_negative: List[str]


class ExplainResponse(BaseModel):
    explanation: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    token_type: str = "bearer"

class KYCTriggerRequest(BaseModel):
    user_id: str
    approved_amount: float

class KYCTriggerResponse(BaseModel):
    kyc_session_id: str
    status: str
    lender_id: str
    lender_name: str


class WebhookPayload(BaseModel):
    event: str
    user_id: str
    approved_amount: Optional[float] = None

class ScoreHistoryItem(BaseModel):
    user_id: str
    score: float
    max_loan_amount: float
    decision_ms: int


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
