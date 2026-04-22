from dataclasses import dataclass
import httpx
from app.config import Settings
from app.schemas import FDInput


@dataclass
class RateResolution:
    annual_rate: float
    source: str


class BlostemRatesClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def resolve_fd_rate(self, fd: FDInput) -> RateResolution:
        if fd.annual_rate is not None:
            return RateResolution(annual_rate=fd.annual_rate, source="user_input")

        if not self.settings.blostem_api_key or not fd.bank_slug:
            fallback = self._fallback_rate(fd)
            return RateResolution(annual_rate=fallback, source="fallback_default")

        payload = {
            "principal": fd.principal,
            "tenureMonths": fd.tenure_months,
            "bankSlug": fd.bank_slug,
            "depositorType": fd.depositor_type.value,
            "isCumulative": True,
        }

        headers = {
            "X-API-Key": self.settings.blostem_api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.post(
                    f"{self.settings.blostem_api_base}/fd-rates/calculate",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                rate_used = data["data"]["rateUsed"]
                return RateResolution(annual_rate=float(rate_used), source="blostem_api")
        except httpx.HTTPError:
            fallback = self._fallback_rate(fd)
            return RateResolution(annual_rate=fallback, source="fallback_default")

    @staticmethod
    def _fallback_rate(fd: FDInput) -> float:
        defaults = {
            "SCB": 7.4,
            "SFB": 8.4,
            "NBFC": 8.8,
            "OTHER": 7.0,
        }
        base = defaults[fd.institution_type.value]
        if fd.depositor_type.value == "senior":
            return min(base + 0.5, 10.0)
        return base
