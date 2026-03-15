from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from fpdf import FPDF
import json
from config import Config
from utils.ai_engine import AIEngine
from metadata import DISEASE_INFO

app = Flask(__name__)
app.config.from_object(Config)

# Security Enhancements
csrf = CSRFProtect(app)
talisman = Talisman(app, 
    content_security_policy=None, 
    force_https=False
)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# AI Engine Initialization
ai_engine = AIEngine(os.path.join(app.root_path, 'models', 'skin_model.h5'), DISEASE_INFO)

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    predictions = db.relationship('Prediction', backref='owner', lazy=True)
    chats = db.relationship('Chat', backref='owner', lazy=True)

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    predicted_class = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    suggested_action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def home():
    return render_template('main/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name=name, email=email, password=hashed_pw)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already exists or invalid data.', 'danger')
            
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
            
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).limit(5).all()
    # Analytics data for dashboard
    counts = {
        'total': Prediction.query.filter_by(user_id=current_user.id).count(),
        'high_risk': Prediction.query.filter_by(user_id=current_user.id).filter(Prediction.predicted_class.in_(['Melanoma', 'Basal Cell Carcinoma', 'Squamous Cell Carcinoma'])).count()
    }
    return render_template('dashboard/index.html', predictions=predictions, counts=counts)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Predict
            label, confidence = ai_engine.predict_image(filepath)
            info = DISEASE_INFO.get(label, {'desc': 'No information available.', 'action': 'Consult a doctor.'})
            
            # Save to Database
            new_pred = Prediction(
                user_id=current_user.id,
                image_path=filepath,
                predicted_class=label,
                confidence=confidence,
                description=info['desc'],
                suggested_action=info['action']
            )
            db.session.add(new_pred)
            db.session.commit()
            
            session['last_prediction_id'] = new_pred.id
            return redirect(url_for('result'))
            
    return render_template('dashboard/predict.html')

@app.route('/result')
@login_required
def result():
    pred_id = session.get('last_prediction_id')
    if not pred_id:
        return redirect(url_for('dashboard'))
    
    prediction = Prediction.query.get(pred_id)
    return render_template('dashboard/result.html', prediction=prediction)

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        user_msg = request.json.get('message')
        
        # Check last prediction context
        last_pred = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).first()
        context_disease = last_pred.predicted_class if last_pred else None
        
        response = ai_engine.get_ai_response(user_msg, context_disease)
        
        # Save chat
        new_chat = Chat(user_id=current_user.id, message=user_msg, response=response)
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({'response': response})
        
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp.asc()).all()
    return render_template('dashboard/chatbot.html', chats=chats)

@app.route('/history')
@login_required
def history():
    predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).all()
    return render_template('dashboard/history.html', predictions=predictions)

@app.route('/report/<int:id>')
@login_required
def download_report(id):
    prediction = Prediction.query.get_or_404(id)
    if prediction.user_id != current_user.id:
        return "Unauthorized", 403
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Skincare AI Nexus - Prediction Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Patient Name: {current_user.name}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {prediction.created_at.strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analysis Results", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Detected Condition: {prediction.predicted_class}", ln=True)
    pdf.cell(200, 10, txt=f"Confidence Level: {prediction.confidence:.2f}%", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Description:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, txt=prediction.description)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Suggested Action:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=prediction.suggested_action, ln=True)
    
    response = app.response_class(
        pdf.output(dest='S').encode('latin-1'),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=report_{id}.pdf'}
    )
    return response

@app.route('/about')
def about():
    return render_template('main/about.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    with app.app_context():
        db.create_all() 
    app.run(host='0.0.0.0', port=5001, debug=True)
