# Kite - AI Recruitment Platform

Kite is an advanced AI-powered recruitment platform designed to streamline the hiring process. It features automated AI interviews, real-time candidate evaluation, and a comprehensive organization dashboard.

## 🚀 Key Features

### 🤖 AI-Driven Interviews
- **Smart Task Generation**: Automatically analyzes Job Descriptions to generate relevant Technical and HR challenges.
- **Roles Support**: Specialized questions for Web Development (Django, React), Mobile (Flutter, Android), AI/ML, DevOps, QA, and more.
- **Sequential Mock Chat**: A robust fallback system that simulates an AI interviewer ensures candidates always get a structured interview experience, even if external APIs are unreachable.

### 📊 Real-Time Scoring & Analytics
- **Instant Evaluation**: Candidates are scored immediately after completing tasks.
- **Dashboard Integration**: "AI Score" is visible on the Candidate Dashboard with color-coded badges.
- **Organization Controls**: Recruiters can manually advance candidates or review detailed interview logs.

### 🛡️ Security & Stability
- **Session Isolation**: Supports concurrent sessions for Recruiters (e.g., on 127.0.0.1) and Candidates (e.g., on localhost) in the same browser.
- **Robust Error Handling**: Fallback mechanisms ensure the interview flow never blocks, even if the AI service experiences downtime.
- **Secure Configuration**: API Keys and Secrets are strictly managed via environment variables.

## 🛠️ Technology Stack
- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL
- **AI Integration**: Google Gemini API
- **Frontend**: Tailwind CSS, HTML5, JavaScript
- **Task Queue**: Celery (Configuration ready)

## ⚙️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rahul-1A44/Kite.git
   cd Kite
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory:
   ```ini
   GEMINI_API_KEY="your_api_key_here"
   EMAIL_HOST_USER="your_email@gmail.com"
   EMAIL_HOST_PASSWORD="your_app_password"
   KHALTI_SECRET_KEY="your_khalti_secret"
   ```

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start Server**
   ```bash
   python manage.py runserver
   ```
