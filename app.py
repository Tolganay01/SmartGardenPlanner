from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import sys
import traceback
import re  
from datetime import datetime

from config import Config
from database import db
from models import User, GardenPlan
from ai_generator import GardenAIGenerator

# Initialize app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize AI generator
ai_generator = GardenAIGenerator()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        data_dir = os.path.join(app.config['BASE_DIR'], 'data')
        os.makedirs(data_dir, exist_ok=True)
        db.create_all()
        print("Database initialized successfully!")

try:
    init_db()
except Exception as e:
    print(f"Error initializing database: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        from password_utils import validate_password_strength
        
        errors = []
        
        # Username validation
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            errors.append("Username can only contain letters, numbers, and underscores")
        
        # Email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Please enter a valid email address")
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            errors.append("Username already exists")
        
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered")
        
        # Password validation
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        password_errors = validate_password_strength(password)
        errors.extend(password_errors)
        
        if errors:
            for error in errors:
                flash(error)
            return redirect(url_for('register'))
        
        # Create new user - NO EMAIL VERIFICATION NEEDED
        new_user = User(
            username=username, 
            email=email, 
            password_hash=generate_password_hash(password)
        )
        try:
            db.session.add(new_user)
            db.session.commit()
    
            # ✅ AUTO VERIFY - NO EMAIL, NO VERIFICATION
            login_user(new_user)
            flash(f'Welcome to Smart Garden Planner, {username}!')
            return redirect(url_for('account'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")
            flash('Error creating account. Please try again.')
    
    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        # ✅ NO EMAIL VERIFICATION CHECK - just login
        login_user(user)
        
        # Optional: password strength warning
        from password_utils import check_password_complexity
        complexity = check_password_complexity(password)
        if complexity['strength'] == 'Weak':
            flash('Your password is weak. Consider changing it for better security.', 'warning')
        
        return redirect(url_for('account'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    # 🔴 ADD THIS - Clear all flash messages and session data
    session.clear()
    flash('You have been logged out successfully.')
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    saved_plans = GardenPlan.query.filter_by(user_id=current_user.id).all()
    return render_template('account.html', user=current_user, plans=[p.to_dict() for p in saved_plans])

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')  # Add this field to your form
    
    from password_utils import validate_password_strength
    
    # Verify current password
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect')
        return redirect(url_for('account'))
    
    # Check if new password matches confirmation
    if new_password != confirm_password:
        flash('New passwords do not match')
        return redirect(url_for('account'))
    
    # Validate new password strength
    password_errors = validate_password_strength(new_password)
    if password_errors:
        for error in password_errors:
            flash(error)
        return redirect(url_for('account'))
    
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Password updated successfully!')
    return redirect(url_for('account'))

# Password Reset Routes
@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            send_password_reset_email(user)
            flash('Check your email for password reset instructions.')
        else:
            flash('No account found with that email address.')
        
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = confirm_token(token)
    if not email:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('reset_password_request'))
    
    user = User.query.filter_by(email=email).first_or_404()
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('reset_password', token=token))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters')
            return redirect(url_for('reset_password', token=token))
        
        user.password_hash = generate_password_hash(password)
        db.session.commit()
        
        flash('Your password has been updated! You can now login.')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

# Create Plan Route (updated to check verification)
@app.route('/create-plan', methods=['GET', 'POST'])
@login_required
def create_plan():
    
    # ... rest of your existing create_plan code ...
    if request.method == 'POST':
        try:
            # 1. Collect form data
            garden_data = {
                'location': request.form.get('location', 'Global'),
                'garden_type': request.form.get('garden_type', 'open_ground'),
                'garden_size': float(request.form.get('garden_size', 10)),
                'soil_type': request.form.get('soil_type', 'loamy'),
                'sunlight': request.form.get('sunlight', 'full_sun'),
                'watering_frequency': request.form.get('watering_frequency', '2_3_times'),
                'main_goal': request.form.get('main_goal', 'consumption'),
                'pest_prevention': request.form.get('pest_prevention') == 'yes',
                'crops': []
            }
            
            # 2. Process crops
            names, areas = request.form.getlist('crop_name[]'), request.form.getlist('crop_area[]')
            total_crop_area = 0
            
            for n, a in zip(names, areas):
                if n and a: 
                    area = float(a)
                    total_crop_area += area
                    garden_data['crops'].append({'name': n.strip(), 'area': area})
            
            if not garden_data['crops']:
                flash('Please add at least one crop')
                return redirect(url_for('create_plan'))
            
            # 🔴 VALIDATION - Only show error, no warning
            garden_size = garden_data['garden_size']
            
            if total_crop_area > garden_size:
                flash(f'❌ Total crop area ({total_crop_area:.1f} sqm) exceeds your garden size ({garden_size:.1f} sqm). Please reduce crop areas or increase garden size.')
                return redirect(url_for('create_plan'))
            # ✅ REMOVED the unused space warning completely
            
            # 3. Generate AI plan with Retry Logic
            ai_plan = ai_generator.generate_plan(garden_data)
            
            if ai_plan.get('is_fallback'):
                flash("The AI service is busy. Showing a standard global plan for now.", "info")
            
            # 4. Save to Database
            new_plan = GardenPlan(
                plan_name=f"Plan for {garden_data['location']}",
                user_id=current_user.id,
                location=garden_data['location'],
                garden_type=garden_data['garden_type'],
                garden_size=garden_data['garden_size'],
                soil_type=garden_data['soil_type'],
                sunlight=garden_data['sunlight'],
                watering_frequency=garden_data['watering_frequency'],
                main_goal=garden_data['main_goal'],
                pest_prevention=garden_data['pest_prevention'],
                crop_data=json.dumps(garden_data['crops']),
                optimized_layout=json.dumps(ai_plan.get('optimized_layout', {})),
                estimated_yield=json.dumps(ai_plan.get('estimated_yield', {})),
                planting_periods=json.dumps(ai_plan.get('planting_periods', {})),
                smart_advice=json.dumps(ai_plan.get('smart_advice', {})),
                pie_chart_image=ai_plan.get('visualizations', {}).get('pie_chart'),
                bar_chart_image=ai_plan.get('visualizations', {}).get('bar_chart')
            )
            
            db.session.add(new_plan)
            db.session.commit()
            
            return render_template('plan_result.html', plan=new_plan, garden_data=garden_data, ai_plan=ai_plan)

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            flash(f'Error: {str(e)}')
            return redirect(url_for('create_plan'))
    
    return render_template('plan_form.html', max_crops=Config.MAX_CROPS)

# View Plan (no changes needed)
@app.route('/plan/<int:plan_id>')
@login_required
def view_plan(plan_id):
    plan = GardenPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        return redirect(url_for('account'))
    
    garden_data = {'crops': json.loads(plan.crop_data or '[]'), 'location': plan.location}
    ai_plan = {
        'optimized_layout': json.loads(plan.optimized_layout or '{}'),
        'estimated_yield': json.loads(plan.estimated_yield or '{}'),
        'planting_periods': json.loads(plan.planting_periods or '{}'),
        'smart_advice': json.loads(plan.smart_advice or '{}'),
        'visualizations': {'pie_chart': plan.pie_chart_image, 'bar_chart': plan.bar_chart_image}
    }
    return render_template('plan_result.html', plan=plan, garden_data=garden_data, ai_plan=ai_plan)

@app.route('/delete-plan/<int:plan_id>')
@login_required
def delete_plan(plan_id):
    plan = GardenPlan.query.get_or_404(plan_id)
    if plan.user_id == current_user.id:
        db.session.delete(plan)
        db.session.commit()
        flash('Plan deleted.')
    return redirect(url_for('account'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)