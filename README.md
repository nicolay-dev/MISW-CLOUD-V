# MISW-CLOUD-V
Repositorio destinado para la aplicación de la asignatura Desarrollo de software en la Nube (Uniandes)

# EJECUCIÓN Y DESPLIEGUE LOCAL

Para realizar el despliegue local en su máquina instale Docker Desktop en su computador.

Clone el repositorio en su máquina local y abra una terminal que apunte a la carpeta del proyecto


## Remueve todos los contenedores (forzado)
docker rm -f $(docker ps -aq)



## Bajar todos los contenedores e imagenes

docker-compose -f docker-compose.prod.yml down -v

## Configure la variable de enviar Email
Por configuración inicial la aplicación no esta configurada para mandar email. Por favor configure en el archivo .env.prod ubicado en el root del proyecto la variable de entorno SEND_EMAIL= "True" para activar la funcionalidad. 

## Construye la imagen 

docker-compose -f docker-compose.prod.yml up -d --build 

## Consideraciones por sistema operativo 

### MacOS
Estar seguro en usuarios MacOS de tener apagado AirPlay Receiver
(Go to System Preference --> Sharing --> uncheck off the AirPlay Receiver)

### WINDOWS
Estar seguro que los archivos docker-compose.prod.yml, Dockerfile.prod, entrypoint.prod.sh están  en LF (configuración de salto de línea en el editor de texto) para Linux 

### El end point del request es http://localhost:1337/

# EJECUCIÓN Y DESPLIEGUE EN CLOUD 

### El end point del request es http://34.122.182.37

Utilice el archivo de postman publicado para realizar las pruebas de los distintos endpoint remotos 

Recuerde configurar la Ip, subir archivos adecuados y configurar el bearer token en las variables remotas. 

https://miso-misw4204-cloud.postman.co/



