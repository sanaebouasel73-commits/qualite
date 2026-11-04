# -*- coding: utf-8 -*-
"""
Dashboard Streamlit : suivi des KPI qualité automobile
Projet YaneCode Academy - BOUASEL Sanae

Lancement :  streamlit run app.py
Connexion :  utilisateur  dashbord_sanae   |   mot de passe  automobile
"""
import hmac
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Qualité Automobile | Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

UTILISATEUR = "dashbord_sanae"
MOT_DE_PASSE = "automobile"
FICHIER_DONNEES = Path(__file__).parent / "database.csv"
OBJECTIF = 98.0  # objectif de conformité (%)

PRIMAIRE, ORANGE, VERT, ROUGE, GRIS = "#E63946", "#FFB703", "#2FBF71", "#FF4D4D", "#8A8A8A"
FOND_GRAPHIQUE = "#141414"

sns.set_theme(
    style="whitegrid",
    rc={
        "figure.facecolor": FOND_GRAPHIQUE, "axes.facecolor": FOND_GRAPHIQUE, "savefig.facecolor": FOND_GRAPHIQUE,
        "text.color": "#F5F5F5", "axes.labelcolor": "#F5F5F5", "axes.edgecolor": "#444444",
        "xtick.color": "#D0D0D0", "ytick.color": "#D0D0D0", "grid.color": "#2B2B2B",
        "axes.titleweight": "bold", "axes.titlesize": 12, "axes.labelsize": 10,
        "legend.facecolor": "#1E1E1E", "legend.edgecolor": "#444444", "legend.labelcolor": "#F5F5F5",
    },
)

CSS = """
<style>
    .stApp {background: linear-gradient(135deg, #000000 0%, #120000 45%, #4a0000 100%); background-attachment: fixed;}
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1400px;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stSidebar"] {background: #070707; border-right: 2px solid #8B0000;}
    .bandeau {
        background: linear-gradient(120deg, #000000 0%, #7A0010 60%, #C1121F 100%);
        color: white; padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
        border: 1px solid #C1121F; box-shadow: 0 6px 22px rgba(193, 18, 31, .35);
    }
    .bandeau h1 {margin: 0; font-size: 1.7rem; color: white;}
    .bandeau p {margin: .3rem 0 0 0; opacity: .9; font-size: .95rem;}
    .kpi {
        background: #0D0D0D; border: 2px solid #E63946; border-radius: 14px; padding: 1.1rem 1.2rem;
        margin-bottom: 1rem; min-height: 140px; text-align: center;
        display: flex; flex-direction: column; justify-content: center;
        box-shadow: 0 0 14px rgba(230, 57, 70, .25);
    }
    .kpi-t {font-size: .8rem; color: #BDBDBD; font-weight: 600; text-transform: uppercase; letter-spacing: .05em;}
    .kpi-v {font-size: 2rem; font-weight: 700; color: #FFFFFF; line-height: 1.3;}
    .kpi-s {font-size: .85rem; font-weight: 600;}
    .carte {
        background: #0D0D0D; border: 1px solid #8B0000; border-radius: 14px; padding: 1.1rem 1.4rem; height: 100%;
    }
    .carte h4 {margin-top: 0; color: #FF4D4D;}
    .login-tete {
        background: linear-gradient(120deg, #000000 0%, #C1121F 100%);
        color: white; padding: 1.6rem; border-radius: 16px 16px 0 0; text-align: center;
        border: 1px solid #C1121F;
    }
    .login-tete h2 {margin: 0; color: white;}
    .login-tete p {margin: .4rem 0 0 0; opacity: .9;}
    .stForm {background: #0D0D0D; border: 1px solid #8B0000 !important; border-radius: 0 0 16px 16px;}
    .stForm button {width: 100%;}
    div[data-baseweb="tab-list"] {gap: .4rem;}
    button[data-baseweb="tab"] {border-radius: 10px 10px 0 0; padding: .5rem 1rem;}
</style>
"""


# ----------------------------------------------------------------------------
# OUTILS DE FORMATAGE
# ----------------------------------------------------------------------------
def nb(x, dec=0):
    """Format français : espace pour les milliers, virgule pour les décimales."""
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def mad(x):
    return f"{nb(x / 1e6, 2)} M MAD" if abs(x) >= 1e6 else f"{nb(x)} MAD"


