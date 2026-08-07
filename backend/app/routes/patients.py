from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.patients import PatientCreateRequest, create_patient

router = APIRouter(prefix="/api")


@router.post("/patients")
def create_patient_route(payload: PatientCreateRequest) -> dict[str, Any]:
	try:
		return create_patient(payload)
	except RuntimeError as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc