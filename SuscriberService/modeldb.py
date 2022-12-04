import database as database
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
import enum
from sqlalchemy.orm import relationship

## Enumeration of possible status a media can be in.
class MediaStatus(enum.Enum):
    uploaded = "uploaded"
    processed = "processed"


class Task(database.Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    source_path = Column(String(50))
    target_path = Column(String(50))
    target_format = Column(String(10))
    status = Column(Enum(MediaStatus))
    created_at = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey('usuario.id'))
    author = relationship('Usuario', back_populates = 'tasks' )

class Usuario(database.Base):
    __tablename__ = 'usuario'
    id = Column(Integer, primary_key=True)
    usuario = Column(String(50))
    contrasena = Column(String(255))
    email = Column(String(255))
    tasks = relationship('Task', cascade='all, delete, delete-orphan', back_populates = "author" )

    def __repr__(self):
        return self.email
    def __str__(self):
        return self.email

