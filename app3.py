import streamlit as st
import pandas as pd
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import qrcode
from fpdf import FPDF
import os
import re
import tempfile

# Fonction pour générer un identifiant unique
def generate_unique_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=5))

# Fonction pour générer une date d'expiration (24h)
def generate_expiry_date():
    return datetime.now() + timedelta(hours=24)

# Fonction pour vérifier la validité de l'email
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

# Fonction pour envoyer un email avec PDF en pièce jointe
def send_email(recipient_email, subject, body, pdf_content):
    sender_email = "bebouyo@gmail.com"
    sender_password =  "noij iynb osmy bzml"
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    part = MIMEApplication(pdf_content, Name="inscription.pdf")
    part["Content-Disposition"] = 'attachment; filename="inscription.pdf"'
    msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

class PDF(FPDF):
    def header(self):
        # Dessiner un rectangle bleu autour des bords du PDF
        self.set_draw_color(0, 0, 255)  # Bleu
        self.set_line_width(1)
        self.rect(5, 5, self.w - 10, self.h - 10)  # Rectangle bleu plus épais

# Fonction pour générer un PDF avec QR code
def generate_pdf_and_qr(client_info):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", size=16, style='B')
    pdf.cell(200, 10, txt="Ticket Sortie Détente à Banfora", ln=True, align="C")
    pdf.set_font("Arial", size=12, style='B')
    pdf.cell(200, 10, txt=f"Nom et prénom : {client_info['Nom et prénom']}", ln=True)
    pdf.cell(200, 10, txt=f"Sexe : {client_info['Sexe']}", ln=True)
    pdf.cell(200, 10, txt=f"Filière/Niveau : {client_info['Filière/Niveau']}", ln=True)
    pdf.cell(200, 10, txt=f"Contact personnel : {client_info['Contact personnel']}", ln=True)
    pdf.cell(200, 10, txt=f"Contact à prévenir : {client_info['Contact à prévenir']}", ln=True)
    pdf.cell(200, 10, txt=f"Email : {client_info['Email']}", ln=True)
    pdf.cell(200, 10, txt=f"Identifiant unique : {client_info['Identifiant unique']}", ln=True)
    pdf.cell(200, 10, txt=f"Prix du ticket : 5000 FCFA", ln=True)

    pdf.set_text_color(150, 150, 150)  # Gris foncé
    pdf.set_font("Arial", size=50)
    pdf.text(60, 270, "Sortie Banfora")

    qr = qrcode.make(client_info["Identifiant unique"])
    qr_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    qr.save(qr_path)
    pdf.image(qr_path, x=10, y=130, w=50, h=50)  # Positionné plus bas
    temp_pdf_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    temp_pdf_file.close()
    pdf.output(temp_pdf_file.name)
    
    with open(temp_pdf_file.name, 'rb') as file:
        pdf_content = file.read()

    # Clean up temporary files
    os.remove(qr_path)
    os.remove(temp_pdf_file.name)

    return pdf_content

# Fonction pour vérifier les identifiants expirés et les supprimer
def check_expired_ids(database):
    current_time = datetime.now()
    for client in database[:]:
        expiry_date_str = client["Date d'expiration"]
        if isinstance(expiry_date_str, datetime):
            expiry_date = expiry_date_str
        else:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S.%f")
        if expiry_date <= current_time and client["Statut de paiement"] == "Non payé":
            database.remove(client)


# Fonction pour charger les données depuis le fichier CSV
def load_data():
    if os.path.exists("database.csv"):
        return pd.read_csv("database.csv").to_dict(orient="records")
    return []

# Fonction pour sauvegarder les données dans le fichier CSV
def save_data(database):
    df = pd.DataFrame(database)
    df.to_csv("database.csv", index=False)

# Initialisation de la base de données (chargée depuis le fichier CSV)
if "database" not in st.session_state:
    st.session_state.database = load_data()
    st.session_state.max_tickets = 50
    st.session_state.admin_password = "7968"

database = st.session_state.database
max_tickets = st.session_state.max_tickets
admin_password = st.session_state.admin_password

# Vérification et suppression des identifiants expirés
check_expired_ids(database)
save_data(database)

# Mise à jour du nombre de tickets disponibles
tickets_restants = max_tickets - len(database)

# Layout for the titles
st.sidebar.title("Amicale des Élèves statisticiens")
st.markdown("<h1 style='text-align: center;'>Inscription pour la sortie de Banfora</h1>", unsafe_allow_html=True)
st.markdown("<div style='width:800px'><strong>Veuillez remplir attentivement les champs et garder à l'esprit que l'identifiant généré est unique et s'expirera après 24 h si vous n'effectuez pas le paiement</strong></div>", unsafe_allow_html=True)

# Espace administrateur
if st.sidebar.text_input("Mot de passe administrateur", type="password") == admin_password:
    st.sidebar.subheader("Espace administrateur")
    
    # Affichage d'un aperçu des clients inscrits
    st.sidebar.subheader("Aperçu des clients inscrits")
    if len(database) > 0:
        df = pd.DataFrame(database)
        st.sidebar.dataframe(df[['Nom et prénom', 'Email', 'Statut de paiement']])
    else:
        st.sidebar.write("Aucun client inscrit pour le moment.")

    # Recherche par identifiant unique
    admin_id = st.sidebar.text_input("Rechercher par identifiant unique")

    # Vérification de l'identifiant unique
    if admin_id:
        client_info = next((client for client in database if client["Identifiant unique"] == admin_id), None)
        if client_info:
            st.write("Informations du client :")
            st.write(client_info)
            new_payment_status = st.selectbox("Statut de paiement", ["Non payé", "Payé"], index=1 if client_info["Statut de paiement"] == "Payé" else 0)
            
            if st.button("Mettre à jour le statut de paiement"):
                client_info["Statut de paiement"] = new_payment_status
                if new_payment_status == "Payé":
                    pdf_content = generate_pdf_and_qr(client_info)
                    send_email(client_info["Email"], "Confirmation de paiement", f"Bonjour {'Mr' if client_info['Sexe'] == 'Masculin' else 'Mme'} {client_info['Nom et prénom']}, veuillez recevoir votre ticket pour la sortie de l'amicale à Banfora prévue du 28 au 31 Mai.", pdf_content)
                    st.success("Statut de paiement mis à jour et email envoyé avec succès !")
                else:
                    st.success("Statut de paiement mis à jour !")
                save_data(database)
        else:
            st.warning("Aucun client trouvé avec cet identifiant unique.")

    if st.sidebar.button("Télécharger la base de données"): 
        df = pd.DataFrame(database) 
        csv = df.to_csv(index=False) 
        st.sidebar.download_button(label="Télécharger la base de données", data=csv, file_name='base_donnees_clients.csv', mime='text/csv')

# Formulaire d'inscription
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
                    if re.match(r"^\d{8}$", contact_personnel) and re.match(r"^\d{8}$", contact_a_prevenir):
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
                            st.success("Inscription réussie ! Votre identifiant unique est : " + unique_id)
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

# Vérification de l'expiration des identifiants non payés et suppression si nécessaire
check_expired_ids(database)
save_data(database)