# ----------------------------------------------------------------------------
# AUTHENTIFICATION
# ----------------------------------------------------------------------------
def identifiants_valides(utilisateur, mot_de_passe):
    ok_u = hmac.compare_digest(utilisateur.encode(), UTILISATEUR.encode())
    ok_p = hmac.compare_digest(mot_de_passe.encode(), MOT_DE_PASSE.encode())
    return ok_u and ok_p


def page_connexion():
    st.markdown(CSS, unsafe_allow_html=True)
    _, centre, _ = st.columns([1, 1.1, 1])
    with centre:
        st.write("")
        st.write("")
        st.markdown(
            '<div class="login-tete"><h2>Qualité Automobile</h2>'
            "<p>Connectez-vous pour accéder au tableau de bord</p></div>",
            unsafe_allow_html=True,
        )
        with st.form("connexion"):
            utilisateur = st.text_input("Nom d'utilisateur")
            mot_de_passe = st.text_input("Mot de passe", type="password")
            envoye = st.form_submit_button("Se connecter")
        if envoye:
            if identifiants_valides(utilisateur.strip(), mot_de_passe):
                st.session_state["connecte"] = True
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")


def deconnexion():
    st.session_state["connecte"] = False


# ----------------------------------------------------------------------------
# CHARGEMENT ET NETTOYAGE DES DONNÉES
# ----------------------------------------------------------------------------
COLONNES_TEXTE = [
    "mois", "equipe", "usine", "ligne", "poste_controle", "famille_piece",
    "reference", "fournisseur", "defaut_principal", "statut_lot", "inspecteur",
]
COLONNES_NOMBRES = [
    "semaine", "quantite_controlee", "nb_conformes", "nb_retouches", "nb_rejets",
    "cout_retouche_mad", "cout_rebut_mad", "objectif_conformite_pct",
]


def nettoyer(brut):
    """Nettoie le jeu de données et renvoie (DataFrame propre, rapport de nettoyage)."""
    df = brut.copy()
    rapport = []

    def noter(etape, constat, action):
        rapport.append({"Étape": etape, "Constat": constat, "Action": action})

    noter("Import", f"{nb(len(df))} lignes, {df.shape[1]} colonnes", "Lecture du fichier CSV (UTF-8)")

    # 1. Noms de colonnes et espaces parasites
    df.columns = [c.strip().lower() for c in df.columns]
    modifies = 0
    for c in COLONNES_TEXTE:
        if c in df.columns:
            avant = df[c].astype("string")
            apres = avant.str.strip().str.replace(r"\s+", " ", regex=True)
            modifies += int((avant.fillna("") != apres.fillna("")).sum())
            df[c] = apres.replace("", pd.NA)
    noter("Texte", f"{nb(modifies)} valeurs avec espaces en trop", "Suppression des espaces superflus")

    # 2. Doublons
    n_doublons = int(df.duplicated().sum())
    df = df.drop_duplicates()
    noter("Doublons", f"{nb(n_doublons)} lignes identiques", "Suppression des doublons")

    # 3. Types
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in COLONNES_NOMBRES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    n_avant = len(df)
    critiques = ["date", "quantite_controlee", "nb_conformes", "nb_retouches", "nb_rejets"]
    df = df.dropna(subset=critiques)
    noter("Valeurs manquantes", f"{nb(n_avant - len(df))} lignes avec date ou comptage manquant",
          "Lignes supprimées")
    for c in ["equipe", "usine", "ligne", "poste_controle", "famille_piece", "fournisseur",
              "defaut_principal", "statut_lot"]:
        manquants = int(df[c].isna().sum())
        if manquants:
            df[c] = df[c].fillna("Non renseigné")
            noter("Valeurs manquantes", f"{manquants} valeurs vides dans « {c} »", "Remplacées par « Non renseigné »")
    df["objectif_conformite_pct"] = df["objectif_conformite_pct"].fillna(OBJECTIF)

    # 4. Cohérence des comptages
    n_avant = len(df)
    negatifs = (df[["quantite_controlee", "nb_conformes", "nb_retouches", "nb_rejets"]] < 0).any(axis=1)
    nulle = df["quantite_controlee"] <= 0
    somme_ko = (df["nb_conformes"] + df["nb_retouches"] + df["nb_rejets"]) != df["quantite_controlee"]
    df = df[~(negatifs | nulle | somme_ko)]
    noter("Cohérence", f"{nb(n_avant - len(df))} lignes incohérentes (quantité nulle, valeurs négatives, "
                       "conformes + retouches + rejets ≠ quantité)", "Lignes supprimées")

    # 5. Recalcul des indicateurs dérivés
    q = df["quantite_controlee"]
    nouveaux = {
        "taux_conformite_pct": (df["nb_conformes"] / q * 100).round(2),
        "taux_retouche_pct": (df["nb_retouches"] / q * 100).round(2),
        "taux_rejet_pct": (df["nb_rejets"] / q * 100).round(2),
        "ppm_rejet": (df["nb_rejets"] / q * 1e6).round(0),
        "cout_non_qualite_mad": df["cout_retouche_mad"] + df["cout_rebut_mad"],
    }
    ecarts = 0
    for col, serie in nouveaux.items():
        if col in df.columns:
            ecarts += int(((pd.to_numeric(df[col], errors="coerce") - serie).abs() > 0.51).sum())
        df[col] = serie
    noter("Indicateurs", f"{nb(ecarts)} valeurs dérivées incorrectes", "Taux, PPM et coût total recalculés à partir des comptages")

    # 6. Colonnes utiles
    df["mois"] = df["date"].dt.strftime("%Y-%m")
    df["lot_bloque"] = (df["statut_lot"] == "Bloqué").astype(int)
    df["non_conformes"] = df["nb_retouches"] + df["nb_rejets"]

    # 7. Valeurs atypiques (information seulement)
    seuil = df["taux_rejet_pct"].quantile(0.75) + 3 * (
        df["taux_rejet_pct"].quantile(0.75) - df["taux_rejet_pct"].quantile(0.25))
    atypiques = int((df["taux_rejet_pct"] > seuil).sum())
    noter("Valeurs atypiques", f"{nb(atypiques)} lots avec un taux de rejet très élevé (> {nb(seuil, 2)} %)",
          "Conservés : ce sont de vrais incidents qualité, utiles à l'analyse")

    df = df.sort_values("date").reset_index(drop=True)
    noter("Résultat", f"{nb(len(df))} lignes propres, du {df['date'].min():%d/%m/%Y} au {df['date'].max():%d/%m/%Y}",
          "Données prêtes pour l'analyse")
    return df, pd.DataFrame(rapport)


