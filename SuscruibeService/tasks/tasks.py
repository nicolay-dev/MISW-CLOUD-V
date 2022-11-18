from string import ascii_lowercase
from telnetlib import SEND_URL
from celery import Celery
from celery.utils.log import get_task_logger
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.cloud import storage, pubsub_v1
from concurrent import futures
from os import getenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from python_http_client.exceptions import HTTPError

# from database import session
# from modeldb import Task, MediaStatus
# from utils import get_from_env

import subprocess
import smtplib
import logging
import tasks.database as database
import tasks.modeldb as modeldb
import tasks.utils as utils
import os

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

storage_client = storage.Client()

bucket = storage_client.get_bucket(BUCKET_NAME)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './cloud-miso-8.json'
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
        return True
    except Exception as e: 
        print(e)
        return False

def notify_authors(converted_audios):
    
    for audio in converted_audios:
        author_email = audio.author
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

    with smtplib.SMTP(utils.get_from_env("SMTP_SERVER"), utils.get_from_env("SMTP_PORT")) as server:
        server.login(utils.get_from_env("SMTP_USERNAME"), utils.get_from_env("SMTP_PASSWORD"))
        server.sendmail(sender, receiver,   message.as_string())

def email(email_data):
    sg = SendGridAPIClient(EMAIL_API_KEY)

    html_content = "<p>"+ email_data["body"] + "</p>"

    message = Mail(
        to_emails= email_data["to"],
        from_email=Email('leslysharyncj@gmail.com', "Team-8"),
        subject=email_data["subject"],
        html_content=html_content
        )
    message.add_bcc("leslysharyncj@gmail.com")

    try:
        response = sg.send(message)
        return f"email.status_code={response.status_code}"
        #expected 202 Accepted

    except HTTPError as e:
        return e.message

def convert_files(audios_to_process):
    converted_audios = []
    for audio in audios_to_process:
        print("Processing audio task id %s" % audio.id)
        source_path = UPLOAD_FOLDER + '/'+ audio.source_path
        target_path = CONVERTED_FOLDER + '/'+ audio.target_path
        target_format = audio.target_format
        download_file_from_bucket('/'+ audio.source_path)
        try:
            result = subprocess.run(["/usr/bin/ffmpeg", "-y", "-i", source_path, target_path])
            if result.returncode == 0:
                upload_to_bucket('/'+ audio.target_path)
                os.remove(target_path)
                converted_audios.append(audio)
                print("Audio proccesed task id %s" % audio.id)
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
    rowcount = database.session.query(modeldb.Task).filter(modeldb.Task.id.in_(converted_files_ids)).\
                update({"status": modeldb.MediaStatus.processed})
    database.session.commit()
    
    return rowcount

def mark_rollback(rollback_audios):
    if len(rollback_audios) == 0:
        print("Todos los audios fueron convertidos.")
        return 0
    rollback_files_ids = tuple(map(lambda audio: audio.id, rollback_audios))
    print("Rollback de archivos no convertidos: %s" % str(rollback_files_ids))
    rowcount = database.session.query(modeldb.Task).filter(modeldb.Task.id.in_(rollback_files_ids)).\
                update({"status": modeldb.MediaStatus.uploaded})
    database.session.commit()
    
    return rowcount



#celery = Celery('tasks', broker=CELERY_BROKER_URL)

#celery.conf.beat_schedule = {
#    "Convert-audio-files": {
#        "task": "tasks.procesar_audio",
#        "schedule": 60
#    }
#}

#@celery.task

def procesar_audio(message):
    try:
        
        logging.debug("Received %s", message)
        
        # audios_to_process = database.session.query(modeldb.Task).filter_by(status = modeldb.MediaStatus.uploaded).limit(100).all()
        # if len(audios_to_process) > 0:
        #     lock_audios_to_process=mark_converted(audios_to_process)        
        # converted_audios = convert_files(audios_to_process)
        # number_audios_updated = mark_converted(converted_audios)
        # print("Number of files processed in the Batch %s" % number_audios_updated)
        # # If conversion resulted in error, move them back to "Recibida" so other process can pick them up
        # audios_to_rollback = [audio for audio in audios_to_process if audio not in converted_audios]
        # number_audios_rollback = mark_rollback(audios_to_rollback)
        # if number_audios_updated > 0:
        #     if SEND_EMAIL == "True":
        #         notify_authors(converted_audios)
        #         print("Notify authors")
        #     else:
        #         print("Not sending emails")
        # return "DONE with SUCCESS"
    except Exception as e:
        print(f"Ocurrió un error durante la ejecución de la tarea: {str(e)}")
        return "DONE with ERRORS"
