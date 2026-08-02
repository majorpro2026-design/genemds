from __future__ import annotations

from pydantic import BaseModel, Field


class DrugLookupRequest(BaseModel):
	drug_names: list[str] = Field(..., min_length=1, description="List of brand or generic drug names")
