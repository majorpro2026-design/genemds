from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine


def _clean_strings(values: Iterable[str | None]) -> list[str]:
	cleaned: list[str] = []
	seen: set[str] = set()

	for value in values:
		if value is None:
			continue

		normalized = value.strip()
		if not normalized:
			continue

		key = normalized.casefold()
		if key in seen:
			continue

		seen.add(key)
		cleaned.append(normalized)

	return cleaned


def lookup_drug_genes(drug_names: list[str]) -> list[dict[str, Any]]:
	cleaned_names = _clean_strings(drug_names)
	if not cleaned_names:
		return []

	query = text(
		"""
		WITH input_drugs AS (
			SELECT DISTINCT unnest(CAST(:drug_names AS text[])) AS input_name
		), brand_matches AS (
			SELECT
				i.input_name,
				'brand' AS matched_as,
				dbg.brand_name,
				dbg.generic_name
			FROM input_drugs i
			JOIN knowledge.drug_brand_generic dbg
				ON lower(btrim(dbg.brand_name)) = lower(btrim(i.input_name))
		), generic_matches AS (
			SELECT
				i.input_name,
				'generic' AS matched_as,
				dbg.brand_name,
				dbg.generic_name
			FROM input_drugs i
			JOIN knowledge.drug_brand_generic dbg
				ON lower(btrim(dbg.generic_name)) = lower(btrim(i.input_name))
		), resolved_drugs AS (
			SELECT * FROM brand_matches
			UNION
			SELECT * FROM generic_matches
		)
		SELECT
			input_name,
			matched_as,
			brand_name,
			generic_name,
			COALESCE(
				array_agg(DISTINCT gene_symbol ORDER BY gene_symbol) FILTER (WHERE gene_symbol IS NOT NULL),
				ARRAY[]::text[]
			) AS gene_symbols
		FROM resolved_drugs
		LEFT JOIN knowledge.gene_drug_pair gdp
			ON lower(btrim(gdp.drug_name)) = lower(btrim(resolved_drugs.generic_name))
		GROUP BY input_name, matched_as, brand_name, generic_name
		ORDER BY input_name, matched_as, brand_name, generic_name
		"""
	)

	try:
		with engine.connect() as connection:
			rows = connection.execute(query, {"drug_names": cleaned_names}).mappings().all()
	except SQLAlchemyError:
		return []

	return [
		{
			"input_name": row["input_name"],
			"matched_as": row["matched_as"],
			"brand_name": row["brand_name"],
			"generic_name": row["generic_name"],
			"gene_symbols": row["gene_symbols"] or [],
		}
		for row in rows
	]
