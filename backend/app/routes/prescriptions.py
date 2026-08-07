from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.drug_lookup import PrescriptionCreateRequest, build_prescription_response


router = APIRouter(prefix="/api")


@router.post("/prescriptions")
def create_prescription(payload: PrescriptionCreateRequest) -> dict[str, Any]:
	try:
		return build_prescription_response(payload)
	except RuntimeError as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc