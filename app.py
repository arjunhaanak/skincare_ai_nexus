from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
import datetime
from datetime import datetime
from werkzeug.utils import secure_filename
from fpdf import FPDF
import json

try:
    import cv2
    import numpy as np
    import tensorflow as tf
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: ML libraries (TensorFlow/OpenCV) not found. Using mock predictions.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skincare_nexus_secret_key'

# MySQL Configuration (Default for User's WAMP)
MYSQL_URI = 'mysql+mysqlconnector://root:@localhost/skincare_nexus'
# SQLite Fallback for immediate running without MySQL setup
SQLITE_URI = 'sqlite:///skincare_nexus.db'

# Use environment variable or check if we want fallback
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', SQLITE_URI) 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

# --- AI Model Loading ---
MODEL_PATH = 'models/skin_model.h5'
disease_info = {
    'Actinic Keratosis': {
        'desc': 'Actinic Keratosis (AK) is a common precancerous skin lesion caused by chronic exposure to ultraviolet (UV) radiation. CLINICAL PATHOLOGY: Characterized by dysplastic keratinocytes in the basal layer of the epidermis. SYMPTOMS: Rough, scaly, sandpaper-like patches; erythematous base; size ranging from 2mm to 2cm; potential for tenderness or stinging. RISK: 5-10% of AKs progress to Squamous Cell Carcinoma (SCC) if left untreated. URGENCY: Moderate clinical priority.',
        'action': 'A board-certified dermatologist should conduct a full-body skin exam. TREATMENT PROTOCOLS: 1. Field Therapy: Topical 5-Fluorouracil (Efudex) or Imiquimod 5% cream. 2. Cryotherapy: Liquid nitrogen for isolated lesions. 3. Photodynamic Therapy (PDT): Using Aminolevulinic acid (ALA) and light activation.'
    },
    'Basal Cell Carcinoma': {
        'desc': 'Basal Cell Carcinoma (BCC) is the most frequent malignant skin neoplasm globally, originating from the basal cell layer of the epidermis. CLINICAL PATHOLOGY: Slow-growing, locally invasive, but rarely metastatic. SYMPTOMS: Translucent (pearly) papules with telangiectasia (visible blood vessels); central ulceration with "rolled borders"; non-healing sores that bleed easily. URGENCY: High clinical priority - Surgical intervention required to prevent local tissue destruction.',
        'action': 'Urgent dermatological consultation for biopsy and staging. TREATMENT PROTOCOLS: 1. Mohs Micrographic Surgery: Gold standard for facial/recurrent lesions (99% cure rate). 2. Standard Surgical Excision with 4mm margins. 3. Superficial BCC: Topical Imiquimod or Electrodesiccation and Curettage (ED&C).'
    },
    'Dermatofibroma': {
        'desc': 'Dermatofibroma is a benign, common cutaneous fibrous histiocytoma. CLINICAL PATHOLOGY: Reactive proliferation of fibroblasts and histiocytes, often following minor trauma or insect bites. SYMPTOMS: Firm, slightly elevated nodule (3-10mm); color varies from tan to dusky red; "Dimple Sign" present (central indentation when pinched). URGENCY: Low priority - Benign entity.',
        'action': 'Clinical diagnosis is usually sufficient. TREATMENT PROTOCOLS: Generally no treatment is required. If symptomatic (pain/itching) or for cosmetic concerns, options include: 1. Simple Surgical Excision (Full thickness). 2. Cryosurgery (to flatten the lesion). Note: Recurrence is possible if not fully excised.'
    },
    'Melanoma': {
        'desc': 'Melanoma is the most aggressive form of skin cancer, arising from the malignant transformation of melanocytes. CLINICAL PATHOLOGY: High potential for metastasis via lymphatic and hematogenous spread. SYMPTOMS (ABCDE Rule): Asymmetry, irregular Borders, varied Color (shades of blue-black/red), Diameter >6mm, Evolving (changing over time). URGENCY: CRITICAL - Time-sensitive diagnosis is essential for survival.',
        'action': 'IMMEDIATE referral to a Surgical Oncologist or specialized Dermatologist. TREATMENT PROTOCOLS: 1. Wide Local Excision (WLE) with appropriate margins based on Breslow Depth. 2. Sentinel Lymph Node Biopsy (SLNB) for staging. 3. Systemic Therapy: Targeted therapy (BRAF inhibitors) or Immunotherapy (Pembrolizumab) for advanced stages.'
    },
    'Nevus': {
        'desc': 'A Melanocytic Nevus (Common Mole) is a benign proliferation of melanocytes. CLINICAL PATHOLOGY: Nesting of melanocytic cells at the dermo-epidermal junction (Junctional) or within the dermis (Intradermal). SYMPTOMS: Uniform color (tan/brown); well-defined borders; symmetrical shape; stable over years. URGENCY: Routine monitoring.',
        'action': 'Annual dermatological screenings recommended. TREATMENT PROTOCOLS: No treatment required unless dysplastic features develop. If removed for cosmetic reasons: 1. Shave Excision. 2. Punch Biopsy/Excision for deeper lesions. Use the "Ugly Duckling" sign to identify atypical lesions for further biopsy.'
    },
    'Pigmented Benign Keratosis': {
        'desc': 'Pigmented Benign Keratosis (including Seborrheic Keratosis and Lichen Planus-like Keratosis) is a non-cancerous epidermal growth. CLINICAL PATHOLOGY: Proliferation of immature keratinocytes. SYMPTOMS: Waxy, "stuck-on" appearance; pigmented ranges from light tan to dark brown; verrucous (wart-like) surface. URGENCY: Low priority - Cosmetic concern only.',
        'action': 'Consultation to rule out melanoma if pigmentation is highly irregular. TREATMENT PROTOCOLS: 1. Cryotherapy (Liquid Nitrogen). 2. Curettage: Scraping the lesion off with a surgical tool. 3. Laser Ablation: For multiple cosmetic removals. These lesions do not have malignant potential.'
    },
    'Squamous Cell Carcinoma': {
        'desc': 'Squamous Cell Carcinoma (SCC) is the second most common skin cancer, arising from malignant keratinocytes. CLINICAL PATHOLOGY: Locally invasive with a moderate risk (2-5%) of metastasis. SYMPTOMS: Firm, red, nodular lesions; scaly or crusty surfaces; persistent non-healing ulcers; often located on sun-exposed areas (head, neck, hands). URGENCY: High clinical priority - Risk of systemic spread.',
        'action': 'Prompt surgical consultation and diagnostic biopsy. TREATMENT PROTOCOLS: 1. Standard Surgical Excision. 2. Mohs Micrographic Surgery (for high-risk locations). 3. Radiation Therapy: For patients unsuitable for surgery. 4. Elective Lymph Node Evaluation for high-risk clinical features.'
    }
}
classes = list(disease_info.keys())

