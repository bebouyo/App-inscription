import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import qrcode
from fpdf import FPDF
import tempfile

# Fonction pour charger les données depuis le fichier CSV
def load_data():
    if os.path.exists("database.csv"):
        return pd.read_csv("database.csv").to_dict(orient="records")
    return []

# Fonction pour sauvegarder les données dans le fichier CSV
def save_data(database):
    df = pd.DataFrame(database)
    df.to_csv("database.csv", index=False,encoding='utf-8')

# Classe PDF pour personnaliser le PDF
class PDF(FPDF):
    def header(self):
        # Dessiner un rectangle bleu autour des bords du PDF
        self.set_draw_color(0, 0, 255)  # Bleu
        self.set_line_width(1)
        self.rect(5, 5, self.w - 10, self.h - 10)  # Rectangle bleu plus épais


# Fonction pour générer un PDF avec QR code
def generate_pdf_and_qr(client_info, admin_name, validation_time):
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
    pdf.cell(200, 10, txt=f"Validé par : {admin_name}", ln=True)
    pdf.cell(200, 10, txt=f"Heure de validation : {validation_time}", ln=True)
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

    return pdf_content, qr_path

# Fonction pour envoyer un email avec PDF et un autre fichier en pièces jointes
def send_email(recipient_email, subject, body, pdf_content, attachment_path):
    sender_email = "Aesissp@gmail.com"
    sender_password = "ruoq dpla fuxx zzxp"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # Joindre le PDF
    part = MIMEApplication(pdf_content, Name="inscription.pdf")
    part["Content-Disposition"] = 'attachment; filename="inscription.pdf"'
    msg.attach(part)

    # Joindre le second fichier sans le lire complètement
    try:
        with open(attachment_path, "rb") as file:
            attachment_part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
            attachment_part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(attachment_part)
    except FileNotFoundError:
        print(f"Erreur : Le fichier {attachment_path} est introuvable.")
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {attachment_path} : {str(e)}")

    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

# Initialisation de la base de données (chargée depuis le fichier CSV)
if "database" not in st.session_state:
    st.session_state.database = load_data()

# Dictionnaire des administrateurs avec leurs mots de passe
admin_accounts = {
    "Carine": "yaro@lss",
    "Ousmane": "ouattara@",
    "Bebou": "bebou@79",
    "Kientega": "abdoumpse",
    "ephraim": "ephralpas1"
}
database = st.session_state.database

# Formulaire de connexion administrateur
st.sidebar.title("Espace administrateur")
username = st.sidebar.text_input("Nom d'utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")

if st.sidebar.button("Se connecter"):
    if username in admin_accounts and admin_accounts[username] == password:
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.sidebar.error("Nom d'utilisateur ou mot de passe incorrect")

if st.session_state.get("logged_in"):
    st.sidebar.success(f"Connecté en tant que {st.session_state.username}")
    
    st.subheader("Aperçu des participants inscrits")
    if len(database) > 0:
        df = pd.DataFrame(database)
        if 'Modifié par' not in df.columns:  # Vérifier si le champ 'Modifié par' existe dans le DataFrame
            df['Modifié par'] = ''  # Ajouter le champ 'Modifié par' s'il n'existe pas
        st.dataframe(df[['Nom et prénom', 'Email', 'Statut de paiement', 'Modifié par']])
    else:
        st.write("Aucun client inscrit pour le moment.")

    admin_id = st.text_input("Rechercher par identifiant unique")

    if admin_id:
        client_info = next((client for client in database if client["Identifiant unique"] == admin_id), None)
        if client_info:
            st.write("Informations du client :")
            st.write(client_info)
            new_payment_status = st.selectbox("Statut de paiement", ["Non payé", "Payé"], index=1 if client_info["Statut de paiement"] == "Payé" else 0)
            
            if st.button("Mettre à jour le statut de paiement"):
                client_info["Statut de paiement"] = new_payment_status
                client_info["Modifié par"] = st.session_state.username  # Ajout de l'administrateur qui a modifié
                if new_payment_status == "Payé":
                    validation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Obtenir l'heure de validation
                    admin_name = st.session_state.username
                    pdf_content, qr_path = generate_pdf_and_qr(client_info, admin_name, validation_time)  # Fournir les arguments requis
                    attachment_path = os.path.join(os.path.dirname(__file__), "reglement_interieur.docx")
                    send_email(client_info["Email"], "Confirmation de paiement", f"Bonjour {'Mr' if client_info['Sexe'] == 'Masculin' else 'Mme'} {client_info['Nom et prénom']}, veuillez recevoir votre ticket pour la sortie de l'amicale à Banfora prévue du 28 au 31 Mai.", pdf_content, attachment_path)
                    st.success("Statut de paiement mis à jour et email envoyé avec succès !")
                else:
                    st.success("Statut de paiement mis à jour !")
                save_data(database)
        else:
            st.warning("Aucun client trouvé avec cet identifiant unique.")

    if st.button("Télécharger la base de données"):
        df = pd.DataFrame(database)
        # Créer un fichier Excel temporaire
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        excel_writer = temp_file.name
        
        # Écrire les données DataFrame dans le fichier Excel temporaire
        df.to_excel(excel_writer, index=False, engine='openpyxl')
    
    # Lire le contenu du fichier Excel temporaire en mode binaire
    with open(excel_writer, 'rb') as file:
        excel_bytes = file.read()
    st.download_button(label="Télécharger la base de données", data=excel_bytes, file_name='base_donnees_clients.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
else:
    st.warning("Veuillez vous connecter en tant qu'administrateur.")

