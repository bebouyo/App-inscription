import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import re
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Fonction pour générer un identifiant unique
def generate_unique_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))

# Fonction pour générer une date d'expiration (24h)
def generate_expiry_date():
    return datetime.now() + timedelta(hours=24)

# Fonction pour vérifier la validité de l'email
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# Fonction pour vérifier la validité du numéro de contact
def is_valid_contact(contact):
    return re.match(r"^\d{8}$", contact) is not None

# Fonction pour charger les données depuis le fichier CSV
def load_data():
    if os.path.exists("database.csv"):
        try:
            return pd.read_csv("database.csv").to_dict(orient="records")
        except Exception as e:
            st.error(f"Erreur de chargement des données: {e}")
            return []
    return []

# Fonction pour sauvegarder les données dans le fichier CSV
def save_data(database):
    df = pd.DataFrame(database)
    try:
        df.to_csv("database.csv", index=False)
    except Exception as e:
        st.error(f"Erreur de sauvegarde des données: {e}")

# Fonction pour envoyer un email
def send_email(to_email, unique_id):
    from_email = "Aesissp@gmail.com"
    from_password = "ruoq dpla fuxx zzxp"
    
    # Configuration du message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Votre identifiant unique pour la sortie de Banfora"
    
    body = f"Merci pour votre inscription. Votre identifiant unique est : {unique_id}. Cet identifiant expirera dans 24 heures si le paiement n'est pas effectué."
    msg.attach(MIMEText(body, 'plain'))
    
    # Connexion au serveur SMTP
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'email : {e}")
        return False

# Initialisation de la base de données (chargée depuis le fichier CSV)
if "database" not in st.session_state:
    st.session_state.database = load_data()
    st.session_state.max_tickets = 50

database = st.session_state.database
max_tickets = st.session_state.max_tickets

# Mise à jour du nombre de tickets disponibles
tickets_restants = max_tickets - len(database)

# CSS personnalisé
st.markdown("""
    <style>
    body {
        background-color: #cce7ff;
    }
    .stButton>button {
        background-color: #007bff;
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .stAlert {
        border-radius: 4px;
        padding: 15px;
    }
    h1 {
        color: #0056b3;
    }
    .current-time, .current-date {
        font-weight: bold;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# Layout pour les titres
st.sidebar.title("Amicale des Élèves statisticiens")
st.markdown("<h1 style='text-align: center;'>Inscription pour la sortie de Banfora</h1>", unsafe_allow_html=True)
st.markdown("<div style='width:100%; text-align:center;'><strong>Veuillez remplir attentivement les champs et garder à l'esprit que l'identifiant généré est unique et s'expirera après 24 h si vous n'effectuez pas le paiement.</strong></div>", unsafe_allow_html=True)

# Afficher la date et l'heure actuelle
current_time = datetime.now().strftime("%H:%M:%S")
current_date = datetime.now().strftime("%Y-%m-%d")
st.markdown(f"<div class='current-time'>Heure actuelle : {current_time}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='current-date'>Date actuelle : {current_date}</div>", unsafe_allow_html=True)

st.markdown(f"<strong>Il reste {tickets_restants} tickets disponibles</strong>", unsafe_allow_html=True)

if tickets_restants > 0:
    with st.form("Inscription"):
        nom_prenom = st.text_input("Nom et prénom")
        sexe = st.selectbox("Sexe", ["Masculin", "Féminin"])
        filiere_niveau = st.selectbox("Filiere/Niveau", ["LPAS1", "LPAS2", "LPAS3", "MPSE1", "MPSE2", "MPSE3", "LSS", "DEMO"])
        contact_personnel = st.text_input("Contact personnel")
        contact_a_prevenir = st.text_input("Contact à prévenir")
        email = st.text_input("Email")
        submit_button = st.form_submit_button("S'inscrire")
        
        if submit_button:
            if nom_prenom and sexe and filiere_niveau and contact_personnel and contact_a_prevenir and email:
                if is_valid_email(email):
                    if is_valid_contact(contact_personnel) and is_valid_contact(contact_a_prevenir):
                        already_registered_today = any(client["Email"] == email and client["Date d'inscription"][:10] == datetime.now().strftime("%Y-%m-%d") for client in database)
                        if not already_registered_today:
                            unique_id = generate_unique_id()
                            expiry_date = generate_expiry_date()
                            client_info = {
                                "Nom et prénom": nom_prenom,
                                "Sexe": sexe,
                                "Filière/Niveau": filiere_niveau,
                                "Contact personnel": contact_personnel,
                                "Contact à prévenir": contact_a_prevenir,
                                "Email": email,
                                "Identifiant unique": unique_id,
                                "Date d'expiration": expiry_date,
                                "Statut de paiement": "Non payé",
                                "Date d'inscription": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                            }
                            database.append(client_info)
                            save_data(database)
                            email_sent = send_email(email, unique_id)
                            if email_sent:
                                st.success(f"Inscription réussie ! Votre identifiant d'inscription unique a été envoyé à votre adresse mail {email}.")
                            else:
                                st.error("L'inscription a réussi, mais l'envoi de l'email a échoué.")
                        else:
                            st.warning("Vous avez déjà effectué une inscription aujourd'hui.")
                    else:
                        st.warning("Veuillez entrer des numéros de contact valides (8 chiffres).")
                else:
                    st.warning("Veuillez entrer une adresse email valide.")
            else:
                st.warning("Veuillez remplir tous les champs du formulaire.")
else:
    st.warning("Les inscriptions sont actuellement fermées.")

