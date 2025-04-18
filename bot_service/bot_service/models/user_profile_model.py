from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from uuid import uuid4

db = SQLAlchemy()

class BaseUser(db.Model):
    __tablename__ = 'base_user'

    sub = db.Column(db.String(255), primary_key=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    picture = db.Column(db.String(255))
    is_service_provider = db.Column(db.Boolean, default=False)
    user_rating = db.Column(db.Float, default=5.0)
    mobile_number = db.Column(db.String(20))

    # Location fields
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province_or_state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Weekly schedule
    weekly_schedule = db.Column(
        JSON,
        default=lambda: {
            "monday": {"available": True, "start": "09:00", "end": "17:00"},
            "tuesday": {"available": True, "start": "09:00", "end": "17:00"},
            "wednesday": {"available": True, "start": "09:00", "end": "17:00"},
            "thursday": {"available": True, "start": "09:00", "end": "17:00"},
            "friday": {"available": True, "start": "09:00", "end": "17:00"},
            "saturday": {"available": False, "start": None, "end": None},
            "sunday": {"available": False, "start": None, "end": None}
        }
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BaseUser {self.name}>'
    
    
class RoleUpdate(db.Model):
    __tablename__ = 'role_update'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()), index = True)  
    sub = db.Column(db.String(255), db.ForeignKey('base_user.sub'), nullable=False)
    is_service_provider = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to BaseUser
    base_user = db.relationship('BaseUser', backref=db.backref('role_updates', lazy=True))
    
    def __repr__(self):
        return f'<RoleUpdate {self.id} for user {self.sub}>'