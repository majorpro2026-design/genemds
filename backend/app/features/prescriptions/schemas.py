from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionDrugItem(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	drug_id: str | int | None = Field(default=None, alias="drugId")
	drug_name: str | None = Field(default=None, alias="drugName")
	brand_name: str | None = Field(default=None, alias="brandName")
	strength: str | None = None
	generics: list[str] = Field(default_factory=list)
	generic_name: str | None = Field(default=None, alias="genericName")
	generic_names: list[str] = Field(default_factory=list, alias="genericNames")
	selected_generic: str | None = Field(default=None, alias="selectedGeneric")
	dosage: str | None = None
	frequency: str | None = None
	duration_days: int | None = Field(default=None, alias="durationDays", ge=0)
	note: str | None = None


class PrescriptionCreateRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	prescription_id: str = Field(..., alias="prescriptionId")
	prescribed_at: datetime = Field(..., alias="prescribedAt")
	prescribed_drugs: list[PrescriptionDrugItem] = Field(..., min_length=1, alias="prescribedDrugs")
