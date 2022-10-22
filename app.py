from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from modelo import db, Usuario
from vistas import VistaTask, VistaAuthenticator, VistaSignIn, VistaArchivo, VistaTaskPorId, VistaTest
from dotenv import load_dotenv
from os import getenv
from flask.cli import FlaskGroup

def set_env():
    load_dotenv()
    global DATABASE_URL
    DATABASE_URL = getenv("DATABASE_URL")
    global JWT_SECRET_KEY
    JWT_SECRET_KEY = getenv("JWT_SECRET_KEY")


set_env()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()

# db.init_app(app)
# db.create_all()

cli = FlaskGroup(app)

@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    db.session.add(Usuario(usuario= "clouduser", email="clouduser@cloudmisw.com", contrasena="clouduser"))
    db.session.commit()


cors = CORS(app)

api = Api(app)

api.add_resource(VistaTest, '/test')
api.add_resource(VistaAuthenticator, '/login')
api.add_resource(VistaSignIn, '/signin')
api.add_resource(VistaTask, '/api/tasks')
api.add_resource(VistaTaskPorId, '/api/tasks/<int:id>')
api.add_resource(VistaArchivo, '/api/files/<filename>')


jwt = JWTManager(app)



if __name__ == '__main__':
    app.run(debug=False)