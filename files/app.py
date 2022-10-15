from flask import Flask, send_from_directory
from flask_restful import Resource, Api

UPLOAD_FOLDER = r"C:\Users\juanc\OneDrive\Documentos"

app = Flask(__name__)
api = Api(app)

class VistaArchivo(Resource):
    def get(self, filename):
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

api.add_resource(VistaArchivo, '/api/files/<filename>')

if __name__ == '__main__':
    app.run(debug=True)
