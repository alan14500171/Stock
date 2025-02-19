from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
def get_db_session(app):
    engine = db.get_engine(app)
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory) 