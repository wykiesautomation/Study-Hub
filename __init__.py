import os
from flask import Flask
from flask_login import LoginManager
from .models import db,User,seed_demo
from .routes import bp
from .api import api
login=LoginManager();login.login_view='main.login'
@login.user_loader
def load_user(uid):return db.session.get(User,int(uid))
def create_app(testing=False):
 app=Flask(__name__)
 app.config.update(SECRET_KEY=os.getenv('SECRET_KEY','fleettrack-dev-change-me'),SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///fleettrack360.db').replace('postgres://','postgresql+psycopg://',1),SQLALCHEMY_TRACK_MODIFICATIONS=False,TESTING=testing,MAX_CONTENT_LENGTH=8*1024*1024)
 db.init_app(app);login.init_app(app);app.register_blueprint(bp);app.register_blueprint(api,url_prefix='/api/fleet/v1')
 with app.app_context():
  db.create_all()
  if os.getenv('SEED_DEMO','false').lower()=='true':seed_demo()
 return app