# Global variable for model
model = None

def get_model():
    global model
    if not ML_AVAILABLE:
        return None
    if model is None:
        if os.path.exists(MODEL_PATH):
            try:
                model = tf.keras.models.load_model(MODEL_PATH)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print("Warning: Model not found at models/skin_model.h5. Predictions will be mock.")
    return model

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
            flash('Email already exists.', 'danger')
            
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
    return render_template('dashboard/index.html', predictions=predictions)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Predict
            ai_model = get_model()
            if ML_AVAILABLE and ai_model:
                try:
                    # Image Preprocessing
                    img = cv2.imread(filepath)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.GaussianBlur(img, (5, 5), 0)
                    img = cv2.resize(img, (224, 224))
                    img_arr = np.array(img) / 255.0
                    img_arr = np.expand_dims(img_arr, axis=0)
                    
                    preds = ai_model.predict(img_arr)[0]
                    idx = np.argmax(preds)
                    confidence = float(preds[idx]) * 100
                    label = classes[idx]
                except Exception as e:
                    print(f"Prediction error: {e}")
                    label = "Error during Analysis"
                    confidence = 0
            else:
                # Mock prediction for demonstration if model missing or libs missing
                import random
                label = random.choice(classes)
                confidence = random.uniform(70, 99)
            
            info = disease_info[label]
            
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
            
            # Store in session for result page
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
        user_msg = request.json.get('message').lower()
        
        # Simple Intent/Keyword Recognition
        response = "I'm sorry, I don't have information on that. Please consult a dermatologist."
        
        intents = {
            'symptoms': ['signs', 'symptoms', 'look like', 'feel like'],
            'treatment': ['cure', 'treat', 'medicine', 'cream', 'therapy'],
            'doctor': ['specialist', 'derm', 'consult', 'hospital', 'see a doctor'],
            'prevention': ['prevent', 'avoid', 'sunscreen', 'protection']
        }
        
        # Check last prediction context
        last_pred = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.created_at.desc()).first()
        context_disease = last_pred.predicted_class if last_pred else None
        
        if any(word in user_msg for word in intents['symptoms']):
            if context_disease:
                response = f"Symptoms for {context_disease} usually include specific skin changes. Please refer to our detailed analysis in your history."
            else:
                response = "Common skin disease symptoms include redness, itching, and unusual moles or spots."
        elif any(word in user_msg for word in intents['treatment']):
            response = "Treatments vary from topical creams to minor surgery. A specialist can provide the best medical plan."
        elif any(word in user_msg for word in intents['doctor']):
            response = "If you notice changes in size, shape, color, or if a spot starts bleeding, you should see a dermatologist immediately."
        elif any(word in user_msg for word in intents['prevention']):
            response = "Protect your skin from UV rays using SPF 30+ sunscreen, wearing hats, and avoiding peak sun hours."
        
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
    with app.app_context():
        # Crucial for initializing DB with SQLAlchemy if not using existing SQL script manually
        # But user mentioned MySQL/WAMP, so they should run the .sql script first.
        # This will create tables if they don't exist in the configured MySQL DB.
        db.create_all() 
    app.run(host='0.0.0.0', port=5001, debug=True)
