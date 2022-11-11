from json import JSONEncoder
from sqlite3 import IntegrityError
from flask_restful import Resource
from flask import request, send_from_directory, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, get_jti
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from modelo import db, Task, TaskSchema, MediaStatus, Usuario
from dotenv import load_dotenv
from os import getenv
import os

ALLOWED_EXTENSIONS = {"wav", "wma", "mp3", "ogg", "flac", "aac", "aiff", "m4a"}

task_schema = TaskSchema()


def set_env():
    load_dotenv()
    global UPLOAD_FOLDER
    UPLOAD_FOLDER = getenv("UPLOAD_FOLDER")
    global CONVERTED_FOLDER
    CONVERTED_FOLDER = getenv("CONVERTED_FOLDER")

set_env()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

         
class VistaTest(Resource):

    def get(self):
        return {"Hola": "Mundo"}

class VistaSignIn(Resource):

    def post(self):
        if (request.json["password1"] == request.json["password2"]):
            requestedUser = Usuario.query.filter(Usuario.usuario == request.json["username"]).first()
            requestedEmail = Usuario.query.filter(Usuario.email == request.json["email"]).first()
            if requestedUser or requestedEmail:
                return {"mensaje": "El usuario o el correo ya existen en el sistema"}
            else:
                nuevo_usuario = Usuario(usuario=request.json["username"], 
                                contrasena=generate_password_hash(request.json["password1"]),
                                email=request.json["email"])
                db.session.add(nuevo_usuario)
                db.session.commit()
                return {"mensaje": "usuario creado exitosamente", "id": nuevo_usuario.id}
        else:
            return {"mensaje": "El usuario no se pudo crear verifique las contraseñas"}

class VistaTaskPorId(Resource):

    @jwt_required()
    def get(self, id):
        #Check if the task exist
        tarea = Task.query.filter(Task.id == id).first()
        if tarea is not None:
        #Check if the user can select the id_task by id_user
            user_id = get_jwt_identity()
            if tarea.user_id == user_id:
                return task_schema.dump(Task.query.get_or_404(id))
            else:
                return {"mensaje": "Este usuario no puede consultar esta tarea"} 
        else: 
            return {"mensaje": "EL id de la tarea no existe"}   


    @jwt_required()
    def delete(self, id):
        #Check if the task exist
        tarea = Task.query.filter(Task.id == id).first()
        if tarea is not None:
        #Check if the user can select the id_task by id_user
            user_id = get_jwt_identity()
            if tarea.user_id == user_id:
                task = Task.query.get_or_404(id)
                db.session.delete(task)
                db.session.commit()
                return {"mensaje": "Tarea eliminada exitosamente"} 
            else:
                return {"mensaje": "Este usuario no puede borrar esta tarea"} 
        else: 
            return {"mensaje": "EL id de la tarea no existe"}
    
    @jwt_required()
    def put(self, id):
        #Check if the task exist
        tarea = Task.query.filter(Task.id == id).first()
        if tarea is not None:
            user_id = get_jwt_identity()
            #Check if task is from user who requested
            if tarea.user_id == user_id:
                #Check if format is allowed
                if request.form["newFormat"] in ALLOWED_EXTENSIONS:
                    #Check if task has been processed
                    if tarea.status == MediaStatus.processed:
                        #Delete file processed and reset task status
                        os.remove(CONVERTED_FOLDER + "/" + tarea.target_path)
                        tarea.status = MediaStatus.uploaded
                    #Change task information and request
                    tarea.target_format = request.form["newFormat"]
                    tarea.target_path = tarea.target_path.rsplit('.', 1)[0] + '.' + request.form["newFormat"]
                    db.session.commit()
                    return task_schema.dump(Task.query.get_or_404(id))
                else:
                    return {"mensaje": "Formato a cambiar no permitido"}
            else:
                return {"mensaje": "No tienes acceso a esta tarea"}
        else:
            return {"mensaje": "La tarea no existe"}

class VistaAuthenticator(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.usuario == request.json["username"]).first()
        db.session.commit()
        if usuario:
            if check_password_hash(usuario.contrasena, request.json["password"]):
                token_de_acceso = create_access_token(identity=usuario.id)
                return {"mensaje": "usuario autenticado exitosamente",
                        "token": token_de_acceso}, 200
            else:
                return {"mensaje": "Contraseña incorrecta"}
        else:
            return {"mensaje": "El usuario no existe"}


class VistaTask(Resource):

    @jwt_required()
    def post(self):
        id_user= get_jwt_identity()
        if allowed_file(request.files['fileName'].filename):
            if request.form["newFormat"] in ALLOWED_EXTENSIONS:
                nuevo_task = Task(source_path= str(id_user) + "_" + request.files["fileName"].filename, 
                                    target_path = str(id_user) + "_" + request.files["fileName"].filename.rsplit('.', 1)[0] + '.' + request.form["newFormat"],
                                    target_format=request.form["newFormat"], 
                                    status=MediaStatus.uploaded,
                                    user_id= id_user)
                db.session.add(nuevo_task)
                db.session.commit()
                print(UPLOAD_FOLDER)
                request.files["fileName"].save(UPLOAD_FOLDER + "/"+ str(id_user) + "_" + request.files["fileName"].filename)
                return {"mensaje": "La tarea fue creada exitosamente", "id": nuevo_task.id}
            else:
                    return {"mensaje": "Formato a cambiar no permitido"}
        else:
            return {"mensaje": "El archivo no es de media"}
    
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        tasks = Task.query.filter(Task.user_id == user_id).all()
        return [task_schema.dump(tarea) for tarea in tasks]
    

class VistaArchivo(Resource):

    @jwt_required()
    def get(self, filename):
        #Get user id from bearer token
        user_id = get_jwt_identity()
        #Get all tasks from user
        tasks = Task.query.filter(Task.user_id == user_id).all()
        archivoUser = str(user_id) + "_" + str(filename)
        convPath = CONVERTED_FOLDER + "/" + str(archivoUser)
        for task in tasks:
            #Check if any task from has an original or uploaded file with the name and extension provided
            if str(task.source_path) == archivoUser:
                return send_from_directory(UPLOAD_FOLDER, archivoUser, as_attachment=True)
            elif str(task.target_path) == archivoUser and os.path.exists(convPath):
                return send_from_directory(CONVERTED_FOLDER, archivoUser, as_attachment=True)
        return {"mensaje": "El archivo no existe."}


