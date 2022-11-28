import logging
from concurrent import futures
from google.cloud import pubsub_v1
import os
from tasks import tasks
from os import getenv

RUN_AS_SUSCRIBER = getenv("RUN_AS_SUSCRIBER")
future = ''

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'cloud-miso-8.json'



project_id = "cloud-miso"
subscription_id = "worker-subscription"


subscriber = pubsub_v1.SubscriberClient()
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_id}`
subscription_path = subscriber.subscription_path(project_id, subscription_id)


def callback(message):
    logging.info("Received %s", message)
    tasks.procesar_audio()
    message.ack()

def suscribe_to_new_msj(self):
    self.future = subscriber.subscribe(subscription_path, callback=callback)

if RUN_AS_SUSCRIBER == True:
    logging.info("Condicional_suscriber")
    suscribe_to_new_msj()
else: 
    logging.info("Condicional_suscriber_false")

with subscriber:
    try:
        future.result()
    except futures.TimeoutError:
        future.cancel()  # Trigger the shutdown.
        future.result()  # Block until the shutdown is complete.