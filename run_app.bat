@echo off
echo Installing required packages...
pip install flask flask-sqlalchemy flask-login flask-wtf python-dotenv

echo Starting the application...
python run.py 