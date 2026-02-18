# 🩺 Skincare AI Nexus - Clinical Intelligence Portal
**Neural-Accelerated Dermatological Analysis & Conversational AI**

[![GitHub Portal](https://img.shields.io/badge/Clinical-Portal-2563eb?style=for-the-badge&logo=mediamarkt)](https://github.com/arjunhaanak/skincare_ai_nexus)
[![AI Model](https://img.shields.io/badge/Neural_Engine-VGG16-0ea5e9?style=for-the-badge&logo=tensorflow)](https://github.com/arjunhaanak/skincare_ai_nexus)
[![Platform](https://img.shields.io/badge/Support-Desktop_%26_Mobile-10b981?style=for-the-badge&logo=pwa)](https://github.com/arjunhaanak/skincare_ai_nexus)

Skincare AI Nexus is a premium, clinical-grade web application designed for high-precision dermatological screening. By leveraging the **VGG16 Deep Learning architecture** and a sophisticated **Doctor's Portal UI**, the system provides instant, expert-level analysis of skin conditions.

---

## 💎 Premium Clinical Features

### 🔬 Neural Diagnostic Engine
- **7-Class Classification**: Specialized detection for Melanoma, Basal Cell Carcinoma, Actinic Keratosis, and more.
- **High-Inference Speed**: Analysis pipeline optimized for <1.2s processing.
- **Clinical Pathometrics**: Provides deep medical insights including Pathophysiology, Symptom Checklists, and surgical protocols.

### 👨‍⚕️ Advanced Doctor's Portal
- **Professional Dashboard**: A side-bar driven medical interface designed for specialists.
- **AI Clinical Specialist**: Context-aware NLP chatbot for technical medical inquiries.
- **Automated Documentation**: Instant generation of professional PDF reports with clinical action plans.
- **Visual Analytics**: Interactive probability distribution charts powered by Chart.js.

### 📱 Full Device Integration (PWA)
- **Standalone App**: Install Nexus directly to your Desktop or Mobile home screen.
- **Service Worker Core**: Advanced caching for rapid load times and offline manifest support.
- **Responsive Layout**: Designed for ultra-wide clinical monitors and handheld devices.

---

## 🛠️ Technical Architecture

| Layer | Technology |
| :--- | :--- |
| **Core Engine** | Python 3.x, Flask |
| **Neural Logic** | TensorFlow 2.x, Keras, VGG16 |
| **Database** | MySQL / SQLAlchemy |
| **Frontend** | Vanilla CSS3 (Modern Medical Design), JavaScript (ES6+), Bootstrap 5 |
| **Imaging** | OpenCV, NumPy, DICOM-compatible processing |

---

## 🚀 Rapid Deployment

### 1. Database Initialization
1. Ensure **MySQL** is active (WAMP/XAMPP/Docker).
2. Create database: `skincare_nexus`.
3. Import `database.sql` to initialize schema.

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/arjunhaanak/skincare_ai_nexus.git

# Install dependencies
pip install -r requirements.txt

# Start the Clinical Portal
python app.py
```
Portal active at: `http://127.0.0.1:5001`

---

## 📊 AI Model Training
To retrain the neural core on a custom clinical dataset:
1. Populate `data/skin_diseases/` with labeled folders.
2. Execute: `python train_model.py`
3. Resulting model saved to `models/skin_model.h5`.

---

## ⚖️ Clinical Disclaimer
*The analysis provided by Skincare AI Nexus is for educational and screening purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment by a board-certified dermatologist.*

---
**Created for Clinical Excellence.**
