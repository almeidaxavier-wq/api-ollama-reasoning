from flask_mongoengine import MongoEngine
from mongoengine import Document, FileField, StringField, IntField, ReferenceField
from cryptography.fernet import Fernet
import os.path as path

db = MongoEngine()

class User(Document):
    id = IntField(unique=True, required=True, primary_key=True)
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)

    def __init__(self):
        self.__password_hash = None
        self.__f = None

    def generate_password_hash(self, new_password):
        key = Fernet.generate_key()
        self.__f = Fernet(key)
        self.__password_hash = self.__f.encrypt(new_password)

    def check_password(self, password):
        password_other = self.__f.decrypt(self.__password_hash)
        if password == str(password_other):
            return True
        return False
    
class Upload(Document):
    creator = ReferenceField(User)
    id = IntField(primary_key=True, unique=True, required=True)
    filename = StringField(unique=True, required=True)
    file = FileField(unique=True, required=True)
    meta = {'collection': 'uploads'}


def upload_file(user:User, log_dir:str, filename:str, raw_file):
    new_upload_doc = Upload(creator=user)
    new_upload_doc.filename = path.join(log_dir, filename)
    new_upload_doc.file.put(raw_file, content_type="text/markdown")
    new_upload_doc.save()
