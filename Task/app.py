from Task import create_app
from flask_restful import Resource, Api
from flask import Flask, request
from flask_jwt_extended import jwt_required, create_access_token, JWTManager
from flask_cors import CORS
from modelo import db, Task, TaskSchema, MediaStatus
import json

app = create_app('Task')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://misoadmin:miso1234@localhost:5432/cloudtask'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()
db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)

UPLOAD_FOLDER = "/home/leslysharyn/audios/original"
CONVERTED_FOLDER = "/home/leslysharyn/audios/converted"
ALLOWED_EXTENSIONS = {"wav", "wma", "mp3", "ogg", "flac", "aac", "aiff", "m4a"}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class VistaTask(Resource):

    def post(self):
        if allowed_file(request.files['file'].filename):
            if request.form["newFormat"] in ALLOWED_EXTENSIONS:
                nuevo_task = Task(source_path= UPLOAD_FOLDER + "/"+ request.files["fileName"].filename, 
                                    target_format=request.form["newFormat"], 
                                    status=MediaStatus.uploaded,
                                    user_id=request.form["id_usuario"])
                db.session.add(nuevo_task)
                db.session.commit()
                request.files["fileName"].save(UPLOAD_FOLDER + "/"+ request.files["fileName"].filename)
                return {"mensaje": "La tarea fue creada exitosamente"}
            else:
                    return {"mensaje": "Formato a cambiar no permitido"}
        else:
            return {"mensaje": "El archivo no es de media"}
       

api.add_resource(VistaTask, '/api/tasks')

jwt = JWTManager(app)