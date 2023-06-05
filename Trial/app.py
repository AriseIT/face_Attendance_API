from flask import Flask
import os

try:
    os.mkdir('StuData')
except OSError as e:
    pass
UPLOAD_FOLDER = 'StuData'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
