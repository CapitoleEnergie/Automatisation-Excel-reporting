from __future__ import annotations

import json
from pathlib import Path

MONTH = {8:"B",9:"C",10:"D",11:"E",12:"F",1:"G",2:"H",3:"I",4:"J",5:"K",6:"L",7:"M"}
KMONTH = {8:"C",9:"D",10:"E",11:"F",12:"G",1:"H",2:"I",3:"J",4:"K",5:"L",6:"M",7:"N"}
SALES = {"Victor Bez":4,"Julian Fraudeau":5,"Omar Saussi":6,"Robin Bonnet":7,"Paul Joffrin":8}

def set_value(plan, sheet, cell, value, metric):
    plan[(sheet, cell)] = {"sheet":sheet,"cell":cell,"value":value,"metric":metric}

def monthly_map(rows, value_key):
    return {r["mois"]: (r.get(value_key) or 0) for r in rows if r.get("mois") in MONTH}

def seed_months(plan, sheet, row, metric, columns=MONTH):
    for month, col in columns.items():
        set_value(plan, sheet, f"{col}{row}", 0, metric)

def build(payload):
    periods=payload.get("periods") or []
    if len(periods)!=1:
        raise ValueError("Utiliser --period current pour le dry-run Excel.")
    p=periods[0]
    s=p["sections"]
    plan={}

    # RESULTAT VENTE INTERNE : toutes les cellules mensuelles autorisées sont écrites.
    r=s["RESULTAT VENTE INTERNE"]
    for metric,row in {"ca_facture":3,"ca_signe":13,"ca_facture_upfront":23}.items():
        seed_months(plan,"RESULTAT VENTE INTERNE",row,metric)
        for month,value in monthly_map(r[metric]["rows"],"total").items():
            set_value(plan,"RESULTAT VENTE INTERNE",f"{MONTH[month]}{row}",value,metric)
    for key,row in [("nb_opportunites",33),("nb_compteurs",43),("volume",53)]:
        seed_months(plan,"RESULTAT VENTE INTERNE",row,key)
        for x in r["opportunites_gagnees"]["rows"]:
            if x.get("mois") in MONTH:
                set_value(plan,"RESULTAT VENTE INTERNE",f"{MONTH[x['mois']]}{row}",x.get(key) or 0,key)

    # GESTION APPELS D'OFFRES
    g=s["GESTION APPELS D'OFFRES"]
    for metric,row in {"nombre_ao":3,"ca_price":21,"ca_signe_all_deals":23}.items():
        seed_months(plan,"GESTION APPELS D'OFFRES",row,metric)
        for month,value in monthly_map(g[metric]["rows"],"total").items():
            set_value(plan,"GESTION APPELS D'OFFRES",f"{MONTH[month]}{row}",value,metric)

    # KPI PAR SALES
    for name,m in s["KPI PAR SALES"].items():
        base=SALES[name]
        for metric,row in {"ca_facture":base,"ca_signe_reel":base+8}.items():
            seed_months(plan,"KPI PAR SALES",row,f"{name}:{metric}",KMONTH)
            for month,value in monthly_map(m[metric]["rows"],"total").items():
                set_value(plan,"KPI PAR SALES",f"{KMONTH[month]}{row}",value,f"{name}:{metric}")
        for key,row in [("nb_opportunites",base+16),("nb_compteurs",base+24),("duree_moyenne",base+40),("volume",base+48)]:
            seed_months(plan,"KPI PAR SALES",row,f"{name}:{key}",KMONTH)
            for x in m["opportunites_compteurs_volume_duree"]["rows"]:
                if x.get("mois") in KMONTH:
                    set_value(plan,"KPI PAR SALES",f"{KMONTH[x['mois']]}{row}",x.get(key) or 0,f"{name}:{key}")
        for metric,offset in [("nombre_ao",56),("ca_price",64)]:
            row=base+offset
            seed_months(plan,"KPI PAR SALES",row,f"{name}:{metric}",KMONTH)
            for month,value in monthly_map(m[metric]["rows"],"total").items():
                set_value(plan,"KPI PAR SALES",f"{KMONTH[month]}{row}",value,f"{name}:{metric}")

    # ANALYSE CA SIGNE
    a=s["ANALYSE CA SIGNE"]
    rows_type={"Conquête":5,"Renouvellement":13,"Vente additionnelle":21}
    for category,row in rows_type.items():
        seed_months(plan,"ANALYSE CA SIGNE",row,f"type:{category}")
    for x in a["par_type"]["rows"]:
        category=x.get("categorie")
        if category in rows_type and x.get("mois") in MONTH:
            set_value(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{rows_type[category]}",x.get("ca_signe") or 0,f"type:{category}")

    for source,row in {"Marketing":36,"Non-Marketing":44}.items():
        seed_months(plan,"ANALYSE CA SIGNE",row,f"source:{source}")
    for x in a["par_source"]["rows"]:
        source=x.get("source")
        row={"Marketing":36,"Non-Marketing":44}.get(source)
        if row and x.get("mois") in MONTH:
            set_value(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{row}",x.get("ca_signe") or 0,f"source:{source}")

    for energie,row in {"Electricité":53,"Gaz":61}.items():
        seed_months(plan,"ANALYSE CA SIGNE",row,f"energie:{energie}")
    for x in a["par_energie"]["rows"]:
        key="Electricité" if x.get("energie") in ("Electricité","Electricite") else x.get("energie")
        row={"Electricité":53,"Gaz":61}.get(key)
        if row and x.get("mois") in MONTH:
            set_value(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{row}",x.get("ca_signe") or 0,f"energie:{key}")

    writes=list(plan.values())
    return {"mode":"DRY_RUN_ONLY","fiscal_year":p["fiscal_year"],"write_count":len(writes),"writes":writes,
            "safety":{"formulas_written":False,"sharepoint_written":False,"only_whitelisted_cells":True,
                      "missing_salesforce_values_cleared_to_zero":True}}

def main():
    payload=json.loads(Path("results.json").read_text(encoding="utf-8"))
    plan=build(payload)
    Path("excel-write-plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Dry-run Excel: {plan['write_count']} cellules autorisées.")

if __name__=="__main__":
    main()
