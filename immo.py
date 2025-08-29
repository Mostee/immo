import streamlit as st
import pandas as pd

# ====== PARAMÈTRES ======
st.title("Simulateur d'investissement immobilier avancé")

# Entrées utilisateur
epargne_mensuelle = st.number_input("Épargne mensuelle (€)", value=2500)
prix_bien_initial = st.number_input("Prix initial d'un bien (€)", value=100000)
apport = st.number_input("Apport (€)", value=10000)
loyer_initial = st.number_input("Loyer mensuel initial (€)", value=800)
duree_pret = st.number_input("Durée du prêt (années)", value=7)
taux_annuel = st.number_input("Taux annuel (%)", value=3.0)/100
duree_totale_annees = st.number_input("Durée totale (années)", value=12)

# Paramètres avancés
vacance = st.number_input("Vacance locative (%)", value=4.0)/100
charges_pct = st.number_input("Charges locatives non récupérables (%)", value=20.0)/100
taxe_fonciere = st.number_input("Taxe foncière par bien (€/mois)", value=100)
appreciation = st.number_input("Appréciation annuelle du bien (%)", value=1.5)/100
revalo_loyer = st.number_input("Revalorisation annuelle des loyers (%)", value=2.0)/100
taux_impot = 0


def format_nombre(valeur):
    """Formate les grands nombres en k€ ou M€"""
    if valeur >= 1_000_000:
        return f"{valeur/1_000_000:.1f} M€"
    elif valeur >= 1_000:
        return f"{valeur/1000:.0f} k€"
    else:
        return f"{valeur} €"

# ====== FONCTION MENSUALITÉ ======
def mensualite(capital, taux_annuel, duree_annees):
    n = duree_annees * 12
    taux_mensuel = taux_annuel / 12
    return capital * taux_mensuel / (1 - (1 + taux_mensuel) ** -n)


# ====== SIMULATION ======
total_mois = duree_totale_annees * 12
cash_epargne = 0
credits = []

prix_bien = prix_bien_initial
loyer_mensuel = loyer_initial

# Liste pour le tableau
tableau = []

for mois in range(1, total_mois+1):
    annee = (mois - 1) // 12 + 1
    mois_annee = (mois - 1) % 12 + 1

    # Ajouter épargne
    cash_epargne += epargne_mensuelle

    # Mise à jour loyers et mensualités
    loyers_bruts = sum([b['loyer'] for b in credits])
    loyers_net = loyers_bruts * (1 - vacance - charges_pct) - (len(credits) * taxe_fonciere)

    mensualites = 0
    interets_totaux = 0
    amortissements_totaux = 0
    for b in credits:
        if b['reste_capital'] > 0:
            mensualites += b['mensualite']
            interets = b['reste_capital'] * (taux_annuel / 12)
            capital_remb = b['mensualite'] - interets
            b['reste_capital'] -= capital_remb
            if b['reste_capital'] < 0:
                b['reste_capital'] = 0
            interets_totaux += interets
            amortissements_totaux += capital_remb

    # Cash flow net après impôt
    benefice_avant_impot = loyers_net - mensualites
    impot = max(0, benefice_avant_impot) * taux_impot
    cash_flow = benefice_avant_impot - impot + epargne_mensuelle
    cash_epargne += (loyers_net - mensualites - impot)

    # Achat dynamique
    commentaires = []
    if cash_epargne >= apport:
        mensualite_pret = mensualite(prix_bien - apport, taux_annuel, duree_pret)
        credits.append({
            'mois_achat': mois,
            'loyer': loyer_mensuel,
            'mensualite': mensualite_pret,
            'reste_capital': prix_bien - apport
        })
        cash_epargne -= apport
        commentaires.append(f"Achat bien #{len(credits)} au prix de {round(prix_bien)}€")

    # Revalorisation annuelle (au 1er mois de chaque année sauf la première)
    if mois_annee == 1 and mois > 1:
        prix_bien *= (1 + appreciation)
        loyer_mensuel *= (1 + revalo_loyer)

    # Capital restant pour chaque prêt
    capital_restants = {f"Prêt {i+1}": round(b['reste_capital']) for i, b in enumerate(credits)}

    # Dette totale et valeur du patrimoine
    dette_totale = round(sum([b['reste_capital'] for b in credits]))
    valeur_patrimoine = round(len(credits) * prix_bien)
    patrimoine_net = valeur_patrimoine - dette_totale

    # Ligne du tableau
    ligne = {
        "Année": annee,
        "Mois": mois_annee,
        "Nb biens": len(credits),
        "Loyers bruts": round(loyers_bruts),
        "Loyers nets": round(loyers_net),
        "Mensualités": round(mensualites),
        "Intérêts": round(interets_totaux),
        "Amortissement": round(amortissements_totaux),
        "Cash flow": round(cash_flow),
        "Trésorerie": round(cash_epargne),
        "Dette totale": dette_totale,
        "Valeur patrimoine": valeur_patrimoine,
        "Patrimoine net": patrimoine_net,
        "Prix bien": round(prix_bien),
        "Commentaires": "; ".join(commentaires)
    }
    ligne.update(capital_restants)
    tableau.append(ligne)


