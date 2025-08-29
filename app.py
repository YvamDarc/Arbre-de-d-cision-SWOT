# app.py
# Streamlit — Diagnostic orienté besoins (SWOT) pour construire une offre de service commerciale
# Objectif : Diagnostiquer, détecter des besoins précis, les rattacher aux services/offres,
# puis générer des "événements" (emails/export) vers les pôles concernés.
# Lancer : streamlit run app.py

import streamlit as st
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import datetime
import pandas as pd
from io import BytesIO, StringIO
import textwrap

st.set_page_config(page_title="Diagnostic & besoins — Cabinet EC", page_icon="🧭", layout="wide")

# =====================================
# Catalogues & constantes
# =====================================

SECTEURS = ["BTP", "Commerce", "Services", "Industrie", "Agricole", "Professions libérales", "E-commerce", "Santé", "Tech/SaaS", "Autre"]
DIGITAL = ["Pas informatique", "Informatique rudimentaire", "Informatique avancée"]
TAILLE = ["0 salarié", "1-10", "11-49", "50-249", "250+"]
IMPACT_ENV = ["Faible/Non", "Moyenne", "Importante"]
HORIZON_RETRAITE = ["Loin (> 5 ans)", "À 5 ans", "< 2 ans"]
EXPO_INTERNATIONAL = ["Aucune", "Occasionnelle", "Régulière/Structurée"]
DEPENDANCE_CLIENT = ["Faible (<20%)", "Moyenne (20-40%)", "Forte (>40%)"]

SERVICES = {
    "social": "Service Paie & RH",
    "fiscal": "Pôle Fiscal",
    "patrimonial": "Pôle Conseil Patrimonial",
    "rse": "Pôle RSE / CSRD",
    "eco_strat": "Pôle Conseil Éco & Stratégie",
    "gestion": "Pôle Gestion / Contrôle de gestion",
    "digital": "Pôle Digitalisation",
    "international": "Pôle International",
    "btp": "Pôle Secteur BTP"
}

# Offres indicatives (non tarifées ici ; l'outil est centré diagnostic)
OFFRES = {
    "social": ["Audit social", "Paie externalisée", "Mise en place SIRH", "Procédures RH"],
    "fiscal": ["Revue fiscale", "Note TVA spécifique", "Sécurisation crédits d'impôt"],
    "patrimonial": ["Bilan patrimonial", "Pré-étude Dutreil", "Structuration holding/SCI"],
    "rse": ["Diagnostic RSE", "Matrice de matérialité", "Préparation CSRD (PME)"],
    "eco_strat": ["Diagnostic stratégique", "Prix de revient & pricing", "Business plan & financement", "Croissance externe"],
    "gestion": ["Tableaux de bord", "Budget & prévisionnel", "Cash management"],
    "digital": ["Cartographie outils", "OCR & API banques", "Hub facturation/achat"],
    "international": ["TVA OSS/IOSS", "DEB/DES & douanes", "Implantation UE/Export"],
    "btp": ["Suivi chantiers", "Retenues de garantie", "Situations & DGD"]
}

DEFAULT_RECIPIENTS = {
    "social": "service-paie@cabinet.com",
    "fiscal": "pole-fiscal@cabinet.com",
    "patrimonial": "conseil-patrimonial@cabinet.com",
    "rse": "rse@cabinet.com",
    "eco_strat": "eco-strategie@cabinet.com",
    "gestion": "controle-gestion@cabinet.com",
    "digital": "digital@cabinet.com",
    "international": "international@cabinet.com",
    "btp": "btp@cabinet.com"
}

PRIORITES = ["Haute", "Moyenne", "Basse"]
ECHEANCES = ["Immédiat (≤ 3 mois)", "6-12 mois", "> 12 mois"]

# =====================================
# Data Models
# =====================================

@dataclass
class ClientProfile:
    nom: str
    secteur: str
    taille: str
    digital: str
    impact_env: str
    rse_sensible: bool
    presence_cadres: bool
    exposition_internationale: str
    dependance_client: str
    croissance: str  # "En baisse", "Stable", "En croissance"
    marge: str       # "Faible", "Correcte", "Confortable"
    tresorerie_tendue: bool
    reporting_mensuel: bool
    nb_banques: int
    proche_retraite: str
    succession_envisagee: bool
    patrimoine_dirigeant_important: bool
    btp_specifique: bool
    ecommerce_plateformes: bool
    risques_juridiques: bool
    notes: str  # notes libres

@dataclass
class Need:
    besoin: str
    service: str
    priorite: str
    echeance: str
    impact: int
    justification: str

