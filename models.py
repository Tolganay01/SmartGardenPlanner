from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    garden_plans = db.relationship('GardenPlan', backref='user', lazy=True)

class GardenPlan(db.Model):
    # ... keep this exactly as is, no changes needed ...
    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    location = db.Column(db.String(100))
    garden_type = db.Column(db.String(50))
    garden_size = db.Column(db.Float)
    soil_type = db.Column(db.String(50))
    sunlight = db.Column(db.String(50))
    watering_frequency = db.Column(db.String(50))
    main_goal = db.Column(db.String(100))
    pest_prevention = db.Column(db.Boolean, default=False)
    
    crop_data = db.Column(db.Text)
    optimized_layout = db.Column(db.Text)
    estimated_yield = db.Column(db.Text)
    planting_periods = db.Column(db.Text)
    smart_advice = db.Column(db.Text)
    
    pie_chart_image = db.Column(db.Text)
    bar_chart_image = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'plan_name': self.plan_name,
            'location': self.location,
            'garden_size': self.garden_size,
            'soil_type': self.soil_type,
            'sunlight': self.sunlight,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }