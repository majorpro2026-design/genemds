from __future__ import annotations

from functools import lru_cache
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


logger = logging.getLogger(__name__)
DEBUG_LOG = Path(__file__).resolve().parents[4] / ".run" / "drug-catalog-debug.log"


def _write_debug(message: str) -> None:
	DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
	with DEBUG_LOG.open("a", encoding="utf-8") as handle:
		handle.write(f"{message}\n")


def lookup_catalog(query: str | None = None) -> list[dict[str, Any]]:
	search = (query or "").strip().casefold()
	catalog = list(_load_catalog())
	_write_debug(f"catalog_size={len(catalog)} search={search!r}")
	if not search:
		return catalog

	matches: list[tuple[int, str, str, dict[str, Any]]] = []
	for row in catalog:
		names = [
			str(row["drugName"]),
			str(row["brandName"]),
			str(row["genericName"]),
			*(str(value) for value in row["generics"]),
		]
		lowered = [value.casefold() for value in names if value]
		if not any(search in value for value in lowered):
			continue

		rank = 0 if any(value.startswith(search) for value in lowered) else 1
		matches.append((rank, str(row["drugName"]).casefold(), str(row["genericName"]).casefold(), row))

	matches.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
	return [row for _, _, _, row in matches]


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[dict[str, Any], ...]:
	sql = text(
		"""
		WITH catalog AS (
			SELECT DISTINCT
				md5(lower(btrim(dbg.brand_name)) || '|' || lower(btrim(dbg.generic_name))) AS drug_id,
				dbg.brand_name AS drug_name,
				dbg.brand_name AS brand_name,
				dbg.generic_name AS generic_name,
				ARRAY[dbg.generic_name]::text[] AS generics,
				CAST(NULL AS text) AS strength,
				'knowledge.drug_brand_generic' AS source_name
			FROM knowledge.drug_brand_generic dbg
			WHERE dbg.brand_name IS NOT NULL
				AND dbg.generic_name IS NOT NULL
		)
		SELECT
			drug_id,
			drug_name,
			brand_name,
			generic_name,
			generics,
			strength,
			source_name
		FROM catalog
		ORDER BY lower(drug_name), lower(generic_name)
		"""
	)

	try:
		with engine.connect() as connection:
			rows = connection.execute(sql).mappings().all()
			_write_debug(f"loaded_rows={len(rows)}")
	except SQLAlchemyError as exc:
		logger.exception("Failed to load drug catalog from knowledge.drug_brand_generic")
		_write_debug(f"sqlalchemy_error={exc!r}")
		return tuple()

	return tuple(
		{
			"drugId": row["drug_id"],
			"drugName": row["drug_name"],
			"brandName": row["brand_name"],
			"genericName": row["generic_name"],
			"generics": row["generics"] or [],
			"strength": row["strength"],
			"sourceName": row["source_name"],
		}
		for row in rows
	)
