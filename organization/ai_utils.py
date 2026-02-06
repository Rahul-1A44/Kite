import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_interview_questions(job_title, job_description, job_requirements, round_type):
    """
    Generates interview questions using a DIRECT API call to Google Gemini.
    This bypasses the SDK library issues (404 Model Not Found) by connecting directly.
    """
    # 1. Check for API Key
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        return "System Error: Gemini API Key not configured in settings.py."

    # 2. Select Model Endpoint (We try the newest fast model first)
    model_name = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    # 3. Construct the Prompt
    prompt_text = f"""
    You are an expert technical recruiter. Generate 3 short, specific, and professional interview questions for a candidate applying for the role of '{job_title}'.
    
    Context:
    - Job Description: {str(job_description)[:500]}...
    - Requirements: {str(job_requirements)}
    
    Current Interview Round: {round_type}
    
    Instructions:
    1. If this is the 'HR Round', focus on soft skills and culture fit.
    2. If this is the 'Technical Round', focus on specific technical skills mentioned in requirements.
    3. If this is the 'Final Round', focus on long-term goals and salary expectations.
    4. Return ONLY the numbered list of questions. Do not include introductory text.
    """

    # 4. Prepare JSON Payload
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        # 5. Send Request (Directly to Google)
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        # 6. Success Handling
        if response.status_code == 200:
            result = response.json()
            try:
                # Extract text from the nested JSON response
                return result['candidates'][0]['content']['parts'][0]['text'].strip()
            except (KeyError, IndexError):
                return "System: AI returned an empty response. Please interview manually."
        
        # 7. Fallback Handling (If 1.5-flash fails, try gemini-pro)
        else:
            print(f"⚠️ Primary Model Failed ({response.status_code}): {response.text}")
            return generate_fallback_questions(api_key, prompt_text)

    except Exception as e:
        return f"System: Connection error ({str(e)}). Please type questions manually."

def generate_fallback_questions(api_key, prompt_text):
    """
    Fallback function that tries the older 'gemini-pro' model if the new one fails.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json={
            "contents": [{"parts": [{"text": prompt_text}]}]
        }, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"❌ Fallback Failed: {e}")
        pass
        
    return "System: Could not auto-generate questions. Please type your questions below."