@st.cache_data(show_spinner="Chargement et nettoyage des données…")
def charger_donnees(chemin):
    brut = pd.read_csv(chemin, encoding="utf-8-sig")
    return nettoyer(brut)


# ----------------------------------------------------------------------------
# CALCUL DES KPI
# ----------------------------------------------------------------------------
def agreger(df, par):
    """KPI pondérés par la quantité contrôlée, pour un ou plusieurs axes."""
    g = df.groupby(par, observed=True).agg(
        qte=("quantite_controlee", "sum"),
        conformes=("nb_conformes", "sum"),
        retouches=("nb_retouches", "sum"),
        rejets=("nb_rejets", "sum"),
        cout=("cout_non_qualite_mad", "sum"),
        cout_rebut=("cout_rebut_mad", "sum"),
        lots=("quantite_controlee", "size"),
        bloques=("lot_bloque", "sum"),
    ).reset_index()
    g["conformite"] = g["conformes"] / g["qte"] * 100
    g["retouche"] = g["retouches"] / g["qte"] * 100
    g["rejet"] = g["rejets"] / g["qte"] * 100
    g["ppm"] = g["rejets"] / g["qte"] * 1e6
    g["pct_bloques"] = g["bloques"] / g["lots"] * 100
    return g


def totaux(df):
    t = agreger(df.assign(_tout="Total"), "_tout").iloc[0]
    return t


def carte(titre, valeur, sous_titre, couleur=PRIMAIRE, icone=""):
    return (
        '<div class="kpi">'
        f'<div class="kpi-t">{icone} {titre}</div>'
        f'<div class="kpi-v">{valeur}</div>'
        f'<div class="kpi-s" style="color:{couleur}">{sous_titre}</div></div>'
    )


# ----------------------------------------------------------------------------
# GRAPHIQUES
# ----------------------------------------------------------------------------
def nouvelle_figure(largeur=7, hauteur=4):
    fig, ax = plt.subplots(figsize=(largeur, hauteur))
    return fig, ax


def afficher(fig):
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)


