from __future__ import annotations

from dataclasses import dataclass
from datetime import date

APPORTEUR_AFFAIRE_ID = "001AZ000005fkfVYAQ"


@dataclass(frozen=True)
class FiscalPeriod:
    start: date
    end: date

    @property
    def label(self) -> str:
        return f"{self.start.year}-{self.end.year}"


def current_fiscal_period(today: date | None = None) -> FiscalPeriod:
    today = today or date.today()
    start_year = today.year if today.month >= 8 else today.year - 1
    return FiscalPeriod(date(start_year, 8, 1), date(start_year + 1, 7, 31))


def previous_fiscal_period(period: FiscalPeriod) -> FiscalPeriod:
    return FiscalPeriod(date(period.start.year - 1, 8, 1), date(period.start.year, 7, 31))


def ca_facture(period: FiscalPeriod) -> str:
    return f"""
SELECT CALENDAR_YEAR(Date_souhaitee_facturation__c) annee,
       CALENDAR_MONTH(Date_souhaitee_facturation__c) mois,
       SUM(Previsionnel_commision__c) total
FROM Facturation__c
WHERE Opportunite__r.ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND Opportunite__r.TypeDeal__c = 'Courtage'
  AND Opportunite__r.StageName LIKE 'Gagn%'
  AND Regularisation__c = false
  AND Opportunite__r.Date_de_signature__c > 2025-07-31
  AND Date_souhaitee_facturation__c >= {period.start.isoformat()}
  AND Date_souhaitee_facturation__c <= {period.end.isoformat()}
GROUP BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
ORDER BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
""".strip()


def ca_signe(period: FiscalPeriod) -> str:
    return f"""
SELECT CALENDAR_YEAR(Date_de_signature__c) annee,
       CALENDAR_MONTH(Date_de_signature__c) mois,
       SUM(Amount) total
FROM Opportunity
WHERE ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND TypeDeal__c = 'Courtage'
  AND StageName LIKE 'Gagn%'
  AND Date_de_signature__c >= {period.start.isoformat()}
  AND Date_de_signature__c <= {period.end.isoformat()}
GROUP BY CALENDAR_YEAR(Date_de_signature__c),
         CALENDAR_MONTH(Date_de_signature__c)
ORDER BY CALENDAR_YEAR(Date_de_signature__c),
         CALENDAR_MONTH(Date_de_signature__c)
""".strip()


def ca_facture_upfront(period: FiscalPeriod) -> str:
    return f"""
SELECT CALENDAR_YEAR(Date_souhaitee_facturation__c) annee,
       CALENDAR_MONTH(Date_souhaitee_facturation__c) mois,
       SUM(Previsionnel_commision__c) total
FROM Facturation__c
WHERE Opportunite__r.ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND Opportunite__r.TypeDeal__c = 'Courtage'
  AND Opportunite__r.StageName LIKE 'Gagn%'
  AND Regularisation__c = false
  AND Opportunite__r.Date_de_signature__c >= {period.start.isoformat()}
  AND Opportunite__r.Date_de_signature__c <= {period.end.isoformat()}
  AND Date_souhaitee_facturation__c >= {period.start.isoformat()}
  AND Date_souhaitee_facturation__c <= {period.end.isoformat()}
GROUP BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
ORDER BY CALENDAR_YEAR(Date_souhaitee_facturation__c),
         CALENDAR_MONTH(Date_souhaitee_facturation__c)
""".strip()


def opportunites_gagnees(period: FiscalPeriod) -> str:
    return f"""
SELECT CALENDAR_YEAR(CloseDate) annee,
       CALENDAR_MONTH(CloseDate) mois,
       COUNT(Id) nb_opportunites,
       SUM(NombreCompteur__c) nb_compteurs,
       SUM(ConsommationTotale__c) volume
FROM Opportunity
WHERE ApporteurAffaire__c = '{APPORTEUR_AFFAIRE_ID}'
  AND IsWon = true
  AND Probability > 0
  AND CloseDate >= {period.start.isoformat()}
  AND CloseDate <= {period.end.isoformat()}
GROUP BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
ORDER BY CALENDAR_YEAR(CloseDate),
         CALENDAR_MONTH(CloseDate)
""".strip()


def resultat_vente_interne_queries(period: FiscalPeriod) -> dict[str, str]:
    return {
        "ca_facture": ca_facture(period),
        "ca_signe": ca_signe(period),
        "ca_facture_upfront": ca_facture_upfront(period),
        "opportunites_gagnees": opportunites_gagnees(period),
    }
