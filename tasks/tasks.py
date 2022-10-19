from celery import Celery
import subprocess

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def procesar_audio(filepath, target_format, new_path):
    print('Procesando audio en: path ' + filepath + ' a formato ' + target_format)
    result = subprocess.run(["ffmpeg", "-y", "-i", filepath, new_path+'.'+target_format])