# =====================================
# Helpers
# =====================================

def strength(txt: str) -> Dict[str, Any]:
    return {"type": "Force", "texte": txt}

def weakness(txt: str) -> Dict[str, Any]:
    return {"type": "Faiblesse", "texte": txt}

def opportunity(txt: str) -> Dict[str, Any]:
    return {"type": "Opportunité", "texte": txt}

def threat(txt: str) -> Dict[str, Any]:
    return {"type": "Menace", "texte": txt}

def swot_from_profile(p: ClientProfile) -> Dict[str, List[Dict[str, Any]]]:
    F: List[Dict[str, Any]] = []
    fbl: List[Dict[str, Any]] = []
    O: List[Dict[str, Any]] = []
    M: List[Dict[str, Any]] = []

    # Forces
    if p.digital == "Informatique avancée":
        F.append(strength("Digitalisation avancée (intégrations possibles)"))
    if p.reporting_mensuel:
        F.append(strength("Reporting financier mensuel déjà en place"))
    if p.marge == "Confortable":
        F.append(strength("Marge confortable"))
    if p.croissance == "En croissance":
        F.append(strength("Croissance du CA"))

    # Faiblesses
    if p.digital == "Pas informatique":
        fbl.append(weakness("Maturité digitale faible (risque d'erreurs/coûts)"))
    if not p.reporting_mensuel:
        fbl.append(weakness("Absence de reporting/indicateurs réguliers"))
    if p.marge == "Faible":
        fbl.append(weakness("Marge insuffisante / prix de revient non maîtrisé"))
    if p.tresorerie_tendue:
        fbl.append(weakness("Trésorerie tendue / pas de prévisionnel"))

    # Opportunités
    if p.proche_retraite in ("À 5 ans", "< 2 ans"):
        O.append(opportunity("Préparer la transmission / retraite dirigeant"))
    if p.patrimoine_dirigeant_important:
        O.append(opportunity("Optimisation patrimoniale (holding/SCI/PEA-PME, etc.)"))
    if p.rse_sensible:
        O.append(opportunity("Valorisation via la démarche RSE / CSRD adaptée"))
    if p.exposition_internationale in ("Occasionnelle", "Régulière/Structurée"):
        O.append(opportunity("Développement export / structuration internationale"))

    # Menaces
    if p.impact_env == "Importante":
        M.append(threat("Exposition réglementaire environnementale élevée"))
    if p.dependance_client == "Forte (>40%)":
        M.append(threat("Dépendance à un client majeur"))
    if p.risques_juridiques:
        M.append(threat("Litiges / risques juridiques non traités"))
    if p.taille in ("11-49", "50-249", "250+") and not p.presence_cadres:
        M.append(threat("Obligations sociales renforcées sans structuration RH"))

    # Secteur/Spécifiques
    if p.secteur == "BTP" or p.btp_specifique:
        M.append(threat("Complexité BTP (retenues, situations, DGD)"))
    if p.ecommerce_plateformes:
        M.append(threat("TVA plateformes / marketplace (OSS/IOSS)"))

    return {"Forces": F, "Faiblesses": fbl, "Opportunités": O, "Menaces": M}

