from string import ascii_lowercase
from telnetlib import SEND_URL
import subprocess
import smtplib
import logging
from email.mime.text import MIMEText
from database import session
from modeldb import Task, MediaStatus, Usuario
from dotenv import load_dotenv
from utils import get_from_env
from google.cloud import storage 
from concurrent import futures
import os
from os import getenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from python_http_client.exceptions import HTTPError
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber import exceptions as sub_exceptions


def set_env():
    load_dotenv()
    global UPLOAD_FOLDER
    UPLOAD_FOLDER = getenv("UPLOAD_FOLDER")
    global CONVERTED_FOLDER
    CONVERTED_FOLDER = getenv("CONVERTED_FOLDER")
    global CELERY_BROKER_URL
    CELERY_BROKER_URL = getenv("CELERY_BROKER_URL")
    global SEND_EMAIL
    SEND_EMAIL = getenv("SEND_EMAIL")
    global BUCKET_NAME 
    BUCKET_NAME = getenv("GCP_BUCKET_NAME")
    global GCP_UPLOADED_FOLDER
    GCP_UPLOADED_FOLDER = getenv("GCP_FOLDER_UPLOADED")
    global GCP_CONVERTED_FOLDER
    GCP_CONVERTED_FOLDER = getenv("GCP_FOLDER_CONVERTED")
    global EMAIL_API_KEY
    EMAIL_API_KEY = getenv("EMAIL_API_KEY")
    global RUN_AS_SUSCRIBER
    RUN_AS_SUSCRIBER = getenv("RUN_AS_SUSCRIBER")

set_env()
LOG_FILENAME = 'subscriber.log'
logging.basicConfig(filename=LOG_FILENAME, format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
logging.info("Recibido")
logging.debug('Recibido3')
timeout = 10.0


storage_client = storage.Client()

bucket = storage_client.get_bucket(BUCKET_NAME)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'cloud-miso-8.json'
project_id = "cloud-miso"
subscription_id = "worker-subscription"
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)


def callback(message):
    procesar_audio(message)
    message.ack()

if RUN_AS_SUSCRIBER == "True":
    logging.debug("Condicional_suscriber")
    future = subscriber.subscribe(subscription_path, callback=callback)
    with subscriber:
        try:
            future.result()
        except futures.TimeoutError:
            future.cancel()  # Trigger the shutdown.
            future.result()  # Block until the shutdown is complete.
    # suscribe_to_new_msj()
else: 
    logging.debug("Condicional_suscriber_false")

def upload_to_bucket(file_path):
    try:
        blob = bucket.blob(GCP_CONVERTED_FOLDER + file_path)
        blob.upload_from_filename(CONVERTED_FOLDER + file_path)
        return True
    except Exception as e: 
        print(e)
        return False

def download_file_from_bucket(file_path):
    try:
        blob = bucket.blob(GCP_UPLOADED_FOLDER + file_path)
        blob.download_to_filename(UPLOAD_FOLDER + file_path)
        print('Blob {} downloaded to {}.'.format(file_path, UPLOAD_FOLDER + file_path))
        return True
    except Exception as e: 
        print(e)
        return False

def notify_authors(converted_audios):
    
    for audio in converted_audios:
        usuario = session.query(Usuario).filter_by(id = audio.user_id).first()
        author_email = usuario.email
        msg_text = f"Usuario {author_email}:\n Queremos avisarle que su audio {audio.target_path} ya ha sido convertido."
        email_data = {
                    'subject': 'Aviso de conversión de audio',
                    'to' : f"{author_email}",
                    'body': msg_text
                    }
        try:
            resemail = email(email_data)
            print(resemail)
        except Exception as e:
            print(f"Unable to send notification to '{author_email}': {e}")
    

def send_email(email_data):
    print("Sending email to %s" % email_data['to'])
    sender = "Private Person <from@smtp.mailtrap.io>"
    receiver = email_data["to"]

    message = MIMEText(email_data["body"])
    message["Subject"] = email_data["subject"]
    message["From"] = sender
    message["To"] =  receiver

    with smtplib.SMTP(get_from_env("SMTP_SERVER"), get_from_env("SMTP_PORT")) as server:
        server.login(get_from_env("SMTP_USERNAME"), get_from_env("SMTP_PASSWORD"))
        server.sendmail(sender, receiver,   message.as_string())