# ====== AFFICHAGE ======
df = pd.DataFrame(tableau)

st.subheader("Simulation mois par mois")
st.dataframe(df)

# Regrouper par année pour graphique clair
df_annee = df.groupby("Année").agg({
    "Cash flow": "sum",
    "Trésorerie": "last",
    "Dette totale": "last",
    "Valeur patrimoine": "last",
    "Patrimoine net": "last",
    "Prix bien": "last",
    "Loyers bruts": "sum"
}).reset_index()

# ====== Indicateurs finaux ======
st.subheader("Indicateurs finaux")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Nb biens", df["Nb biens"].iloc[-1])
col2.metric("Patrimoine brut", format_nombre(df['Valeur patrimoine'].iloc[-1]))
col3.metric("Dette finale", format_nombre(df['Dette totale'].iloc[-1]))
col4.metric("Patrimoine net", format_nombre(df['Patrimoine net'].iloc[-1]))
col5.metric("Trésorerie finale", format_nombre(df['Trésorerie'].iloc[-1]))

# ====== Graphiques ======
st.subheader("Évolution trésorerie et cash flow")
st.line_chart(df_annee.set_index("Année")[["Cash flow", "Trésorerie"]])

st.subheader("Évolution dette et patrimoine")
st.line_chart(df_annee.set_index("Année")[["Dette totale", "Valeur patrimoine", "Patrimoine net"]])

# ====== Évolution du prix d’un bien avec appréciation ======
df_prix = pd.DataFrame({
    "Année": range(1, duree_totale_annees+1),
    "Prix du bien": [round(prix_bien_initial * (1 + appreciation) ** (annee-1)) for annee in range(1, duree_totale_annees+1)]
})

st.subheader("Évolution du prix d’un bien (avec appréciation)")
st.dataframe(df_prix)

st.subheader("Revenus locatifs bruts générés par an")
st.line_chart(df_annee.set_index("Année")[["Loyers bruts"]])

# ====== Nombre de biens ======
df_biens = df.groupby("Année").agg({"Nb biens": "last"}).reset_index()
st.subheader("Évolution du nombre de biens par année")
st.line_chart(df_biens.set_index("Année")["Nb biens"])


# ====== Cash flow cumulatif ======
df_annee["Cash flow cumulatif"] = df_annee["Cash flow"].cumsum()
st.subheader("Cash flow cumulatif")
st.line_chart(df_annee.set_index("Année")[["Cash flow cumulatif"]])


# ====== Évolution des dettes par prêt (annuel) ======
prets_cols = [col for col in df.columns if col.startswith("Prêt ")]

if prets_cols:
    df_prets_annee = df.groupby("Année")[prets_cols].last().reset_index()

    # Ajout d'une colonne Dette totale
    df_prets_annee["Dette totale"] = df_prets_annee[prets_cols].sum(axis=1)

    st.subheader("Évolution des dettes par prêt (annuel)")

    # Tableau avec colonne dette totale
    st.dataframe(df_prets_annee)

    # Graphique
    st.line_chart(df_prets_annee.set_index("Année"))


