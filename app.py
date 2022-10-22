from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from modelo import db
from vistas import VistaTask, VistaAuthenticator, VistaSignIn, VistaArchivo, VistaTaskPorId


app = Flask(__name__)
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

api.add_resource(VistaAuthenticator, '/login')
api.add_resource(VistaSignIn, '/signin')
api.add_resource(VistaTask, '/api/tasks')
api.add_resource(VistaTaskPorId, '/api/tasks/<int:id>')
api.add_resource(VistaArchivo, '/api/files/<filename>')


jwt = JWTManager(app)


if __name__ == '__main__':
    app.run(debug=True)
