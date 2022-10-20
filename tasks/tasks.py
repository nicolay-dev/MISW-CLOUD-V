from celery import Celery
import subprocess
from flask import current_app
from flask_mail import Mail, Message
import smtplib
from email.mime.text import MIMEText

celery = Celery('tasks', broker='redis://localhost:6379/0')


@celery.task
def procesar_audio(filepath, target_format, new_path):
    print('Procesando audio en: path ' + filepath + ' a formato ' + target_format)
    result = subprocess.run(["ffmpeg", "-y", "-i", filepath, new_path+'.'+target_format])
    email_data = {
        'subject': 'Hello from the other side!',
        'to': "lcampojimenez@gmail.com",
        'body': "Your file is ready, you can download it from the following link: http://localhost:5000/'/api/files/<filename>'"
    }
    send_async_email(email_data)


@celery.task
def send_async_email(email_data):
    sender = "Private Person <from@smtp.mailtrap.io>"
    receiver = email_data["to"]

    message = MIMEText(email_data["body"])
    message["Subject"] = email_data["subject"]
    message["From"] = sender
    message["To"] = receiver

    with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:
        server.login("d6c443b941c34d", "dd3bce0a9b04ff")
        server.sendmail(sender, receiver, message.as_string())
