from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.features.prescriptions.schemas import PrescriptionCreateRequest
from app.features.prescriptions.service import build_prescription_response


router = APIRouter(prefix="/api", tags=["prescriptions"])


@router.post("/prescriptions")
def create_prescription(payload: PrescriptionCreateRequest) -> dict[str, Any]:
	return build_prescription_response(payload)
