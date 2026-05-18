# 🚀 AI HR Recruitment Agent

An automated B2B recruitment system powered by AI. This project consists of a Telegram Bot for candidates to submit their CVs, and a Streamlit-based Web Dashboard (CMS) for HR managers to review candidates, manage job postings, and track AI-calculated match scores.

## 🌟 Key Features

* **No-Code HR Dashboard:** A clean web interface (Streamlit) for HRs to add/remove vacancies and view candidate pipelines.
* **Smart Telegram Bot:** Guides candidates through the application process dynamically based on active vacancies.
* **AI Resume Parsing:** Utilizes the Groq API (Llama-3.3-70b-versatile) to accurately extract candidate skills and English proficiency from uploaded PDFs.
* **Mathematical Scoring Core:** Calculates an objective "Match Percentage" (Intersection over Union) comparing the candidate's parsed skills against the core requirements of the job.
* **Automated Cloud Storage:** Automatically creates folders and uploads recommended CVs to Google Drive, attaching the link directly to the candidate's profile in the database.
* **Multi-Apply Support:** Allows candidates to apply for different roles, with built-in misclick protection (`/cancel`).

## 🛠️ Tech Stack

* **Backend:** Python 3.10+
* **Bot Framework:** Aiogram 3.x
* **Frontend / CMS:** Streamlit & Pandas
* **Database:** SQLite (Local Single Source of Truth)
* **AI / LLM:** Groq API
* **Integrations:** Google Drive API (OAuth 2.0), PyPDF

## 📁 Project Structure

├── main.py                 # Telegram Bot background process
├── dashboard.py            # Streamlit Web CMS
├── requirements.txt        # Python dependencies
├── START_WINDOWS.bat       # 1-click launcher for Windows
├── start.sh                # Launcher script for Linux/Mac
├── .env                    # Environment variables (Tokens)
└── client_secret.json      # Google Drive OAuth 2.0 credentials

⚙️ Setup & Installation

1. Clone the repository and navigate to the folder:
Extract the project files to your local machine.

2. Configure API Keys:
Create a .env file in the root directory and add your tokens:

TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here

3. Configure Google Drive API:
Place your client_secret.json (obtained from Google Cloud Console) in the root directory. Upon the first launch, the system will open a browser window to authenticate and generate a token.json file.
🚀 Running the System

For Windows Users:
Simply double-click the START_WINDOWS.bat file.
The script will automatically create a virtual environment, install all dependencies from requirements.txt, start the Telegram bot in the background, and open the HR Dashboard in your default browser.

For Linux / Mac Users:
Open your terminal and run:

chmod +x start.sh
./start.sh

📊 How It Works

    HR manager opens the Dashboard and creates a new vacancy, specifying the exact required skills (e.g., Python, SQL, Docker).

    The vacancy instantly becomes available as a clickable button in the Telegram Bot.

    A candidate applies and uploads their PDF resume.

    The AI parses the PDF, extracts the candidate's actual skills, and the internal mathematical core calculates a match percentage against the HR's requirements.

    If the match is >= 60%, the system flags the candidate as ✅ RECOMMENDED, uploads their CV to Google Drive, and saves all data to the local SQLite database.

    HR manager views the neatly formatted results in the Dashboard.