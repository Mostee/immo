import streamlit as st
import pandas as pd

# ====== PARAMÈTRES ======
st.title("Simulateur d'investissement immobilier")

epargne_mensuelle = st.number_input("Épargne mensuelle (€)", value=2500)
prix_bien = st.number_input("Prix d'un bien (€)", value=100000)
apport = st.number_input("Apport (€)", value=10000)
loyer_mensuel = st.number_input("Loyer mensuel (€)", value=700)
duree_pret = st.number_input("Durée du prêt (années)", value=7)
taux_annuel = st.number_input("Taux annuel (%)", value=3.0)/100
duree_totale_annees = st.number_input("Durée totale (années)", value=12)

# ====== FONCTION MENSUALITÉ ======
def mensualite(capital, taux_annuel, duree_annees):
    n = duree_annees * 12
    taux_mensuel = taux_annuel / 12
    return capital * taux_mensuel / (1 - (1 + taux_mensuel) ** -n)

mensualite_pret = mensualite(prix_bien - apport, taux_annuel, duree_pret)

# ====== SIMULATION ======
total_mois = duree_totale_annees * 12
cash_epargne = 0
credits = []
tableau = []

for mois in range(1, total_mois+1):
    annee = (mois - 1) // 12 + 1
    mois_annee = (mois - 1) % 12 + 1

    cash_epargne += epargne_mensuelle

    loyers = sum([b['loyer'] for b in credits])
    mensualites = 0
    for b in credits:
        if b['reste_capital'] > 0:
            mensualites += b['mensualite']
            interets = b['reste_capital'] * (taux_annuel / 12)
            capital_remb = b['mensualite'] - interets
            b['reste_capital'] -= capital_remb
            if b['reste_capital'] < 0:
                b['reste_capital'] = 0

    cash_flow = loyers - mensualites + epargne_mensuelle
    cash_epargne += (loyers - mensualites)

    commentaires = []
    while cash_epargne >= apport:
        credits.append({
            'mois_achat': mois,
            'loyer': loyer_mensuel,
            'mensualite': mensualite_pret,
            'reste_capital': prix_bien - apport
        })
        cash_epargne -= apport
        mensualites += mensualite_pret
        loyers += loyer_mensuel
        commentaires.append(f"Achat bien #{len(credits)}")

    capital_restants = {f"Prêt {i+1}": round(b['reste_capital']) for i, b in enumerate(credits)}
    dette_totale = round(sum([b['reste_capital'] for b in credits]))
    valeur_patrimoine = round(len(credits) * prix_bien)

    ligne = {
        "Année": annee,
        "Mois": mois_annee,
        "Nb biens": len(credits),
        "Loyers": round(loyers),
        "Mensualités": round(mensualites),
        "Cash flow": round(cash_flow),
        "Trésorerie": round(cash_epargne),
        "Dette totale": dette_totale,
        "Valeur patrimoine": valeur_patrimoine,
        "Commentaires": "; ".join(commentaires)
    }
    ligne.update(capital_restants)
    tableau.append(ligne)

df = pd.DataFrame(tableau)

# ====== AFFICHAGE ======
st.subheader("Simulation mois par mois")
st.dataframe(df)

# ====== REGROUPEMENT PAR ANNÉE ======
df_annee = df.groupby("Année")[["Cash flow", "Trésorerie", "Dette totale", "Valeur patrimoine"]].sum()
st.subheader("Graphique annuel du cash flow, trésorerie, dette et patrimoine")
st.line_chart(df_annee)