def barres_horizontales(donnees, categorie, valeur, titre, objectif=None, fmt="{:.2f} %", xlabel=""):
    """Barres horizontales triées ; vert = atteint l'objectif, rouge = sous l'objectif."""
    d = donnees.sort_values(valeur, ascending=False)
    ordre = d[categorie].tolist()
    if objectif is not None:
        couleurs = {c: (VERT if v >= objectif else ROUGE) for c, v in zip(d[categorie], d[valeur])}
    else:
        couleurs = {c: PRIMAIRE for c in ordre}
    fig, ax = nouvelle_figure(7, max(2.8, 0.55 * len(d) + 1.2))
    sns.barplot(data=d, x=valeur, y=categorie, hue=categorie, order=ordre, palette=couleurs,
                legend=False, ax=ax)
    if objectif is not None:
        ax.axvline(objectif, color=ORANGE, linestyle="--", linewidth=1.6, label=f"Objectif {objectif:.0f} %")
        ax.legend(loc="lower right", frameon=True)
        bas = np.floor(d[valeur].min()) - 1.5
        ax.set_xlim(bas, max(100.6, d[valeur].max() + 0.3))
    else:
        ax.set_xlim(0, d[valeur].max() * 1.18)
    marge = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.01
    for i, (_, ligne) in enumerate(d.iterrows()):
        ax.text(ligne[valeur] + marge, i, fmt.format(ligne[valeur]), va="center", fontsize=9, fontweight="bold")
    ax.set_title(titre, loc="left")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("")
    sns.despine(left=True, bottom=True)
    return fig


def carte_chaleur(donnees, lignes, colonnes, valeur, titre, fmt=".1f"):
    p = donnees.pivot_table(index=lignes, columns=colonnes, values=valeur)
    fig, ax = nouvelle_figure(8, max(3, 0.55 * len(p) + 1.5))
    sns.heatmap(p, annot=True, fmt=fmt, cmap="YlOrRd_r", linewidths=1, linecolor=FOND_GRAPHIQUE,
                cbar_kws={"label": "Conformité (%)"}, vmin=p.min().min(), vmax=max(p.max().max(), OBJECTIF + 0.5), ax=ax)
    ax.set_title(titre, loc="left")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    plt.setp(ax.get_yticklabels(), rotation=0)
    return fig


