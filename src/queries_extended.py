from __future__ import annotations

from datetime import date

from .queries import APPORTEUR_AFFAIRE_ID, FiscalPeriod

GESTIONNAIRE = "CAPITOLE ENERGIE"
EXCLUDED_PRICERS = (
    "Mylène Prost",
    "Benoit Vilcot",
    "Paul Joffrin",
    "Julian Fraudeau",
    "Morgan Marechal",
    "Gael Jouffroy",
    "Victor Bez",
    "Charles Ducos",
)
SALES = ("Victor Bez", "Julian Fraudeau", "Omar Saussi", "Robin Bonnet", "Paul Joffrin")


def _d(value: date) -> str:
    return value.isoformat()


def _period_end_for_ao(period: FiscalPeriod, today: date | None = None) -> date:
    today = today or date.today()
    if period.start <= today <= period.end:
        return today
    return period.end


def _excluded_pricers() -> str:
    return ",".join(f"'{name}'" for name in EXCLUDED_PRICERS)


def ao_count(period: FiscalPeriod, today: date | None = None, sales_name: str | None = None) -> str:
    owner_filter = (
        f"\n  AND Proprietaire_de_l_opportunite__c = '{sales_name}'"
        if sales_name
        else ""
    )
    end = _period_end_for_ao(period, today)
    return f"""
SELECT CALENDAR_YEAR(Date_de_remise_client__c) annee,
       CALENDAR_MONTH(Date_de_remise_client__c) mois,
       COUNT(Id) total
FROM Slot_Pricing__c
WHERE Gestionnaire__c = '{GESTIONNAIRE}'
  AND (Nature_de_la_demande__c = 'Pour Signature'
       OR Nature_de_la_demande__c = 'Indicative'
       OR Nature_de_la_demande__c LIKE 'R_actualisation')
  AND Statut__c LIKE 'R_alis_'
  AND Pricer__r.Name NOT IN ({_excluded_pricers()})
  AND Date_de_remise_client__c >= {_d(period.start)}
  AND Date_de_remise_client__c <= {_d(end)}{owner_filter}
GROUP BY CALENDAR_YEAR(Date_de_remise_client__c),
         CALENDAR_MONTH(Date_de_remise_client__c)
ORDER BY CALENDAR_YEAR(Date_de_remise_client__c),
         CALENDAR_MONTH(Date_de_remise_client__c)
""".strip()


def ao_ca_price(period: FiscalPeriod, today: date | None = None, sales_name: str | None = None) -> str:
    owner_filter = (
        f"\n  AND Proprietaire_de_l_opportunite__c = '{sales_name}'"
        if sales_name
        else ""
    )
    end = _period_end_for_ao(period, today)
    return f"""
SELECT CALENDAR_YEAR(Date_de_remise_client__c) annee,
       CALENDAR_MONTH(Date_de_remise_client__c) mois,
       SUM(Montant__c) total
FROM Slot_Pricing__c
WHERE Gestionnaire__c = '{GESTIONNAIRE}'
  AND (Nature_de_la_demande__c = 'Pour Signature'
       OR Nature_de_la_demande__c = 'Indicative'
       OR Nature_de_la_demande__c LIKE 'R_actualisation')
  AND Statut__c LIKE 'R_alis_'
  AND Pricer__r.Name NOT IN ({_excluded_pricers()})
  AND Date_de_remise_client__c >= {_d(period.start)}
  AND Date_de_remise_client__c <= {_d(end)}{owner_filter}
GROUP BY CALENDAR_YEAR(Date_de_remise_client__c),
         CALENDAR_MONTH(Date_de_remise_client__c)
ORDER BY CALENDAR_YEAR(Date_de_remise_client__c),
         CALENDAR_MONTH(Date_de_remise_client__c)
""".strip()


def ca_signe_all_deals_by_close_date(
    period: FiscalPeriod,
    sales_name: str | None = None,
    real_amount: bool = False,
) -> str:
    amount_field = "Amount"
    owner_filter = f"\n  AND Owner.Name = '{sales_name}'" if sales_name else ""
    return f"""
SELECT CALENDAR_YEAR(CloseDate) annee,
       CALENDAR_MONTH(CloseDate) mois,
       SUM({amount_field}) total
FROM Opportunity
WHERE ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND IsWon = true
  AND Probability > 0
  AND CloseDate >= {_d(period.start)}
  AND CloseDate <= {_d(period.end)}{owner_filter}
GROUP BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
ORDER BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
""".strip()


def opportunity_kpis(period: FiscalPeriod, sales_name: str) -> str:
    return f"""
SELECT CALENDAR_YEAR(CloseDate) annee,
       CALENDAR_MONTH(CloseDate) mois,
       COUNT(Id) nb_opportunites,
       SUM(NombreCompteur__c) nb_compteurs,
       SUM(ConsommationTotale__c) volume,
       AVG(Duree_LO_retenue__c) duree_moyenne
FROM Opportunity
WHERE ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND IsWon = true
  AND Probability > 0
  AND Owner.Name = '{sales_name}'
  AND CloseDate >= {_d(period.start)}
  AND CloseDate <= {_d(period.end)}
GROUP BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
ORDER BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
""".strip()


