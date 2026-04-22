from dataclasses import dataclass
from time import perf_counter

from schemas import Breakdown, PreQualRequest, PreQualResponse, RouteOption
from services import BlostemRatesClient


@dataclass
class ProcessedFD:
    principal: float
    collateral_value: float
    annual_rate: float
    remaining_months: int
    source: str


class LoanReadinessEngine:
    def __init__(self, rates_client: BlostemRatesClient) -> None:
        self.rates_client = rates_client

    async def evaluate(self, request: PreQualRequest) -> PreQualResponse:
        started = perf_counter()
        processed_fds = []

        for fd in request.fds:
            rate_resolution = await self.rates_client.resolve_fd_rate(fd)
            haircut = self.institution_haircut(fd.institution_type.value)
            lock_factor =self.lock_factor(fd.remaining_months)
            collateral = fd.principal * haircut * lock_factor
            processed_fds.append(
                ProcessedFD(
                    principal=fd.principal,
                    collateral_value=collateral,
                    annual_rate=rate_resolution.annual_rate,
                    remaining_months=fd.remaining_months,
                    source=rate_resolution.source,
                )
            )

        collateral_strength = self.collateral_strength(processed_fds)
        cashflow_stability = self.cashflow_stability(request)
        tenure_quality = self.tenure_quality(processed_fds)
        kyc_readiness =100 if len(request.profile.pan) == 10 else 45

        readiness_score = round(
            0.45 * collateral_strength
            + 0.30 * cashflow_stability
            + 0.15 * tenure_quality
            + 0.10 * kyc_readiness
        )

        ltv = self.ltv_from_score(readiness_score)
        total_collateral = sum(item.collateral_value for item in processed_fds)
        eligible_max = round(total_collateral * ltv, 2)
        eligible_min = round(eligible_max * 0.8, 2)
        annual_rate_band = self.rate_band(readiness_score)
        estimated_emi_12m =round((eligible_max / 12.0) * 1.06, 2)
        decision = self.decision(readiness_score, eligible_max)
        suggested_path = self.path(readiness_score)
        explanation = self.explanation(readiness_score, collateral_strength, cashflow_stability)

        source_mode = (
            "blostem_live"
            if any(fd.source=="blostem_api" for fd in processed_fds)
            else "mock_or_fallback"
        )

        ended =perf_counter()
        return PreQualResponse(
            readiness_score=readiness_score,
            decision=decision,
            eligible_loan_min=eligible_min,
            eligible_loan_max=eligible_max,
            ltv_applied=ltv,
            annual_rate_band=annual_rate_band,
            estimated_emi_12m=estimated_emi_12m,
            suggested_path=suggested_path,
            explanation=explanation,
            breakdown=Breakdown(
                collateral_strength=collateral_strength,
                cashflow_stability=cashflow_stability,
                tenure_quality=tenure_quality,
                kyc_readiness=kyc_readiness,
            ),
            routes=self._route_options(),
            processing_ms=int((ended - started) * 1000),
            source_mode=source_mode,
        )

    @staticmethod
    def institution_haircut(inst_type: str) -> float:
        mapping = {"SCB": 0.90, "SFB": 0.86, "NBFC": 0.80, "OTHER": 0.74}
        return mapping[inst_type]

    @staticmethod
    def lock_factor(remaining_months: int) -> float:
        if remaining_months > 24:
            return 0.90
        if remaining_months > 12:
            return 0.95
        return 1.0

    @staticmethod
    def collateral_strength(fds: list[ProcessedFD]) -> int:
        total_collateral = sum(fd.collateral_value for fd in fds)
        score = min(100, int((total_collateral / 800000) * 100))
        diversification_bonus = min(8, len(fds) * 2)
        return min(100, score + diversification_bonus)

    @staticmethod
    def cashflow_stability(request: PreQualRequest) -> int:
        profile = request.profile
        savings_ratio = max(0.0, min(1.0, (profile.monthly_income - profile.monthly_expense) / profile.monthly_income))
        buffer_ratio = min(1.0, profile.avg_month_end_balance / max(profile.monthly_expense, 1))
        bounce_penalty = min(0.4, profile.emi_bounces_6m * 0.08)
        base = 100 * (0.65 * savings_ratio + 0.35 * buffer_ratio)
        adjusted = int(base * (1 - bounce_penalty))
        return max(15, min(100, adjusted))

    @staticmethod
    def tenure_quality(fds: list[ProcessedFD]) -> int:
        if not fds:
            return 20
        weighted = sum((max(1, fd.remaining_months) * fd.collateral_value) for fd in fds)
        total = sum(fd.collateral_value for fd in fds)
        avg_remaining = weighted / max(total, 1)
        if avg_remaining >= 24:
            return 90
        if avg_remaining >= 12:
            return 75
        if avg_remaining >= 6:
            return 60
        return 45

    @staticmethod
    def ltv_from_score(score: int) -> float:
        if score >= 85:
            return 0.82
        if score >= 75:
            return 0.75
        if score >= 60:
            return 0.66
        return 0.55

    @staticmethod
    def rate_band(score: int) -> str:
        if score >= 85:
            return "10.5% - 12.0%"
        if score >= 75:
            return "12.0% - 14.5%"
        if score >= 60:
            return "14.5% - 17.0%"
        return "17.0% - 20.0%"

    @staticmethod
    def decision(score: int, eligible_max: float) -> str:
        if score >= 75 and eligible_max >= 100000:
            return "pre_qualified"
        if score >= 60:
            return "conditionally_ready"
        return "improve_then_apply"

    @staticmethod
    def path(score: int) -> str:
        if score >= 75:
            return "Route to secured FD-backed loan at FD-holding bank first."
        if score >= 60:
            return "Try own-bank secured option, keep unsecured backup for urgency."
        return "Improve monthly surplus and add FD buffer before applying."

    @staticmethod
    def explanation(score: int, collateral: int, cashflow: int) -> str:
        if score >= 75:
            return (
                f"Strong readiness driven by collateral score {collateral}/100 and stable cashflow "
                f"{cashflow}/100. Start with your FD-holding bank for lower-cost approval."
            )
        if score >= 60:
            return (
                f"Moderate readiness. Collateral is usable, but cashflow score {cashflow}/100 is limiting "
                "better pricing. Improving surplus for 2-3 months can lift the band."
            )
        return (
            f"Current readiness is constrained by low collateral/cashflow balance ({collateral}/{cashflow}). "
            "Increase FD cushion and reduce EMI bounces to improve approval confidence."
        )

    @staticmethod
    def route_options() -> list[RouteOption]:
        return [
            RouteOption(
                route="Own FD Bank (Secured)",
                rationale="Lien marking is straightforward when FD and loan are in the same bank.",
                expected_speed="Fast",
                expected_cost="Lower",
            ),
            RouteOption(
                route="External Lender (Unsecured fallback)",
                rationale="Useful when speed is critical but pricing is usually higher.",
                expected_speed="Medium",
                expected_cost="Higher",
            ),
        ]
