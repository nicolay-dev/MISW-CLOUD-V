import enum
import datetime
from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

db = SQLAlchemy()

## Enumeration of possible status a media can be in.
class MediaStatus(enum.Enum):
    uploaded = "uploaded"
    processed = "processed"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_path = db.Column(db.String(50))
    target_path = db.Column(db.String(50))
    target_format = db.Column(db.String(10))
    status = db.Column(db.Enum(MediaStatus))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    contrasena = db.Column(db.String(255))
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')
    


class UsuarioSchema(SQLAlchemyAutoSchema):
    class Meta:
         model = Usuario
         include_relationships = True
         load_instance = True

         
class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
         model = Task
         include_relationships = True
         load_instance = True