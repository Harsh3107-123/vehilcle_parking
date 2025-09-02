from app import app
# import os to handle file paths
import os
# import load_dotenv to load environment variables from a .env file
from dotenv import load_dotenv
# load environment variables from a .env file
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False