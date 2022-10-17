from Authenticator import create_app
from flask_restful import Resource, Api
from flask import Flask, request
from flask_jwt_extended import jwt_required, create_access_token, JWTManager
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from modelo import db, Usuario
import secrets
import json

app = create_app('Authenticator')
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

class VistaSignIn(Resource):

    def post(self):
        newKey = secrets.token_hex(16)
        nuevo_usuario = Usuario(usuario=request.json["usuario"], contrasena=generate_password_hash(request.json["contrasena"]))
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
                result = json.dumps({
                    "mensaje": "usuario autenticado exitosamente",
                    "token": token_de_acceso,
                    "usuario_id": usuario.id
                })
                return {"mensaje": "usuario autenticado exitosamente","token": token_de_acceso,"usuario_id": usuario.id}, 200
            else:
                return {"mensaje": "usuario o contraseña incorrecta"}

        

api.add_resource(VistaAuthenticator, '/login')
api.add_resource(VistaSignIn, '/signin')

jwt = JWTManager(app)