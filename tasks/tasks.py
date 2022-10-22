from string import ascii_lowercase
from celery import Celery
from celery.utils.log import get_task_logger
import subprocess
import smtplib
from email.mime.text import MIMEText
from database import session
from modeldb import Task, MediaStatus

UPLOAD_FOLDER = "/home/leslysharyn/audios/original"
CONVERTED_FOLDER = "/home/leslysharyn/audios/converted"

celery = Celery('tasks', broker='redis://localhost:6379/0')

celery.conf.beat_schedule = {
    "Convert-audio-files": {
        "task": "tasks.procesar_audio",
        "schedule": 30.0
    }
}




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
            send_email(email_data)
        except Exception as e:
            print(f"Unable to send notification to '{author_email}': {e}")
    

def send_email(email_data):
    print(email_data)
    sender = "Private Person <from@smtp.mailtrap.io>"
    receiver = email_data["to"]

    message = MIMEText(email_data["body"])
    message["Subject"] = email_data["subject"]
    message["From"] = sender
    message["To"] =  receiver

    with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
        server.login("43016d8c11fc9e", "ace826b1322476")
        server.sendmail(sender, receiver,   message.as_string())

def convert_files(audios_to_process):
    converted_audios = []
    for audio in audios_to_process:
        source_path = UPLOAD_FOLDER + '/'+ audio.source_path
        target_path = CONVERTED_FOLDER + '/'+ audio.target_path
        target_format = audio.target_format
        try:
            result = subprocess.run(["ffmpeg", "-y", "-i", source_path, target_path])
            if result.returncode == 0:
                converted_audios.append(audio)
        except Exception as e:
            print("Error al convertir el archivo: %s", e)
    return list(converted_audios)
    
def mark_converted(converted_audios):
    if len(converted_audios) == 0:
        print("Ninguna voz fue convertida en esta iteración.")
        return 0
    converted_files_ids = tuple(map(lambda audio: audio.id, converted_audios))
    for id in converted_files_ids:
        print(id)
    rowcount = session.query(Task).filter(Task.id.in_(converted_files_ids)).\
                update({"status": MediaStatus.processed})
    session.commit()
    
    return rowcount


@celery.task
def procesar_audio():
    try:
        audios_to_process = session.query(Task).filter_by(status = MediaStatus.uploaded).all()
        converted_audios = convert_files(audios_to_process)
        number_audios_updated = mark_converted(converted_audios)
        print(number_audios_updated)
        # If conversion resulted in error, move them back to "Recibida" so other process can pick them up
        audios_to_rollback = [audio for audio in audios_to_process if audio not in converted_audios]
        if number_audios_updated > 0:
            print("Notify authors")
            notify_authors(converted_audios)
        return "DONE with SUCCESS"
    except Exception as e:
        print(f"Ocurrió un error durante la ejecución de la tarea: {str(e)}")
        return "DONE with ERRORS"
