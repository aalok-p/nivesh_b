from enum import Enum
from pydantic import BaseModel, Field, field_validator


class CityTier(str, Enum):
    tier_1 = "tier_1"
    tier_2 = "tier_2"
    tier_3 = "tier_3"


class EmploymentType(str, Enum):
    salaried = "salaried"
    self_employed = "self_employed"


class InstitutionType(str, Enum):
    scb = "SCB"
    sfb = "SFB"
    nbfc = "NBFC"
    other = "OTHER"


class DepositorType(str, Enum):
    general = "general"
    senior = "senior"


class FDInput(BaseModel):
    bank_name: str = Field(min_length=2, max_length=80)
    bank_slug: str | None = Field(default=None, max_length=80)
    institution_type: InstitutionType
    principal: float = Field(gt=0, le=100000000)
    tenure_months: int = Field(ge=1, le=120)
    remaining_months: int = Field(ge=0, le=120)
    annual_rate: float | None = Field(default=None, ge=1, le=20)
    depositor_type: DepositorType = DepositorType.general

    @field_validator("remaining_months")
    @classmethod
    def remaining_within_tenure(cls, value: int, info) -> int:
        tenure = info.data.get("tenure_months")
        if tenure is not None and value > tenure:
            raise ValueError("remaining_months cannot be greater than tenure_months")
        return value


class ApplicantProfile(BaseModel):
    applicant_name: str = Field(min_length=2, max_length=80)
    pan: str = Field(min_length=10, max_length=10)
    age: int = Field(ge=18, le=75)
    city_tier: CityTier
    employment_type: EmploymentType
    monthly_income: float = Field(gt=0, le=5000000)
    monthly_expense: float = Field(ge=0, le=5000000)
    avg_month_end_balance: float = Field(ge=0, le=10000000)
    emi_bounces_6m: int = Field(ge=0, le=12)

    @field_validator("pan")
    @classmethod
    def normalize_pan(cls, value: str) -> str:
        return value.strip().upper()


class PreQualRequest(BaseModel):
    profile: ApplicantProfile
    fds: list[FDInput] = Field(min_length=1, max_length=20)


class Breakdown(BaseModel):
    collateral_strength: int
    cashflow_stability: int
    tenure_quality: int
    kyc_readiness: int


class RouteOption(BaseModel):
    route: str
    rationale: str
    expected_speed: str
    expected_cost: str


class PreQualResponse(BaseModel):
    readiness_score: int
    decision: str
    eligible_loan_min: float
    eligible_loan_max: float
    ltv_applied: float
    annual_rate_band: str
    estimated_emi_12m: float
    suggested_path: str
    explanation: str
    breakdown: Breakdown
    routes: list[RouteOption]
    processing_ms: int
    source_mode: str


class SimulateRequest(BaseModel):
    base_request: PreQualRequest
    additional_fd_amount: float = Field(ge=0, le=10000000)
    additional_fd_bank: str = Field(default="SBI", min_length=2, max_length=80)
    additional_fd_type: InstitutionType = InstitutionType.scb
    additional_fd_tenure_months: int = Field(default=12, ge=1, le=120)


class SimulateResponse(BaseModel):
    base_score: int
    new_score: int
    base_eligible_loan_max: float
    new_eligible_loan_max: float
    delta_loan_amount: float
    message: str