def detect_needs(p: ClientProfile, swot: Dict[str, List[Dict[str, Any]]]) -> List[Need]:
    needs: List[Need] = []

    def add(besoin: str, service_key: str, priorite: str, echeance: str, impact: int, justif: str):
        needs.append(Need(
            besoin=besoin,
            service=SERVICES[service_key],
            priorite=priorite,
            echeance=echeance,
            impact=impact,
            justification=justif
        ))

    # Règles issues des faiblesses/menaces
    fb_texts = [x["texte"] for x in swot.get("Faiblesses", [])]
    m_texts = [x["texte"] for x in swot.get("Menaces", [])]

    if "Maturité digitale faible (risque d'erreurs/coûts)" in fb_texts:
        add("Cartographie & plan de digitalisation", "digital", "Moyenne", "6-12 mois", 3, "Digitalisation faible détectée")
    if "Absence de reporting/indicateurs réguliers" in fb_texts:
        add("Mise en place de tableaux de bord mensuels", "gestion", "Haute", "Immédiat (≤ 3 mois)", 4, "Absence de pilotage mensuel")
    if "Marge insuffisante / prix de revient non maîtrisé" in fb_texts:
        add("Étude prix de revient & politique de pricing", "eco_strat", "Haute", "Immédiat (≤ 3 mois)", 5, "Marge insuffisante")
    if "Trésorerie tendue / pas de prévisionnel" in fb_texts:
        add("Prévisionnel & cash management", "gestion", "Haute", "Immédiat (≤ 3 mois)", 5, "Tension de trésorerie")

    if "Exposition réglementaire environnementale élevée" in m_texts or p.rse_sensible:
        add("Diagnostic RSE & plan d'actions", "rse", "Moyenne", "6-12 mois", 3, "Enjeux RSE / environnementaux")
    if "Dépendance à un client majeur" in m_texts:
        add("Plan de diversification commerciale", "eco_strat", "Moyenne", "6-12 mois", 4, "Risque de dépendance client")
    if "Complexité BTP (retenues, situations, DGD)" in m_texts:
        add("Mise en place suivi chantiers / DGD", "btp", "Moyenne", "6-12 mois", 3, "Spécificités BTP")
    if "TVA plateformes / marketplace (OSS/IOSS)" in m_texts:
        add("Revue TVA (OSS/IOSS) & procédures", "international", "Haute", "Immédiat (≤ 3 mois)", 4, "Risque TVA marketplaces")

    # Opportunités
    if any("Préparer la transmission / retraite dirigeant" in x["texte"] for x in swot.get("Opportunités", [])):
        add("Bilan retraite & pré-étude de transmission", "patrimonial", "Moyenne", "6-12 mois", 3, "Fenêtre d'opportunité transmission")
    if any("Optimisation patrimoniale" in x["texte"] for x in swot.get("Opportunités", [])):
        add("Bilan patrimonial dirigeant", "patrimonial", "Moyenne", "6-12 mois", 3, "Patrimoine dirigeant important")
    if any("Développement export" in x["texte"] for x in swot.get("Opportunités", [])):
        add("Diagnostic international (TVA / flux / implantations)", "international", "Moyenne", "6-12 mois", 3, "Opportunité export")
    if any("Valorisation via la démarche RSE" in x["texte"] for x in swot.get("Opportunités", [])):
        add("Reporting extra-financier simplifié", "rse", "Basse", "> 12 mois", 2, "Créer de la valeur via RSE")

    # Social / RH (induit par taille/obligations)
    if p.taille in ("11-49", "50-249", "250+"):
        if not p.presence_cadres:
            add("Audit social & mise en conformité (CSE, DUERP...)", "social", "Haute", "Immédiat (≤ 3 mois)", 4, "Obligations sociales renforcées")
        else:
            add("Optimisation processus paie/RH", "social", "Moyenne", "6-12 mois", 3, "Effectif significatif")

    # Fiscal — détection via ecommerce/international
    if p.ecommerce_plateformes or p.exposition_internationale in ("Occasionnelle", "Régulière/Structurée"):
        add("Revue fiscale ciblée (TVA, prix de transfert simplifiés)", "fiscal", "Moyenne", "6-12 mois", 3, "Flux e-commerce/internationaux")

    # Gestion — si nb de banques > 1, reporting absent ou trésorerie tendue
    if (p.nb_banques > 1 and not p.reporting_mensuel) or p.tresorerie_tendue:
        add("Centralisation banques & rapprochements automatiques", "digital", "Moyenne", "6-12 mois", 3, "Multiples banques sans process outillé")

    # Éco/Stratégie — croissance, marge, dépendance
    if p.croissance in ("En baisse", "Stable") and p.marge != "Confortable":
        add("Diagnostic stratégique (marché/offre/organisation)", "eco_strat", "Moyenne", "6-12 mois", 4, "Performance perfectible")

    # Déduplication & consolidation
    unique = []
    seen = set()
    for n in needs:
        key = (n.besoin, n.service)
        if key not in seen:
            unique.append(n)
            seen.add(key)
    return unique

def needs_to_dataframe(needs: List[Need]) -> pd.DataFrame:
    data = [asdict(n) for n in needs]
    df = pd.DataFrame(data)
    if not df.empty:
        df["Envoyer ?"] = True
    else:
        df = pd.DataFrame(columns=["besoin","service","priorite","echeance","impact","justification","Envoyer ?"])
    return df

