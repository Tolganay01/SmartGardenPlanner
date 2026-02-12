# SmartGardenPlanner
Smart Garden Planner is a web-based application designed to help farmers and home gardeners plan how to use their garden space efficiently. 

Features:
User authentication (Register/Login);
Personalized dashboard;
AI-based crop distribution optimization;
Crop rotation and yield estimation;
Garden area visualization (Pie & Bar charts);
Plan history storage;
Download & share plans.

Tech Stack:
Backend:
Python,
Flask,
SQLite 3,
SQLAlchemy,
Flask-Login,
Gemini AI,
Matplotlib.

Frontend:
HTML (Jinja2 Templates),
CSS (static/style.css)

Project Structure:
smart-garden-planner/
│── app.py               # Main application entry
│── models.py            # Database models
│── ai_generator.py      # AI logic
│── config.py            # Configuration settings
│── database.py          # DB connection
│── init_db.py           # Database initialization
│── password_utils.py    # Password hashing utilities
│── templates/           # HTML templates
│── static/
│    └── style.css       # Main stylesheet
│── requirements.txt

Clone repository:
git clone https://github.com/Tolganay01/SmartGardenPlanner.git

cd SmartGardenPlanner 

Create virtual environment:
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

Install dependencies:
pip install -r requirements.txt

Configure environment variables:
creeate .env file:
SECRET_KEY=(create secret key)
GEMINI_API_KEY=(get your api key from gemini)

Initialize database:
python init_db.py

Run application:
python app.py

Open in browser:
http://127.0.0.1:5000

Authentication:
Secure password hashing,
session-based login via Flask-Login,
password reset functionality.

Machine Learning Logic
The system:
Analyzes crop selection
Evaluates garden conditions
Predicts optimal distribution
Estimates yield
Generates visual diagrams

Authors:
Orazaliyeva Tolganay
Meldebekova Sabina
