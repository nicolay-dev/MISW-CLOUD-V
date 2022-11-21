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

### El end point del request es http://35.241.56.82 el cual es la ip del load balancer

Utilice el archivo de postman publicado para realizar las pruebas de los distintos endpoint remotos 

Recuerde configurar la Ip, subir archivos adecuados y configurar el bearer token en las variables remotas. 

[https://miso-misw4204-cloud.postman.co/
](https://documenter.getpostman.com/view/20288420/2s84Dssfmy)

# REPLICAR PRUEBAS 

Por favor solicitar acceso al proyecto en Google Cloud al siguiente correo: leslysharyncj@gmail.com (no se colocan claves para entrar por ser correo personal).  

Ejecutar las pruebas desde la instancia test-instance 

Cargar el archivo de configuración a la máquina virtual, recuerde que el archivo de configuración debe tener el bearer token en el head, para generarlo utilice postman para login y copie y pegue el token en el header de Jmeter.  

El archivo de configuración lo puede encontrar en el repositorio  

https://github.com/nicolay-dev/MISW-CLOUD-V/blob/main/testaudio.jmx 

Para replicar las pruebas se debe cargar el archivo de configuración de JMeter y ejecutarlo con el siguiente comando: 

./jmeter.sh -n -t <<Path del archivo de configuración de JMeter en la máquina de cgp>> -l <<Path del archivo de logs con los resultados de ejecución>> 