def make_email(service_email: str, client_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
    subject = f"[DIAG] {client_name} — {row['besoin']} ({row['priorite']}, {row['echeance']})"
    body_lines = [
        f"Service concerné : {row['service']}",
        f"Client : {client_name}",
        f"Besoin : {row['besoin']}",
        f"Priorité : {row['priorite']} | Échéance : {row['echeance']} | Impact : {row['impact']}/5",
        f"Justification : {row['justification']}",
        "",
        "Merci de revenir vers le chargé de dossier pour planifier la prise en charge."
    ]
    body = "\n".join(body_lines)
    # .eml minimal (brouillon local)
    eml = textwrap.dedent(f"""\
    From: diagnostic@cabinet.com
    To: {service_email}
    Subject: {subject}
    MIME-Version: 1.0
    Content-Type: text/plain; charset=UTF-8

    {body}
    """)
    return {"to": service_email, "subject": subject, "body": body, "eml": eml}

def zip_emails(emails: List[Dict[str, Any]], client_name: str) -> bytes:
    import zipfile
    tmp = BytesIO()
    with zipfile.ZipFile(tmp, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, em in enumerate(emails, start=1):
            filename = f"{i:02d}_{client_name.replace(' ','_')}.eml"
            zf.writestr(filename, em["eml"])
    tmp.seek(0)
    return tmp.read()

# =====================================
# UI — Paramètres & profil
# =====================================

st.title("🧭 Diagnostic orienté besoins — Cabinet d'expertise comptable")
st.caption("Structure SWOT adaptée → détection de besoins → rattachement services → génération d'événements.")

with st.sidebar:
    st.header("📂 Dossier client")
    nom = st.text_input("Nom du client / dossier", "Client DEMO")
    secteur = st.selectbox("Secteur", SECTEURS, index=2)
    taille = st.selectbox("Taille", TAILLE, index=1)
    digital = st.selectbox("Maturité digitale", DIGITAL, index=1)
    impact_env = st.selectbox("Impact environnemental", IMPACT_ENV, index=0)
    rse_sensible = st.toggle("Sensible RSE", value=False)
    presence_cadres = st.toggle("Présence de cadres / RH structuré", value=False)
    exposition_internationale = st.selectbox("Exposition internationale", EXPO_INTERNATIONAL, index=0)
    dependance_client = st.selectbox("Dépendance à un client", DEPENDANCE_CLIENT, index=0)
    croissance = st.selectbox("Tendance d'activité", ["En baisse","Stable","En croissance"], index=1)
    marge = st.selectbox("Niveau de marge", ["Faible","Correcte","Confortable"], index=1)
    tresorerie_tendue = st.toggle("Trésorerie tendue", value=False)
    reporting_mensuel = st.toggle("Reporting mensuel en place", value=False)
    nb_banques = st.number_input("Nombre de banques actives", min_value=0, max_value=20, value=1, step=1)
    proche_retraite = st.selectbox("Horizon retraite dirigeant", HORIZON_RETRAITE, index=0)
    succession_envisagee = st.toggle("Projet de succession / transmission", value=False)
    patrimoine_dirigeant_important = st.toggle("Patrimoine dirigeant important", value=False)
    btp_specifique = st.toggle("Spécificités BTP", value=(secteur=="BTP"))
    ecommerce_plateformes = st.toggle("E-commerce via plateformes", value=False)
    risques_juridiques = st.toggle("Risques juridiques/litiges", value=False)
    notes = st.text_area("Notes libres", "")

    st.markdown("---")
    st.subheader("📧 Routage des services")
    recipients = {}
    for k, label in SERVICES.items():
        recipients[k] = st.text_input(f"Email — {label}", value=DEFAULT_RECIPIENTS[k])

profile = ClientProfile(
    nom=nom,
    secteur=secteur,
    taille=taille,
    digital=digital,
    impact_env=impact_env,
    rse_sensible=rse_sensible,
    presence_cadres=presence_cadres,
    exposition_internationale=exposition_internationale,
    dependance_client=dependance_client,
    croissance=croissance,
    marge=marge,
    tresorerie_tendue=tresorerie_tendue,
    reporting_mensuel=reporting_mensuel,
    nb_banques=int(nb_banques),
    proche_retraite=proche_retraite,
    succession_envisagee=succession_envisagee,
    patrimoine_dirigeant_important=patrimoine_dirigeant_important,
    btp_specifique=btp_specifique,
    ecommerce_plateformes=ecommerce_plateformes,
    risques_juridiques=risques_juridiques,
    notes=notes
)

# =====================================
# Diagnostic & besoins
# =====================================

swot = swot_from_profile(profile)

c1, c2 = st.columns(2)
with c1:
    st.subheader("✅ Forces")
    if swot["Forces"]:
        for x in swot["Forces"]:
            st.success(x["texte"])
    else:
        st.info("Aucune force saillante identifiée pour l'instant.")

    st.subheader("🚀 Opportunités")
    if swot["Opportunités"]:
        for x in swot["Opportunités"]:
            st.info(x["texte"])
    else:
        st.caption("Complétez les informations pour faire émerger des opportunités.")

with c2:
    st.subheader("⚠️ Faiblesses")
    if swot["Faiblesses"]:
        for x in swot["Faiblesses"]:
            st.warning(x["texte"])
    else:
        st.caption("Rien de critique détecté à ce stade.")

    st.subheader("⛔ Menaces")
    if swot["Menaces"]:
        for x in swot["Menaces"]:
            st.error(x["texte"])
    else:
        st.caption("Pas de menace majeure détectée.")

st.divider()

st.subheader("🎯 Besoins détectés (éditables)")
needs = detect_needs(profile, swot)
df = needs_to_dataframe(needs)

edited = st.data_editor(
    df,
    use_container_width=True,
    disabled=[],
    column_config={
        "priorite": st.column_config.SelectboxColumn("Priorité", options=PRIORITES, required=True),
        "echeance": st.column_config.SelectboxColumn("Échéance", options=ECHEANCES, required=True),
        "impact": st.column_config.NumberColumn("Impact (1-5)", min_value=1, max_value=5, step=1),
        "Envoyer ?": st.column_config.CheckboxColumn("Envoyer ?", default=True)
    },
    num_rows="fixed"
)

st.markdown("**Astuce :** ajustez priorités/échéances avant de générer les événements.")

st.divider()

colA, colB, colC = st.columns([1,1,1])

with colA:
    st.subheader("📤 Export besoins")
    csv_buf = StringIO()
    edited.to_csv(csv_buf, index=False)
    st.download_button("Télécharger CSV des besoins", data=csv_buf.getvalue(), file_name=f"besoins_{profile.nom.replace(' ','_')}.csv", mime="text/csv")

with colB:
    st.subheader("🧾 Synthèse Markdown")
    md_lines = [f"# Diagnostic & besoins — {profile.nom}", "", f"_Date : {datetime.date.today().isoformat()}_", ""]
    md_lines.append("## SWOT (orienté besoins)")
    for bloc in ("Forces","Faiblesses","Opportunités","Menaces"):
        md_lines.append(f"### {bloc}")
        if swot[bloc]:
            for x in swot[bloc]:
                md_lines.append(f"- {x['texte']}")
        else:
            md_lines.append("- (néant)")
        md_lines.append("")
    md_lines.append("## Besoins & rattachement services")
    if not edited.empty:
        for _, row in edited.iterrows():
            md_lines.append(f"- **{row['besoin']}** → _{row['service']}_ — **{row['priorite']}**, {row['echeance']} (impact {row['impact']}/5)")
            md_lines.append(f"  - Justification : {row['justification']}")
    else:
        md_lines.append("- (aucun)")
    md = "\n".join(md_lines)
    st.download_button("Télécharger la synthèse (.md)", data=md, file_name=f"diagnostic_{profile.nom.replace(' ','_')}.md", mime="text/markdown")

with colC:
    st.subheader("✉️ Générer les e-mails")
    to_send = edited[edited["Envoyer ?"] == True] if not edited.empty else edited
    if to_send.empty:
        st.caption("Cochez au moins un besoin à envoyer.")
    else:
        emails: List[Dict[str, Any]] = []
        for _, row in to_send.iterrows():
            # retrouver la clé service inverse pour email routing
            svc_email = None
            for key, label in SERVICES.items():
                if label == row["service"]:
                    svc_email = recipients.get(key, DEFAULT_RECIPIENTS[key])
                    break
            if not svc_email:
                svc_email = "info@cabinet.com"
            em = make_email(svc_email, profile.nom, row.to_dict())
            emails.append(em)

        # ZIP .eml
        zip_bytes = zip_emails(emails, profile.nom)
        st.download_button("Télécharger .zip des brouillons d'e-mails (.eml)", data=zip_bytes, file_name=f"emails_{profile.nom.replace(' ','_')}.zip", mime="application/zip")

        # Aperçu du dernier email
        with st.expander("Aperçu d'un e-mail (dernier généré)"):
            st.code(emails[-1]["eml"], language="eml")

st.divider()
with st.expander("📚 Cartographie offres internes (référence)"):
    st.write("Ci-dessous, les offres indicatives par service pour orienter la réponse :")
    for key, label in SERVICES.items():
        st.markdown(f"**{label}**")
        st.write(", ".join(OFFRES[key]))
        st.markdown("---")

st.caption("💡 Cet outil est centré sur le diagnostic. Les prix, si souhaités, peuvent être gérés ailleurs. Ajoutez vos règles métier et modèles d'e-mails propres au cabinet.")
