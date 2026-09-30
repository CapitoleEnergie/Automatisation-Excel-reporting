from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .queries import (
    FiscalPeriod,
    current_fiscal_period,
    previous_fiscal_period,
    resultat_vente_interne_queries,
)
from .queries_extended import (
    analyse_ca_signe_queries,
    gestion_appels_offres_queries,
    kpi_par_sales_queries,
)
from .salesforce import SalesforceClient


def clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if k != "attributes"} for row in records]


def run_queries(
    client: SalesforceClient,
    queries: dict[str, str],
    prefix: str,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for name, soql in queries.items():
        print(f"[READ] {prefix} - {name}")
        metrics[name] = {
            "rows": clean_records(client.query(soql)),
            "soql": soql,
        }
    return metrics


def extract_period(client: SalesforceClient, period: FiscalPeriod) -> dict[str, Any]:
    sales_metrics: dict[str, Any] = {}
    for sales_name, queries in kpi_par_sales_queries(period).items():
        sales_metrics[sales_name] = run_queries(
            client,
            queries,
            f"{period.label} - KPI PAR SALES - {sales_name}",
        )

    return {
        "fiscal_year": period.label,
        "start": period.start.isoformat(),
        "end": period.end.isoformat(),
        "sections": {
            "RESULTAT VENTE INTERNE": run_queries(
                client,
                resultat_vente_interne_queries(period),
                f"{period.label} - RESULTAT VENTE INTERNE",
            ),
            "GESTION APPELS D'OFFRES": run_queries(
                client,
                gestion_appels_offres_queries(period),
                f"{period.label} - GESTION APPELS D'OFFRES",
            ),
            "KPI PAR SALES": sales_metrics,
            "ANALYSE CA SIGNE": run_queries(
                client,
                analyse_ca_signe_queries(period),
                f"{period.label} - ANALYSE CA SIGNE",
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=("current", "previous", "both"), default="both")
    parser.add_argument("--output", default="results.json")
    args = parser.parse_args()

    load_dotenv()

    current = current_fiscal_period(date.today())
    selected = {
        "current": [current],
        "previous": [previous_fiscal_period(current)],
        "both": [previous_fiscal_period(current), current],
    }[args.period]

    print("Authentification Salesforce...")
    client = SalesforceClient.from_client_credentials()
    print("Authentification Salesforce : OK")

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "mode": "READ_ONLY",
        "scope": [
            "RESULTAT VENTE INTERNE",
            "GESTION APPELS D'OFFRES",
            "KPI PAR SALES",
            "ANALYSE CA SIGNE",
        ],
        "periods": [extract_period(client, period) for period in selected],
    }

    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Extraction terminée : {args.output}")


if __name__ == "__main__":
    main()
