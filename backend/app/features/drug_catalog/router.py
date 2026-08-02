from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.features.drug_catalog.service import lookup_catalog


router = APIRouter(prefix="/api", tags=["drug-catalog"])


@router.get("/drugs")
def get_drugs(q: str | None = Query(default=None, description="Optional search term")) -> dict[str, list[dict[str, Any]]]:
	return {"data": lookup_catalog(q)}
