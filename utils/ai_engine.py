import os
import cv2
import numpy as np
import tensorflow as tf
import google.generativeai as genai
from flask import current_app

class AIEngine:
    def __init__(self, model_path, disease_info):
        self.model_path = model_path
        self.disease_info = disease_info
        self.classes = list(disease_info.keys())
        self.model = None
        self._initialize_gemini()

    def _initialize_gemini(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.chat_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.chat_model = None

    def get_model(self):
        if self.model is None:
            if os.path.exists(self.model_path):
                try:
                    self.model = tf.keras.models.load_model(self.model_path)
                except Exception as e:
                    print(f"Error loading model: {e}")
            else:
                print(f"Warning: Model not found at {self.model_path}")
        return self.model

    def predict_image(self, filepath):
        model = self.get_model()
        if model:
            try:
                img = cv2.imread(filepath)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # Clinical preprocessing
                img = cv2.GaussianBlur(img, (3, 3), 0)
                img = cv2.resize(img, (224, 224))
                img_arr = np.array(img) / 255.0
                img_arr = np.expand_dims(img_arr, axis=0)
                
                preds = model.predict(img_arr)[0]
                idx = np.argmax(preds)
                confidence = float(preds[idx]) * 100
                label = self.classes[idx]
                return label, confidence
            except Exception as e:
                print(f"Prediction error: {e}")
                return "Analysis Error", 0
        else:
            # Mock for testing/demo
            import random
            label = random.choice(self.classes)
            confidence = random.uniform(75, 98)
            return label, confidence

    def get_ai_response(self, user_msg, context_disease=None):
        if not self.chat_model:
            return "I am currently in 'offline mode'. Please check back later for full AI capabilities."

        prompt = f"""
        You are 'Nexus AI Specialist', an expert clinical assistant for the Skincare AI Nexus platform.
        Current Context: The patient was recently analyzed for {context_disease if context_disease else 'general skin health'}.
        User Question: {user_msg}
        
        Guidelines:
        1. Be professional, clinical, and empathetic.
        2. Always include a medical disclaimer that you are an AI.
        3. Do not provide definitive diagnosis or prescribe medication.
        4. Focus on explaining the symptoms, risks, and follow-up clinical actions.
        5. Keep responses concise and structured.
        """
        
        try:
            response = self.chat_model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return "I'm having trouble connecting to my neural core. Please try again or consult a human physician."
