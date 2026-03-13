import base64
import unicodedata
import pandas as pd
import streamlit as st
import base64

# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================
df = pd.read_csv("transfers_clean.csv", encoding="utf-8",sep=";")
df["transfer_date"] = pd.to_datetime(df["transfer_date"], dayfirst=True) # convertit la colonne "transfer_date" en format de date et en spécifiant que le jour est le premier élément de la date (dayfirst=True), ce qui permet de manipuler les dates plus facilement dans le code, par exemple pour trier les transferts par date ou calculer des durées entre les transferts.
df = df.rename(columns={"player_name": "nom_joueur",
                        "from_club_name": "club_depart",
                        "to_club_name": "club_arrivee",
                        "transfer_date": "date_transfert"}) #permet de renommer les colonnes du tableau pour les rendre plus compréhensibles et faciles à utiliser dans le code, en utilisant la méthode rename() et en spécifiant un dictionnaire de correspondance entre les anciens noms de colonnes et les nouveaux noms de colonnes, puis en assignant le résultat à df pour mettre à jour le tableau avec les nouveaux noms de colonnes
df = df.dropna(subset=["market_value_in_eur"]) #permet de supprimer les lignes qui contiennent des valeurs manquantes 

# ============================================================
# LOGIQUE DU JEU
# ============================================================
def musique_fond(chemin):
    with open(chemin, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    st.markdown(f"""
    <audio autoplay loop>
        <source src="data:audio/mp3;base64,{data}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)


def get_joueurs_filtres(prix_min):
    compte = df["nom_joueur"].value_counts()
    joueurs_actifs = compte[compte >= 3].index
    valeur_max = df.groupby("nom_joueur")["market_value_in_eur"].max()
    joueurs_chers = valeur_max[valeur_max > prix_min].index # filtre les joueurs avec une valeur maximale supérieure
    df_dup = df[
        df["nom_joueur"].isin(joueurs_actifs) &
        df["nom_joueur"].isin(joueurs_chers) # 
    ]["nom_joueur"].drop_duplicates() # filtre mini 3 clubs et prix minimum + supprime les lignes avec le meme nom de joueur
    return df_dup


def tirer_joueur(prix_min):
    """Tire un joueur aléatoire et ses 3 clubs, stocke dans session_state."""
    joueurs = get_joueurs_filtres(prix_min)
    rdm_player = joueurs.sample(n=1).values[0]
    resultat = df[df["nom_joueur"] == rdm_player][["club_depart", "club_arrivee", "date_transfert"]]
    resultat_alea = resultat.sample(3)
    resultat_tri = resultat_alea.sort_values("date_transfert", ascending=False)

# st.session_state est une mémoire persistante qui survit entre ces réexécutions.

    st.session_state.joueur = rdm_player
    st.session_state.clubs = resultat_tri
    st.session_state.essais = 0
    st.session_state.gagne = False
    st.session_state.perdu = False
    st.session_state.message = ""
    st.session_state.partie_lancee = True

def normaliser(texte):
    # Enlève les accents, met en minuscule, garde seulement les lettres
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte.strip().lower()

# ============================================================
# INITIALISATION SESSION STATE
# ============================================================
# Ces lignes servent à créer les variables avec des valeurs par défaut si elles n'existent pas encore. (Sinon plantage)

if "partie_lancee" not in st.session_state:
    st.session_state.partie_lancee = False
if "essais" not in st.session_state:
    st.session_state.essais = 0
if "gagne" not in st.session_state:
    st.session_state.gagne = False
if "perdu" not in st.session_state:
    st.session_state.perdu = False
if "message" not in st.session_state:
    st.session_state.message = ""

# ============================================================
# INTERFACE
# ============================================================
st.title("⚽ Devine le joueur !")
if st.button("📣 Ferveur des supporters "):
    musique_fond("musique_stade.mp3")
# ── Étape 1 : Paramètre prix ────────────────────────────────
st.markdown("### 🎯 Paramètres")
prix_millions = st.number_input("Valeur de marché minimale (M€)", min_value=0.1, value=10, step=1)
prix = prix_millions * 1_000_000  # reconvertit en euros pour le filtre

if st.button("🎲 Lancer une partie"):
    tirer_joueur(prix)
    st.rerun()

# ── Étape 2 : Jeu ──────────────────────────────────────────
if st.session_state.partie_lancee:
    st.markdown("---")
    st.markdown("### 🏟️ Liste des clubs :")
    clubs = st.session_state.clubs
    for _, row in clubs.iterrows():
        date = row["date_transfert"].strftime("%B %Y")
        st.markdown(f"- **{row['club_depart']}** *({date})*")

    st.markdown("---")

    # Affichage du nombre d'essais restants
    essais_restants = 3 - st.session_state.essais
    st.markdown(f"**Essais restants : {'🟢' * essais_restants}{'🔴' * st.session_state.essais}**")

    # ── Fin de partie ──────────────────────────────────────
    if st.session_state.gagne:
        st.success(f"🏆 Bravo ! C'était bien **{st.session_state.joueur}** !")
        if st.button("🔄 Nouvelle partie"):
            tirer_joueur(prix)
            st.rerun()

    elif st.session_state.perdu:
        st.error(f"😔 Dommage ! Le joueur était **{st.session_state.joueur}**.")
        if st.button("🔄 Nouvelle partie"):
            tirer_joueur(prix)
            st.rerun()

    # ── Saisie réponse ─────────────────────────────────────
    else:
        reponse = st.text_input("✏️ Entrez le nom du joueur :")

        if st.button("Valider"):
            if reponse.strip() == "":
                st.warning("⚠️ Entre un nom avant de valider.")
            else:
                st.session_state.essais += 1
                if normaliser(reponse) in normaliser(st.session_state.joueur):
                    st.session_state.gagne = True
                elif st.session_state.essais >= 3:
                    st.session_state.perdu = True
                else:
                    reste = 3 - st.session_state.essais
                    st.session_state.message = f"❌ Ce n'est pas le bon joueur. Il te reste {reste} essai(s)."
                st.rerun()

        if st.session_state.message:
            st.warning(st.session_state.message)


# ============================================================
# Fond
# ============================================================
st.markdown("""
<style>
    .stApp {
        background-image: url("https://wallpaper.forfun.com/fetch/b5/b5e4a831512adb318af4526e68c70f59.jpeg?w=1470&r=0.5625&f=webp");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
</style>
""", unsafe_allow_html=True)