def email(email_data):
    sg = SendGridAPIClient(EMAIL_API_KEY)

    html_content = "<p>"+ email_data["body"] + "</p>"

    message = Mail(
        to_emails= email_data["to"],
        from_email=Email('ls.campo10@uniandes.edu.co', "CloudTeam8"),
        subject=email_data["subject"],
        html_content=html_content
        )
    message.add_bcc("ls.campo10@uniandes.edu.co")

    try:
        response = sg.send(message)
        return f"email.status_code={response.status_code}"
        #expected 202 Accepted

    except HTTPError as e:
        return e.message

def convert_files(audios_to_process):
    converted_audios = []
    for audio in audios_to_process:
        print("Processing audio task id %s" % audio.source_path)
        source_path = UPLOAD_FOLDER + '/'+ audio.source_path
        target_path = CONVERTED_FOLDER + '/'+ audio.target_path
        download_file_from_bucket('/'+ audio.source_path)
        print("downloading file  %s" % audio.source_path)
        try:
            result = subprocess.run(["/usr/bin/ffmpeg", "-y", "-i", source_path, target_path])
            if result.returncode == 0:
                upload_to_bucket('/'+ audio.target_path)
                os.remove(target_path)
                converted_audios.append(audio)
                print("Audio proccesed task target path %s" % audio.target_path)
            os.remove(source_path)    
        except Exception as e:
            print("Error al convertir el archivo: %s", e)
    return list(converted_audios)
    
def mark_converted(converted_audios):
    if len(converted_audios) == 0:
        print("Ninguna voz fue convertida en esta iteración.")
        return 0
    converted_files_ids = tuple(map(lambda audio: audio.id, converted_audios))
    print("Marcando archivos convertidos: %s" % str(converted_files_ids))
    rowcount = session.query(Task).filter(Task.id.in_(converted_files_ids)).\
                update({"status": MediaStatus.processed})
    session.commit()
    
    return rowcount


class Audio:
    def __init__(self, id, source_path, target_path, target_format, user_id):
        self.id = id
        self.source_path = source_path
        self.target_path = target_path
        self.target_format = target_format
        self.user_id = user_id


def procesar_audio(message):
    try:
        print("Iniciando proceso de conversión de audio...")
        logging.info("Iniciando proceso de conversión de audio...")
        if message.attributes:
            audios_to_process= [Audio(  id=message.attributes['id'],
                source_path=message.attributes['source_path'], 
                        target_path=message.attributes['target_path'], 
                        user_id=message.attributes ['user_id'], 
                        target_format=message.attributes['target_format'])]    
            converted_audios = convert_files(audios_to_process)
            number_audios_updated = mark_converted(converted_audios)
            if number_audios_updated > 0:
                if SEND_EMAIL == "True":
                    notify_authors(converted_audios)
                    print("Notify authors")
                else:
                    print("Not sending emails")
        logging.info("Finalizando proceso de conversión de audio...")
        logging.info("Tiempo empleado para la conversión de audio...")
        return "DONE with SUCCESS"
    except Exception as e:
        logging.info(f"Ocurrió un error durante la ejecución de la tarea: {str(e)}")
        return "DONE with ERRORS"




''' --------------------------- -------------------- ------------------------'''




project_id = "cloud-miso"
subscription_id = "worker-subscription"
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)


def callback(message):
    procesar_audio(message)
    ack_future = message.ack_with_response()
    try:
        # Block on result of acknowledge call.
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        ack_future.result()
        logging.info(f"Ack for message {message.message_id} successful.")
    except sub_exceptions.AcknowledgeError as e:
        logging.info(
            f"Ack for message {message.message_id} failed with error: {e.error_code}"
        )

# Limit the subscriber to only have ten outstanding messages at a time.
flow_control = pubsub_v1.types.FlowControl(max_messages=10)
streaming_pull_future = subscriber.subscribe(
    subscription_path, callback=callback, flow_control=flow_control, 
)

logging.debug("Condicional_suscriber")

with subscriber:
    try:
        streaming_pull_future.result()
    except futures.TimeoutError:
        streaming_pull_future.cancel()  # Trigger the shutdown.
        streaming_pull_future.result()  # Block until the shutdown is complete.
# suscribe_to_new_msj()
