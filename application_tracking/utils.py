import os
import re
import json
import PyPDF2
from docx import Document
import warnings

# Suppress the "FutureWarning" from google.generativeai about the package deprecation
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
from django.conf import settings

# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)

# =================================================
# 1. ROBUST AI CALLER (The Fix for 404 Errors)
# =================================================
def generate_ai_content(prompt):
    """
    Tries multiple Gemini models. Returns text if successful, None if all fail.
    This prevents the app from crashing if 'gemini-pro' is deprecated or busy.
    """
    # Priority list: Newer/Faster -> Standard -> Legacy
    models_to_try = [
        'gemini-flash-latest',   # Latest stable flash
        'gemini-pro-latest',     # Latest stable pro
        'gemini-2.0-flash-lite', # New fast model
        'gemini-1.5-flash',      # Previous default
        'gemini-1.5-pro'         # Previous pro
    ]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            # Log error but continue to next model
            print(f"Model {model_name} failed: {e}")
            continue
    
    print("All AI models failed.")
    return None

# =================================================
# 2. FILE EXTRACTION
# =================================================
def extract_text_from_file(uploaded_file):
    text = ""
    try:
        uploaded_file.seek(0)
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + " " 
        elif uploaded_file.name.endswith('.docx'):
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + " "
        else:
            text = uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error reading file: {e}")
        return ""
    
    final_text = text.replace('\n', ' ').strip()
    
    # Fix for "s p a c e d o u t" text often found in PDFs
    if len(final_text) > 50:
        words = final_text.split()
        if len(words) > 0 and (sum(len(w) for w in words) / len(words)) < 1.6:
            final_text = final_text.replace(" ", "")
    return final_text

# =================================================
# 3. MATCHING LOGIC
# =================================================
def get_match_score(resume_text, job_description):
    if not resume_text or not job_description:
        return {'score': 0, 'missing_skills': [], 'reason': "Missing data"}

    prompt = f"""
    Act as a Strict Technical Recruiter.
    JOB: {job_description[:4000]}
    RESUME: {resume_text[:4000]}
    
    RULES:
    1. If role mismatch (e.g. Chef vs Developer), score = 0.
    2. Check for missing HARD SKILLS.
    3. Return JSON ONLY.
    
    FORMAT:
    {{
        "match_score": <int>,
        "missing_skills": ["skill1", "skill2"],
        "reason": "<string>"
    }}
    """

    # Use robust caller
    content = generate_ai_content(prompt)

    if not content:
        # Fallback if AI fails completely - ensures frontend doesn't break
        return {
            'score': 0, 
            'missing_skills': ["AI Service Unavailable"], 
            'reason': "Could not connect to AI service."
        }

    try:
        # Clean JSON markdown blocks
        content = re.sub(r"```json", "", content)
        content = re.sub(r"```", "", content).strip()
        data = json.loads(content)
        return {
            'score': data.get('match_score', 0),
            'missing_skills': data.get('missing_skills', []),
            'reason': data.get('reason', 'Analysis Complete')
        }
    except:
        return {'score': 0, 'missing_skills': [], 'reason': "Error parsing AI response."}

def extract_missing_skills(resume_text, job_skills):
    """Deprecated but kept for compatibility"""
    return [] 

# =================================================
# 4. LEARNING RESOURCES (The "No Blank Page" Fix)
# =================================================
def get_learning_resources(topic):
    if not topic: return None
    
    # 1. AI Prompt
    prompt = f"""
    Act as a Learning Concierge. The user wants to learn: "{topic}".
    Provide 3 high-quality FREE resources for each category.
    
    JSON ONLY. EXACT KEYS: "videos", "articles", "books".
    
    EXAMPLE:
    {{
        "videos": [{{ "title": "{topic} Crash Course", "channel": "YouTube", "link": "https://youtube.com/..." }}],
        "articles": [{{ "title": "{topic} Documentation", "source": "Official Docs", "link": "https://..." }}],
        "books": [{{ "title": "Mastering {topic}", "author": "Expert", "link": "https://..." }}]
    }}
    """
    
    # 2. Try AI Generation
    content = generate_ai_content(prompt)
    
    if content:
        try:
            content = re.sub(r"```json", "", content)
            content = re.sub(r"```", "", content).strip()
            return json.loads(content)
        except Exception as e:
            print(f"JSON Parse Error: {e}")

    # 3. FAIL-SAFE FALLBACK 
    # This block GUARANTEES the user sees results even if the AI is down/404.
    print(f"AI failed for topic '{topic}'. Using Fallback Generators.")
    
    # Encode topic for URLs
    topic_enc = topic.replace(" ", "+")
    
    return {
        "videos": [
            {"title": f"Learn {topic} - Full Course", "channel": "YouTube Search", "link": f"https://www.youtube.com/results?search_query={topic_enc}+course"},
            {"title": f"{topic} for Beginners", "channel": "YouTube Search", "link": f"https://www.youtube.com/results?search_query={topic_enc}+tutorial"},
            {"title": f"Advanced {topic} Concepts", "channel": "YouTube Search", "link": f"https://www.youtube.com/results?search_query={topic_enc}+advanced"}
        ],
        "articles": [
            {"title": f"Official {topic} Documentation", "source": "Google Search", "link": f"https://www.google.com/search?q={topic_enc}+documentation"},
            {"title": f"Getting Started with {topic}", "source": "Google Search", "link": f"https://www.google.com/search?q={topic_enc}+tutorial"}
        ],
        "books": [
            {"title": f"Best Books for {topic}", "author": "Amazon Search", "link": f"https://www.amazon.com/s?k={topic_enc}+book"},
            {"title": f"Google Books: {topic}", "author": "Google Books", "link": f"https://www.google.com/search?tbm=bks&q={topic_enc}"}
        ]
    }