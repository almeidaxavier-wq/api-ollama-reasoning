from flask_mongoengine import MongoEngine
from mongoengine import Document, FileField, StringField, IntField, ReferenceField
from werkzeug.security import generate_password_hash, check_password_hash
import os.path as path

db = MongoEngine()

class User(Document):
    id = IntField(primary_key=True)
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    password_hash = StringField(required=True)

    def generate_password_hash(self, new_password):
        # store a salted hash using werkzeug
        if isinstance(new_password, bytes):
            new_password = new_password.decode('utf-8')
        self.password_hash = generate_password_hash(new_password)

    def check_password(self, password):
        if not getattr(self, 'password_hash', None):
            return False
        return check_password_hash(self.password_hash, password)
    
class Upload(Document):
    creator = ReferenceField(User)
    id = IntField(primary_key=True)
    filename = StringField(required=True)
    file = FileField(required=True)
    meta = {'collection': 'uploads'}


def upload_file(user:User, log_dir:str, filename:str, raw_file):
    new_upload_doc = Upload(creator=user)
    new_upload_doc.filename = path.join(log_dir, filename)
    new_upload_doc.file.put(raw_file, content_type="text/markdown")
    new_upload_doc.save()