def etiquettes_mois(ax, mois):
    pas = max(1, len(mois) // 11)
    positions = list(range(0, len(mois), pas))
    ax.set_xticks(positions)
    ax.set_xticklabels([mois[i] for i in positions], rotation=45, ha="right")


def tendance_conformite(mensuel):
    x = np.arange(len(mensuel))
    y = mensuel["conformite"].to_numpy()
    fig, ax = nouvelle_figure(9, 4.2)
    ax.axhline(OBJECTIF, color=ORANGE, linestyle="--", linewidth=1.6, label=f"Objectif {OBJECTIF:.0f} %")
    sns.lineplot(x=x, y=y, marker="o", color=PRIMAIRE, linewidth=2.4, label="Conformité mensuelle", ax=ax)
    if len(x) >= 3:
        pente, origine = np.polyfit(x, y, 1)
        ax.plot(x, pente * x + origine, color="#F5F5F5", linestyle=":", linewidth=2, label="Tendance")
    ax.fill_between(x, y, OBJECTIF, where=(y < OBJECTIF), color=ROUGE, alpha=0.10)
    etiquettes_mois(ax, mensuel["mois"].tolist())
    ax.set_title("Taux De Conformité Mensuel Vs Objectif", loc="left")
    ax.set_ylabel("Conformité (%)")
    ax.set_xlabel("")
    ax.legend(loc="lower right")
    sns.despine()
    return fig


def donut_statuts(df):
    comptes = df["statut_lot"].value_counts()
    couleurs = {"Accepté": VERT, "Accepté sous dérogation": ORANGE, "Bloqué": ROUGE}
    fig, ax = nouvelle_figure(4.5, 4.2)
    ax.pie(comptes.values, labels=comptes.index, autopct="%1.1f%%", startangle=90, pctdistance=0.78,
           colors=[couleurs.get(c, GRIS) for c in comptes.index],
           wedgeprops={"width": 0.42, "edgecolor": FOND_GRAPHIQUE, "linewidth": 2}, textprops={"fontsize": 9})
    ax.set_title("Statut Des Lots", loc="left")
    return fig


def taux_mensuels(mensuel):
    x = np.arange(len(mensuel))
    fig, ax = nouvelle_figure(7, 3.8)
    sns.lineplot(x=x, y=mensuel["rejet"], marker="o", color=ROUGE, linewidth=2.2, label="Taux De Rejet", ax=ax)
    sns.lineplot(x=x, y=mensuel["retouche"], marker="s", color=ORANGE, linewidth=2.2, label="Taux De Retouche", ax=ax)
    etiquettes_mois(ax, mensuel["mois"].tolist())
    ax.set_title("Rejets Et Retouches Par Mois", loc="left")
    ax.set_ylabel("%")
    ax.set_xlabel("")
    sns.despine()
    return fig


def cout_mensuel(mensuel):
    x = np.arange(len(mensuel))
    fig, ax = nouvelle_figure(7, 3.8)
    ax.bar(x, mensuel["cout"] / 1e6, color=PRIMAIRE, alpha=0.9)
    etiquettes_mois(ax, mensuel["mois"].tolist())
    ax.set_title("Coût De La Non-Qualité Par Mois", loc="left")
    ax.set_ylabel("Millions de MAD")
    sns.despine()
    return fig


def evolution_par_groupe(df, groupe, titre):
    d = agreger(df, ["mois", groupe]).sort_values("mois")
    mois = sorted(d["mois"].unique())
    d["x"] = d["mois"].map({m: i for i, m in enumerate(mois)})
    fig, ax = nouvelle_figure(8, 4)
    sns.lineplot(data=d, x="x", y="conformite", hue=groupe, marker="o", linewidth=2, palette=[PRIMAIRE, "#F5F5F5", ORANGE, VERT][:d[groupe].nunique()], ax=ax)
    ax.axhline(OBJECTIF, color=ORANGE, linestyle="--", linewidth=1.4)
    etiquettes_mois(ax, mois)
    ax.set_title(titre, loc="left")
    ax.set_ylabel("Conformité (%)")
    ax.set_xlabel("")
    ax.legend(title="", loc="lower right", ncol=2, fontsize=8)
    sns.despine()
    return fig


def pareto(df, mesure):
    d = df[df["defaut_principal"] != "Aucun"]
    colonne = "non_conformes" if mesure == "Pièces non conformes" else "cout_non_qualite_mad"
    s = d.groupby("defaut_principal")[colonne].sum().sort_values(ascending=False)
    cumul = s.cumsum() / s.sum() * 100
    couleurs = [PRIMAIRE if (c - v / s.sum() * 100) < 80 else GRIS for v, c in zip(s.values, cumul.values)]
    fig, ax = nouvelle_figure(11, 4.8)
    ax.bar(range(len(s)), s.values, color=couleurs)
    ax.set_xticks(range(len(s)))
    ax.set_xticklabels(s.index, rotation=50, ha="right", fontsize=9)
    ax.set_ylabel("Pièces non conformes" if colonne == "non_conformes" else "Coût (MAD)")
    ax2 = ax.twinx()
    sns.lineplot(x=range(len(s)), y=cumul.values, marker="o", color="#F5F5F5", linewidth=2, ax=ax2)
    ax2.axhline(80, color=ORANGE, linestyle="--", linewidth=1.2)
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumul (%)")
    ax2.grid(False)
    ax.set_title(f"Pareto Des Défauts : {mesure.lower()}", loc="left")
    sns.despine(right=False)
    return fig, s, cumul


# ----------------------------------------------------------------------------
# FILTRES
# ----------------------------------------------------------------------------
def reinitialiser_filtres():
    for cle in [k for k in st.session_state if k.startswith("f_")]:
        del st.session_state[cle]


def appliquer_filtres(df):
    st.sidebar.markdown("### 🎛️ Filtres")
    st.sidebar.caption("Cochez les éléments à afficher.")
    d_min, d_max = df["date"].min().date(), df["date"].max().date()
    periode = st.sidebar.date_input("Période", value=(d_min, d_max), min_value=d_min, max_value=d_max,
                                    format="DD/MM/YYYY", key="f_periode")
    if isinstance(periode, (tuple, list)) and len(periode) == 2:
        debut, fin = periode
    else:
        debut, fin = d_min, d_max
    masque = (df["date"].dt.date >= debut) & (df["date"].dt.date <= fin)

    filtres = [
        ("usine", "Site (Usine)", True), ("equipe", "Équipe", True), ("ligne", "Ligne De Production", True),
        ("poste_controle", "Poste De Contrôle", False), ("famille_piece", "Famille De Pièces", False),
        ("fournisseur", "Fournisseur", False), ("statut_lot", "Statut Du Lot", False),
    ]
    for colonne, libelle, ouvert in filtres:
        options = sorted(df[colonne].unique())
        with st.sidebar.expander(libelle, expanded=ouvert):
            choix = [o for o in options if st.checkbox(str(o), value=True, key=f"f_{colonne}_{o}")]
        masque &= df[colonne].isin(choix)

    st.sidebar.button("↺ Tout recocher", on_click=reinitialiser_filtres)
    return df[masque]


# ----------------------------------------------------------------------------
# ONGLETS
# ----------------------------------------------------------------------------
def onglet_synthese(df):
    t = totaux(df)
    ecart = t["conformite"] - OBJECTIF
    atteint = ecart >= 0
    sous_titre_conf = (f"▲ +{nb(ecart, 2)} pt au-dessus de l'objectif ({OBJECTIF:.0f} %)" if atteint
                       else f"▼ {nb(ecart, 2).replace('-', '−')} pt sous l'objectif ({OBJECTIF:.0f} %)")

    c1, c2, c3 = st.columns(3)
    c1.markdown(carte("Taux De Conformité", f"{nb(t['conformite'], 2)} %", sous_titre_conf,
                      VERT if atteint else ROUGE, "✅"), unsafe_allow_html=True)
    c2.markdown(carte("Taux De Rejet", f"{nb(t['rejet'], 2)} %", f"{nb(t['rejets'])} pièces rejetées",
                      ROUGE, "🚫"), unsafe_allow_html=True)
    c3.markdown(carte("Taux De Retouche", f"{nb(t['retouche'], 2)} %", f"{nb(t['retouches'])} pièces retouchées",
                      ORANGE, "🔧"), unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    c4.markdown(carte("PPM De Rejet", nb(t["ppm"]), "pièces rejetées par million", PRIMAIRE, "📊"),
                unsafe_allow_html=True)
    c5.markdown(carte("Coût De La Non-Qualité", mad(t["cout"]),
                      f"dont {nb(t['cout_rebut'] / t['cout'] * 100 if t['cout'] else 0, 0)} % de rebuts", ORANGE, "💰"),
                unsafe_allow_html=True)
    c6.markdown(carte("Lots Bloqués", f"{nb(t['pct_bloques'], 1)} %",
                      f"{nb(t['bloques'])} lots sur {nb(t['lots'])}", ROUGE if t["pct_bloques"] > 20 else PRIMAIRE, "⛔"),
                unsafe_allow_html=True)

    mensuel = agreger(df, "mois").sort_values("mois")
    g1, g2 = st.columns([2, 1])
    with g1:
        afficher(tendance_conformite(mensuel))
    with g2:
        afficher(donut_statuts(df))
    g3, g4 = st.columns(2)
    with g3:
        afficher(taux_mensuels(mensuel))
    with g4:
        afficher(cout_mensuel(mensuel))


def onglet_fournisseurs(df):
    f = agreger(df, "fournisseur")
    g1, g2 = st.columns([1, 1])
    with g1:
        afficher(barres_horizontales(f, "fournisseur", "conformite", "Classement Des Fournisseurs Par Conformité",
                                     objectif=OBJECTIF, xlabel="Conformité (%)"))
    with g2:
        afficher(barres_horizontales(f, "fournisseur", "cout", "Coût De La Non-Qualité Par Fournisseur",
                                     fmt="{:,.0f}", xlabel="MAD"))
    st.markdown("##### Tableau De Classement")
    tableau = f.sort_values("conformite", ascending=False).reset_index(drop=True)
    tableau.insert(0, "Rang", tableau.index + 1)
    tableau = tableau[["Rang", "fournisseur", "conformite", "rejet", "retouche", "ppm", "cout", "pct_bloques", "lots"]]
    tableau.columns = ["Rang", "Fournisseur", "Conformité (%)", "Rejet (%)", "Retouche (%)", "PPM",
                       "Coût (MAD)", "Lots bloqués (%)", "Lots"]
    st.dataframe(
        tableau.style.format({"Conformité (%)": "{:.2f}", "Rejet (%)": "{:.2f}", "Retouche (%)": "{:.2f}",
                              "PPM": "{:,.0f}", "Coût (MAD)": "{:,.0f}", "Lots bloqués (%)": "{:.1f}"})
        .background_gradient(subset=["Conformité (%)"], cmap="RdYlGn")
        .background_gradient(subset=["Rejet (%)"], cmap="Reds"),
        hide_index=True,
    )
    afficher(carte_chaleur(agreger(df, ["fournisseur", "famille_piece"]), "fournisseur", "famille_piece",
                           "conformite", "Conformité (%) : Fournisseur × Famille De Pièces"))


def onglet_pieces(df):
    fam = agreger(df, "famille_piece")
    g1, g2 = st.columns([1, 1])
    with g1:
        afficher(barres_horizontales(fam, "famille_piece", "conformite", "Conformité Par Famille De Pièces",
                                     objectif=OBJECTIF, xlabel="Conformité (%)"))
    with g2:
        afficher(barres_horizontales(fam, "famille_piece", "rejet", "Taux De Rejet Par Famille De Pièces",
                                     fmt="{:.2f} %", xlabel="Rejet (%)"))
    st.markdown("#### Pareto Des Défauts")
    mesure = st.radio("Mesure", ["Pièces non conformes", "Coût De La Non-Qualité"], horizontal=True)
    fig, serie, cumul = pareto(df, "Pièces non conformes" if mesure == "Pièces non conformes" else "Coût")
    afficher(fig)
    vitaux = int((cumul.shift(fill_value=0) < 80).sum())
    st.caption(f"Les {vitaux} premiers défauts (en rouge) représentent environ 80 % du total : "
               "ce sont les priorités d'action. Les lots sans défaut (« Aucun ») sont exclus.")


def onglet_equipes(df):
    eq = agreger(df, "equipe")
    us = agreger(df, "usine")
    g1, g2 = st.columns(2)
    with g1:
        afficher(barres_horizontales(eq, "equipe", "conformite", "Conformité Par Équipe", objectif=OBJECTIF,
                                     xlabel="Conformité (%)"))
    with g2:
        afficher(barres_horizontales(us, "usine", "conformite", "Conformité Par Site", objectif=OBJECTIF,
                                     xlabel="Conformité (%)"))
    g3, g4 = st.columns(2)
    with g3:
        afficher(carte_chaleur(agreger(df, ["equipe", "ligne"]), "equipe", "ligne", "conformite",
                               "Conformité (%) : Équipe × Ligne"))
    with g4:
        afficher(barres_horizontales(agreger(df, "poste_controle"), "poste_controle", "conformite",
                                     "Conformité Par Poste De Contrôle", objectif=OBJECTIF, xlabel="Conformité (%)"))
    afficher(evolution_par_groupe(df, "equipe", "Évolution Mensuelle De La Conformité Par Équipe"))


def onglet_donnees(df, rapport):
    st.markdown("#### 🧹 Rapport De Nettoyage")
    st.dataframe(rapport, hide_index=True)
    st.markdown("#### 🔎 Aperçu Des Données Filtrées")
    colonnes = ["date", "usine", "equipe", "ligne", "famille_piece", "fournisseur", "quantite_controlee",
                "taux_conformite_pct", "taux_rejet_pct", "defaut_principal", "cout_non_qualite_mad", "statut_lot"]
    st.dataframe(df[colonnes].head(200), hide_index=True)
    st.download_button("⬇️ Télécharger les données filtrées (CSV)",
                       df.drop(columns=["lot_bloque", "non_conformes"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name="donnees_filtrees.csv", mime="text/csv")
    with st.expander("Statistiques descriptives"):
        st.dataframe(df[["quantite_controlee", "taux_conformite_pct", "taux_retouche_pct", "taux_rejet_pct",
                         "ppm_rejet", "cout_non_qualite_mad"]].describe().T)


def onglet_conclusions(df):
    t = totaux(df)
    f = agreger(df, "fournisseur").sort_values("conformite")
    fam = agreger(df, "famille_piece").sort_values("conformite")
    eq = agreger(df, "equipe").sort_values("conformite")
    mensuel = agreger(df, "mois").sort_values("mois")
    sous_obj = int((f["conformite"] < OBJECTIF).sum())

    pire_f, meilleur_f = f.iloc[0], f.iloc[-1]
    pire_fam = fam.iloc[0]
    pire_eq, meilleure_eq = eq.iloc[0], eq.iloc[-1]
    part_cout = pire_f["cout"] / t["cout"] * 100 if t["cout"] else 0

    constats = [
        f"**Conformité globale : {nb(t['conformite'], 2)} %**, soit "
        f"{'au-dessus' if t['conformite'] >= OBJECTIF else 'sous'} l'objectif de {OBJECTIF:.0f} % "
        f"({nb(abs(t['conformite'] - OBJECTIF), 2)} pt d'écart).",
        f"**{pire_f['fournisseur']} est le fournisseur le moins bon** ({nb(pire_f['conformite'], 2)} %, "
        f"{nb(pire_f['ppm'])} PPM) et pèse {nb(part_cout, 0)} % du coût de non-qualité. "
        f"Le meilleur est {meilleur_f['fournisseur']} ({nb(meilleur_f['conformite'], 2)} %). "
        f"{sous_obj} fournisseur(s) sur {len(f)} sont sous l'objectif.",
        f"**La famille la plus problématique est : {pire_fam['famille_piece']}** "
        f"({nb(pire_fam['conformite'], 2)} % de conformité, {nb(pire_fam['rejet'], 2)} % de rejet).",
        f"**L'équipe « {pire_eq['equipe']} » est la plus faible** ({nb(pire_eq['conformite'], 2)} %), "
        f"à {nb(meilleure_eq['conformite'] - pire_eq['conformite'], 2)} pt de l'équipe « {meilleure_eq['equipe']} ».",
    ]
    if len(mensuel) >= 3:
        pente = np.polyfit(np.arange(len(mensuel)), mensuel["conformite"], 1)[0]
        premier, dernier = mensuel.iloc[0], mensuel.iloc[-1]
        sens = "s'améliore" if pente > 0 else "se dégrade"
        constats.append(
            f"**La qualité {sens} avec le temps** : {nb(premier['conformite'], 2)} % en {premier['mois']} "
            f"contre {nb(dernier['conformite'], 2)} % en {dernier['mois']} "
            f"({'+' if pente > 0 else '−'}{nb(abs(pente), 2)} pt par mois en moyenne)."
        )

    recommandations = [
        f"**Fournisseurs** : lancer un plan d'action correctif (8D) avec {pire_f['fournisseur']}, renforcer le "
        "contrôle à réception et suspendre les nouvelles commandes tant que l'objectif n'est pas atteint.",
        f"**Pièces** : mettre sous surveillance renforcée la famille « {pire_fam['famille_piece']} » "
        "(test de continuité, vérification du routage et des connecteurs avant expédition).",
        f"**Équipes** : analyser les causes de l'écart de l'équipe « {pire_eq['equipe']} » (fatigue, supervision, "
        "éclairage, effectif) et standardiser les bonnes pratiques de l'équipe la plus performante.",
        "**Défauts** : traiter en priorité les défauts du Pareto qui représentent 80 % du coût de non-qualité.",
        "**Pilotage** : suivre ces KPI chaque semaine, avec des alertes lorsque la conformité d'un fournisseur "
        f"passe sous {OBJECTIF:.0f} %.",
    ]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="carte"><h4>📌 Constats</h4>' + "".join(
            f"<p>{x}</p>" for x in constats).replace("**", "") + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="carte"><h4>✅ Recommandations</h4>' + "".join(
            f"<p>{x}</p>" for x in recommandations).replace("**", "") + "</div>", unsafe_allow_html=True)
    st.caption("Ces conclusions se recalculent automatiquement selon les filtres choisis dans la barre latérale.")


# ----------------------------------------------------------------------------
# APPLICATION
# ----------------------------------------------------------------------------
def application():
    st.markdown(CSS, unsafe_allow_html=True)
    if not FICHIER_DONNEES.exists():
        st.error("Fichier « database.csv » introuvable : placez-le dans le même dossier que app.py.")
        st.stop()
    donnees, rapport = charger_donnees(str(FICHIER_DONNEES))

    st.sidebar.markdown("## Qualité Automobile")
    st.sidebar.caption(f"Connecté : **{UTILISATEUR}**")
    st.sidebar.button("🚪 Se déconnecter", on_click=deconnexion)
    st.sidebar.divider()
    df = appliquer_filtres(donnees)

    st.markdown(
        '<div class="bandeau"><h1>Tableau De Bord Qualité Automobile</h1>'
        "<p>Suivi des KPI de conformité, rejet, retouche, PPM et coût de la non-qualité "
        f"· {nb(len(df))} lots affichés sur {nb(len(donnees))}</p></div>",
        unsafe_allow_html=True,
    )
    if df.empty:
        st.warning("Aucune donnée ne correspond aux filtres sélectionnés. Élargissez la sélection.")
        st.stop()

    onglets = st.tabs(["📈 Synthèse", "🏭 Fournisseurs", "🔩 Pièces Et Défauts", "👥 Équipes Et Sites",
                       "🧹 Données", "🧭 Conclusions"])
    with onglets[0]:
        onglet_synthese(df)
    with onglets[1]:
        onglet_fournisseurs(df)
    with onglets[2]:
        onglet_pieces(df)
    with onglets[3]:
        onglet_equipes(df)
    with onglets[4]:
        onglet_donnees(df, rapport)
    with onglets[5]:
        onglet_conclusions(df)


if st.session_state.get("connecte"):
    application()
else:
    page_connexion()
