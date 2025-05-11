from app.extensions import db


from datetime import datetime





class UserSettings(db.Model):


    __tablename__ = 'user_settings'


    __table_args__ = {'extend_existing': True}


    


    id = db.Column(db.Integer, primary_key=True)


    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)


    theme = db.Column(db.String(20))


    font_size = db.Column(db.String(20))


    notifications_enabled = db.Column(db.Boolean, default=True)


    language = db.Column(db.String(10)) 


    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    


    # Fix relationship with back_populates and overlaps parameters


    user = db.relationship('User', back_populates='settings', overlaps="settings") 