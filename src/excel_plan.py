from __future__ import annotations

import json
from pathlib import Path

MONTH = {8:"B",9:"C",10:"D",11:"E",12:"F",1:"G",2:"H",3:"I",4:"J",5:"K",6:"L",7:"M"}
KMONTH = {8:"C",9:"D",10:"E",11:"F",12:"G",1:"H",2:"I",3:"J",4:"K",5:"L",6:"M",7:"N"}
SALES = {"Victor Bez":4,"Julian Fraudeau":5,"Omar Saussi":6,"Robin Bonnet":7,"Paul Joffrin":8}

def add(plan, sheet, cell, value, metric):
    plan.append({"sheet":sheet,"cell":cell,"value":value,"metric":metric})

def monthly(rows):
    return [r for r in rows if r.get("mois") in MONTH]

def build(payload):
    periods=payload.get("periods") or []
    if len(periods)!=1:
        raise ValueError("Utiliser --period current pour le dry-run Excel.")
    p=periods[0]
    s=p["sections"]
    plan=[]

    r=s["RESULTAT VENTE INTERNE"]
    for metric,row in {"ca_facture":3,"ca_signe":13,"ca_facture_upfront":23}.items():
        for x in monthly(r[metric]["rows"]):
            add(plan,"RESULTAT VENTE INTERNE",f"{MONTH[x['mois']]}{row}",x["total"],metric)
    for x in monthly(r["opportunites_gagnees"]["rows"]):
        c=MONTH[x["mois"]]
        add(plan,"RESULTAT VENTE INTERNE",f"{c}33",x["nb_opportunites"],"nb_opportunites")
        add(plan,"RESULTAT VENTE INTERNE",f"{c}43",x["nb_compteurs"],"nb_compteurs")
        add(plan,"RESULTAT VENTE INTERNE",f"{c}53",x["volume"],"volume")

    g=s["GESTION APPELS D'OFFRES"]
    for metric,row in {"nombre_ao":3,"ca_price":21,"ca_signe_all_deals":23}.items():
        for x in monthly(g[metric]["rows"]):
            add(plan,"GESTION APPELS D'OFFRES",f"{MONTH[x['mois']]}{row}",x["total"],metric)

    for name,m in s["KPI PAR SALES"].items():
        base=SALES[name]
        for metric,row in {"ca_facture":base,"ca_signe_reel":base+8}.items():
            for x in monthly(m[metric]["rows"]):
                add(plan,"KPI PAR SALES",f"{KMONTH[x['mois']]}{row}",x["total"],f"{name}:{metric}")
        for x in monthly(m["opportunites_compteurs_volume_duree"]["rows"]):
            c=KMONTH[x["mois"]]
            for key,row in [("nb_opportunites",base+16),("nb_compteurs",base+24),("duree_moyenne",base+40),("volume",base+48)]:
                add(plan,"KPI PAR SALES",f"{c}{row}",x[key],f"{name}:{key}")
        for metric,offset in [("nombre_ao",56),("ca_price",64)]:
            for x in monthly(m[metric]["rows"]):
                add(plan,"KPI PAR SALES",f"{KMONTH[x['mois']]}{base+offset}",x["total"],f"{name}:{metric}")

    a=s["ANALYSE CA SIGNE"]
    rows_type={"Conquête":5,"Renouvellement":13,"Vente additionnelle":21}
    for x in a["par_type"]["rows"]:
        if x.get("categorie") in rows_type and x.get("mois") in MONTH:
            add(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{rows_type[x['categorie']]}",x["ca_signe"],f"type:{x['categorie']}")
    for x in a["par_source"]["rows"]:
        row={"Marketing":36,"Non-Marketing":44}.get(x.get("source"))
        if row and x.get("mois") in MONTH:
            add(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{row}",x["ca_signe"],f"source:{x['source']}")
    for x in a["par_energie"]["rows"]:
        key="Electricité" if x.get("energie") in ("Electricité","Electricite") else x.get("energie")
        row={"Electricité":53,"Gaz":61}.get(key)
        if row and x.get("mois") in MONTH:
            add(plan,"ANALYSE CA SIGNE",f"{MONTH[x['mois']]}{row}",x["ca_signe"],f"energie:{key}")

    cells={(x["sheet"],x["cell"]) for x in plan}
    if len(cells)!=len(plan):
        raise ValueError("Cellule cible dupliquée dans le plan.")
    return {"mode":"DRY_RUN_ONLY","fiscal_year":p["fiscal_year"],"write_count":len(plan),"writes":plan,
            "safety":{"formulas_written":False,"sharepoint_written":False,"only_whitelisted_cells":True}}

def main():
    payload=json.loads(Path("results.json").read_text(encoding="utf-8"))
    plan=build(payload)
    Path("excel-write-plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Dry-run Excel: {plan['write_count']} cellules autorisées.")

if __name__=="__main__":
    main()
