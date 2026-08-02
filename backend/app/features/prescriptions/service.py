from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import engine
from app.features.drug_gene_lookup.service import _clean_strings, lookup_drug_genes
from app.features.prescriptions.schemas import PrescriptionCreateRequest, PrescriptionDrugItem


def _extract_drug_terms(item: PrescriptionDrugItem | dict[str, Any]) -> list[str]:
	if isinstance(item, PrescriptionDrugItem):
		return _clean_strings(
			[
				item.drug_name,
				item.brand_name,
				item.selected_generic,
				item.generic_name,
				*item.generics,
				*item.generic_names,
			]
		)

	return _clean_strings(
		[
			item.get("drugName"),
			item.get("brandName"),
			item.get("selectedGeneric"),
			item.get("genericName"),
			*(item.get("generics") or []),
			*(item.get("genericNames") or []),
		]
	)


def _resolve_terms_from_prescription(payload: PrescriptionCreateRequest) -> list[str]:
	return _clean_strings(
		term
		for drug in payload.prescribed_drugs
		for term in _extract_drug_terms(drug)
	)


def _attach_gene_matches(
	prescribed_drug: PrescriptionDrugItem,
	lookup_rows: list[dict[str, Any]],
) -> dict[str, Any]:
	terms = _extract_drug_terms(prescribed_drug)
	matches = [row for row in lookup_rows if row["input_name"] in terms]

	gene_symbols: list[str] = []
	for match in matches:
		for symbol in match["gene_symbols"]:
			if symbol not in gene_symbols:
				gene_symbols.append(symbol)

	return {
		**prescribed_drug.model_dump(by_alias=True),
		"lookupTerms": terms,
		"matchedDrugs": matches,
		"geneSymbols": gene_symbols,
	}


def _collect_gene_symbols(resolved_drugs: list[dict[str, Any]]) -> list[str]:
	gene_symbols: list[str] = []
	for drug in resolved_drugs:
		for symbol in drug.get("geneSymbols", []):
			if symbol not in gene_symbols:
				gene_symbols.append(symbol)
	return gene_symbols


def lookup_gene_test_recommendations(gene_symbols: list[str]) -> list[dict[str, Any]]:
	cleaned_symbols = _clean_strings(gene_symbols)
	if not cleaned_symbols:
		return []

	query = text(
		"""
		WITH ranked_pairs AS (
			SELECT DISTINCT ON (lower(btrim(gene_symbol)))
				gene_symbol,
				drug_name,
				guideline_name,
				guideline_url,
				cpic_level,
				clinpgx_level,
				provisional
			FROM knowledge.gene_drug_pair
			WHERE gene_symbol = ANY(CAST(:gene_symbols AS text[]))
			ORDER BY
				lower(btrim(gene_symbol)),
				CASE
					WHEN guideline_name IS NOT NULL AND btrim(guideline_name) <> '' THEN 0
					ELSE 1
				END,
				lower(btrim(COALESCE(guideline_name, drug_name)))
		)
		SELECT
			gene_symbol,
			drug_name,
			guideline_name,
			guideline_url,
			cpic_level,
			clinpgx_level,
			provisional
		FROM ranked_pairs
		ORDER BY lower(btrim(gene_symbol))
		"""
	)

	try:
		with engine.connect() as connection:
			rows = connection.execute(query, {"gene_symbols": cleaned_symbols}).mappings().all()
	except SQLAlchemyError:
		return []

	recommendations: list[dict[str, Any]] = []
	for row in rows:
		gene_symbol = (row["gene_symbol"] or "").strip()
		guideline_name = (row["guideline_name"] or "").strip()
		drug_name = (row["drug_name"] or "").strip()

		title = guideline_name or (f"{gene_symbol} testing" if gene_symbol else "Gene testing")
		details = drug_name or gene_symbol or "Selected gene"
		description = f"Recommended gene test for {details}."

		recommendations.append(
			{
				"title": title,
				"description": description,
				"geneSymbol": gene_symbol,
				"drugName": drug_name,
				"guidelineName": guideline_name or None,
				"guidelineUrl": row["guideline_url"],
				"cpicLevel": row["cpic_level"],
				"clinpgxLevel": row["clinpgx_level"],
				"provisional": bool(row["provisional"]),
			}
		)

	return recommendations


def build_prescription_response(payload: PrescriptionCreateRequest) -> dict[str, Any]:
	search_terms = _resolve_terms_from_prescription(payload)
	lookup_rows = lookup_drug_genes(search_terms)
	resolved_drugs = [
		_attach_gene_matches(drug, lookup_rows)
		for drug in payload.prescribed_drugs
	]
	gene_symbols = _collect_gene_symbols(resolved_drugs)
	suggested_tests = lookup_gene_test_recommendations(gene_symbols)

	return {
		"id": payload.prescription_id,
		"status": "saved",
		"message": "Prescription payload accepted",
		"prescriptionId": payload.prescription_id,
		"prescribedAt": payload.prescribed_at.isoformat(),
		"geneSymbols": gene_symbols,
		"suggestedTests": suggested_tests,
		"resolvedDrugs": resolved_drugs,
	}
