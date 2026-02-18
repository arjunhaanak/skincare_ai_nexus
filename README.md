# SKINCARE AI NEXUS 🩺

**Automated Multi-Disease Skin Analysis Using CNN and Conversational Intelligence**

Skincare AI Nexus is a premium full-stack web application designed to help users identify potential skin conditions using cutting-edge deep learning (VGG16) and interact with an AI-powered dermatologist chatbot.

## 🚀 Features
- **Skin Disease Classification**: Detects 7 diseases (Melanoma, Basal Cell Carcinoma, etc.) using VGG16 Transfer Learning.
- **AI Chatbot**: NLP-based virtual assistant for medical guidance and symptoms.
- **Medical Reports**: Generate and download detailed PDF reports of your analysis.
- **Analytics Dashboard**: Probability charts (Chart.js) and history tracking.
- **Modern UI**: Dark/Light mode support with premium glassmorphism aesthetics.
- **Secure**: Password hashing, session management, and secure file uploads.

## 🛠️ Tech Stack
- **Backend**: Python, Flask, SQLAlchemy, TensorFlow, Keras.
- **Frontend**: HTML5, CSS3 (Vanilla + Bootstrap 5), JavaScript (Vanilla + Chart.js).
- **Database**: MySQL (Compatible with WAMP/XAMPP).
- **AI Model**: VGG16 Convolutional Neural Network.

## 📦 Installation & Setup

### 1. Database Configuration
1. Start your **MySQL** server (e.g., using WAMP or XAMPP).
2. Create a database named `skincare_nexus`.
3. Import the `database.sql` file provided in the project root.
4. Update the `SQLALCHEMY_DATABASE_URI` in `app.py` if your MySQL credentials differ (Default: `root:@localhost`).

### 2. Environment Setup
1. Open terminal in the project directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Model Preparation
1. To train the model, place your dataset in `data/skin_diseases` (7 folders for 7 classes).
2. Run the training script:
   ```bash
   python train_model.py
   ```
3. If you don't have a dataset, the script will create an untrained `models/skin_model.h5` so the application can still run (predictions will be mock).

### 4. Run the Application
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

## 📂 Project Structure
```
skincare_ai_nexus/
├── app.py              # Main Flask Backend
├── train_model.py      # CNN Training Script
├── database.sql        # SQL Schema
├── requirements.txt    # Dependencies
├── static/             # CSS, JS, Images
├── templates/          # HTML Templates (Auth, Dashboard, Main)
├── models/             # Saved .h5 Model
├── uploads/            # User Uploaded Images
└── data/               # (User) Training Dataset
```

## ⚖️ Disclaimer
*This application is for educational purposes and is not a replacement for professional medical diagnosis.*
