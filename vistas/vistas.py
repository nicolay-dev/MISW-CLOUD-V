from json import JSONEncoder
from sqlite3 import IntegrityError
from flask_restful import Resource
from flask import request, send_from_directory, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity, get_jti
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from modelo import db, Task, TaskSchema, MediaStatus, Usuario


UPLOAD_FOLDER = "/home/jcp98/audios/original"
CONVERTED_FOLDER = "/home/jcp98/audios/converted"
ALLOWED_EXTENSIONS = {"wav", "wma", "mp3", "ogg", "flac", "aac", "aiff", "m4a"}
task_schema = TaskSchema()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

         
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
                token_de_acceso = create_access_token(identity=nuevo_usuario.id)
                return {"mensaje": "usuario creado exitosamente", "token": token_de_acceso, "id": nuevo_usuario.id}
        else:
            return {"mensaje": "El usuario no se pudo crear verifique las contraseñas"}
       

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
                request.files["fileName"].save(UPLOAD_FOLDER + "/"+ request.files["fileName"].filename)
                return {"mensaje": "La tarea fue creada exitosamente"}
            else:
                    return {"mensaje": "Formato a cambiar no permitido"}
        else:
            return {"mensaje": "El archivo no es de media"}
    
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        tareas = []
        tasks = Task.query.filter(Usuario.id == user_id).all()
        for task in tasks:
            if task.status == "uploaded":
                newStatus = "uploaded"
            else:
                newStatus = "processed"
            newTarea = {
                "id" : task.id,
                "source_path" : task.source_path,
                "target_path" : task.target_path,
                "target_format" : task.target_format,
                "status" : newStatus,
                "created_at" : task.created_at,
                "user_id" : task.user_id,
            }
            tareas.append(newTarea)
        return [task_schema.dump(tarea) for tarea in tareas]
    
       

class VistaArchivo(Resource):

    @jwt_required()
    def get(self, filename):
        user_id = get_jwt_identity()
        tasks = Task.query.filter(Usuario.id == user_id).all()
        archivoUser = str(user_id) + "_" + str(filename)
        convPath = CONVERTED_FOLDER + "/" + str(filename)
        for task in tasks:
            if str(task.source_path) == archivoUser:
                return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
            elif str(task.target_path) == archivoUser and convPath.exists():
                return send_from_directory(CONVERTED_FOLDER, filename, as_attachment=True)
        return {"mensaje": "El archivo no existe."}


