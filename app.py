from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from modelo import db
import logging
from vistas import VistaTask, VistaAuthenticator, VistaSignIn, VistaArchivo, VistaTaskPorId, VistaTest
from dotenv import load_dotenv
from os import getenv
from concurrent import futures
import logging
from google.cloud import pubsub_v1
import os
from tasks import tasks

def set_env():
    load_dotenv()
    global DATABASE_URL
    DATABASE_URL = getenv("DATABASE_URL")
    global JWT_SECRET_KEY
    JWT_SECRET_KEY = getenv("JWT_SECRET_KEY")
    global RUN_AS_SUSCRIBER
    RUN_AS_SUSCRIBER = getenv("RUN_AS_SUSCRIBER")

set_env()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)

api.add_resource(VistaTest, '/test')
api.add_resource(VistaAuthenticator, '/api/auth/login')
api.add_resource(VistaSignIn, '/api/auth/signup')
api.add_resource(VistaTask, '/api/tasks')
api.add_resource(VistaTaskPorId, '/api/tasks/<int:id>')
api.add_resource(VistaArchivo, '/api/files/<filename>')


jwt = JWTManager(app)
LOG_FILENAME = './logs/suscriber.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.info("Recibido")
app.logger.debug('nuevo_log')
logging.debug('Recibido3')

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'cloud-miso-8.json'
project_id = "cloud-miso"
subscription_id = "worker-subscription"
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)


def callback(message):
    tasks.procesar_audio(message)
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




LOG_FILENAME = 'web.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.info("WEb iniciada")
logging.debug('This message should go to the log file')

if __name__ == '__main__':
    app.run(debug=True)
    
    
