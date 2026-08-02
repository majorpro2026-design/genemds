from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.features.drug_gene_lookup.schemas import DrugLookupRequest
from app.features.drug_gene_lookup.service import lookup_drug_genes


router = APIRouter(prefix="/api", tags=["drug-gene-lookup"])


@router.post("/drug-gene-lookup")
def drug_gene_lookup(payload: DrugLookupRequest) -> dict[str, list[dict[str, Any]]]:
	return {"results": lookup_drug_genes(payload.drug_names)}
