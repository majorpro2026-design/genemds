from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine


class PatientCreateRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	full_name: str = Field(..., alias="fullName", min_length=1)
	dob: date
	sex: str = Field(..., min_length=1)


def create_patient(payload: PatientCreateRequest) -> dict[str, Any]:
	sql = text(
		"""
		INSERT INTO core.patient (full_name, dob, sex)
		VALUES (:full_name, :dob, :sex)
		RETURNING patient_id, full_name, dob, sex, created_at
		"""
	)

	try:
		with engine.begin() as connection:
			row = connection.execute(
				sql,
				{"full_name": payload.full_name.strip(), "dob": payload.dob, "sex": payload.sex.strip()},
			).mappings().one()
	except SQLAlchemyError as exc:
		raise RuntimeError(f"Failed to create patient: {exc}") from exc

	return {
		"patientId": row["patient_id"],
		"fullName": row["full_name"],
		"dob": row["dob"].isoformat(),
		"sex": row["sex"],
		"createdAt": row["created_at"].isoformat(),
	}