def ca_facture_sales(period: FiscalPeriod, sales_name: str) -> str:
    return f"""
SELECT CALENDAR_YEAR(Date_souhaitee_facturation__c) annee,
       CALENDAR_MONTH(Date_souhaitee_facturation__c) mois,
       SUM(Previsionnel_commision__c) total
FROM Facturation__c
WHERE Opportunite__r.ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND Opportunite__r.TypeDeal__c = 'Courtage'
  AND Opportunite__r.StageName LIKE 'Gagn%'
  AND Opportunite__r.Owner.Name = '{sales_name}'
  AND Regularisation__c = false
  AND Opportunite__r.Date_de_signature__c > 2025-07-31
  AND Date_souhaitee_facturation__c >= {_d(period.start)}
  AND Date_souhaitee_facturation__c <= {_d(period.end)}
GROUP BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
ORDER BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
""".strip()


def analyse_base_filter(period: FiscalPeriod) -> str:
    return f"""
ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND TypeDeal__c = 'Courtage'
  AND StageName LIKE 'Gagn%'
  AND Date_de_signature__c >= {_d(period.start)}
  AND Date_de_signature__c <= {_d(period.end)}
""".strip()


def analyse_type(period: FiscalPeriod) -> str:
    return f"""
SELECT Type categorie, SUM(Amount) ca_signe, SUM(Amount) ca_reel
FROM Opportunity
WHERE {analyse_base_filter(period)}
GROUP BY Type
ORDER BY Type
""".strip()


def analyse_source(period: FiscalPeriod) -> str:
    return f"""
SELECT Account.AccountSource source, SUM(Amount) ca_signe, SUM(Amount) ca_reel
FROM Opportunity
WHERE {analyse_base_filter(period)}
GROUP BY Account.AccountSource
ORDER BY Account.AccountSource
""".strip()


def analyse_energie(period: FiscalPeriod) -> str:
    return f"""
SELECT Energie__c energie, SUM(Amount) ca_signe, SUM(Amount) ca_reel
FROM Opportunity
WHERE {analyse_base_filter(period)}
GROUP BY Energie__c
ORDER BY Energie__c
""".strip()


def analyse_ecart(period: FiscalPeriod) -> str:
    return f"""
SELECT SUM(Amount) ca_reel, SUM(Amount) ca_estime
FROM Opportunity
WHERE {analyse_base_filter(period)}
""".strip()


def analyse_annee_debut_contrat(period: FiscalPeriod) -> str:
    return f"""
SELECT CALENDAR_YEAR(Date_min_de_debut_souhaitee__c) annee_debut,
       SUM(Amount) ca_signe,
       SUM(Amount) ca_reel
FROM Opportunity
WHERE {analyse_base_filter(period)}
GROUP BY CALENDAR_YEAR(Date_min_de_debut_souhaitee__c)
ORDER BY CALENDAR_YEAR(Date_min_de_debut_souhaitee__c)
""".strip()


def analyse_concurrence_total(period: FiscalPeriod) -> str:
    return f"""
SELECT COUNT(Id) total
FROM Opportunity
WHERE {analyse_base_filter(period)}
""".strip()


def analyse_concurrence_oui(period: FiscalPeriod) -> str:
    return f"""
SELECT COUNT(Id) total
FROM Opportunity
WHERE {analyse_base_filter(period)}
  AND Id IN (
      SELECT Opportunite__c
      FROM Slot_Pricing__c
      WHERE Concurrence__c = 'Oui'
  )
""".strip()


def analyse_top10_clients(period: FiscalPeriod) -> str:
    return f"""
SELECT Account.Name compte, SUM(Amount) ca_reel
FROM Opportunity
WHERE {analyse_base_filter(period)}
GROUP BY Account.Name
ORDER BY SUM(Amount) DESC
LIMIT 10
""".strip()


def gestion_appels_offres_queries(period: FiscalPeriod) -> dict[str, str]:
    return {
        "nombre_ao": ao_count(period),
        "ca_price": ao_ca_price(period),
        "ca_signe_all_deals": ca_signe_all_deals_by_close_date(period),
    }


def kpi_par_sales_queries(period: FiscalPeriod) -> dict[str, dict[str, str]]:
    return {
        sales: {
            "ca_facture": ca_facture_sales(period, sales),
            "ca_signe_reel": ca_signe_all_deals_by_close_date(period, sales, real_amount=True),
            "opportunites_compteurs_volume_duree": opportunity_kpis(period, sales),
            "nombre_ao": ao_count(period, sales_name=sales),
            "ca_price": ao_ca_price(period, sales_name=sales),
        }
        for sales in SALES
    }


def analyse_ca_signe_queries(period: FiscalPeriod) -> dict[str, str]:
    return {
        "par_type": analyse_type(period),
        "par_source": analyse_source(period),
        "par_energie": analyse_energie(period),
        "ecart_global": analyse_ecart(period),
        "par_annee_debut_contrat": analyse_annee_debut_contrat(period),
        "concurrence_total": analyse_concurrence_total(period),
        "concurrence_oui": analyse_concurrence_oui(period),
        "top10_clients": analyse_top10_clients(period),
    }
