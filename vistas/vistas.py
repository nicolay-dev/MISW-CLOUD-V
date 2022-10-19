from flask_restful import Resource
from flask import request, send_from_directory
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from modelo import db, Task, TaskSchema, MediaStatus, Usuario
from tasks import procesar_audio



UPLOAD_FOLDER = "/home/leslysharyn/audios/original"
CONVERTED_FOLDER = "/home/leslysharyn/audios/converted"
ALLOWED_EXTENSIONS = {"wav", "wma", "mp3", "ogg", "flac", "aac", "aiff", "m4a"}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

         
class VistaSignIn(Resource):

    def post(self):
        nuevo_usuario = Usuario(usuario=request.json["usuario"], 
                                contrasena=generate_password_hash(request.json["contrasena"]))
        db.session.add(nuevo_usuario)
        db.session.commit()
        token_de_acceso = create_access_token(identity=nuevo_usuario.id)
        return {"mensaje": "usuario creado exitosamente", "token": token_de_acceso, "id": nuevo_usuario.id}
       

class VistaAuthenticator(Resource):

    def post(self):
        usuario = Usuario.query.filter(Usuario.usuario == request.json["usuario"]).first()
        db.session.commit()
        if usuario:
            if check_password_hash(usuario.contrasena, request.json["contrasena"]):
                token_de_acceso = create_access_token(identity=usuario.id)
                return {"mensaje": "usuario autenticado exitosamente",
                        "token": token_de_acceso}, 200
            else:
                return {"mensaje": "usuario o contraseña incorrecta"}


class VistaTask(Resource):

    @jwt_required()
    def post(self):
        if allowed_file(request.files['fileName'].filename):
            if request.form["newFormat"] in ALLOWED_EXTENSIONS:
                nuevo_task = Task(source_path= UPLOAD_FOLDER + "/"+ request.files["fileName"].filename, 
                                    target_format=request.form["newFormat"], 
                                    status=MediaStatus.uploaded,
                                    user_id= get_jwt_identity())
                db.session.add(nuevo_task)
                db.session.commit()
                request.files["fileName"].save(UPLOAD_FOLDER + "/"+ request.files["fileName"].filename)
                procesar_audio.delay(nuevo_task.source_path, nuevo_task.target_format, CONVERTED_FOLDER+'/'+ (request.files["fileName"].filename).rsplit('.', 1)[0].lower())
                return {"mensaje": "La tarea fue creada exitosamente"}
            else:
                    return {"mensaje": "Formato a cambiar no permitido"}
        else:
            return {"mensaje": "El archivo no es de media"}
       

class VistaArchivo(Resource):

    @jwt_required()
    def get(self, filename):
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

