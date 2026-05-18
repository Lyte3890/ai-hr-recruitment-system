# 🧠 AI HR Recruitment System (B2B Edition)

An automated, decoupled recruitment system powered by AI. This project replaces manual resume screening with an intelligent pipeline that extracts data from CVs, calculates match percentages against job requirements, and organizes successful candidates in a cloud-based CRM and Google Drive.

## 🎥 System Demonstration (How It Works)

<details>
<summary><b>🎬 Click to expand and watch the AI Core & Dashboard in action!</b></summary>
<br>

### 🤖 Telegram Bot Interface (Candidate Side)
![Bot Demo](https://github.com/user-attachments/assets/8ee284ea-c96c-4445-b768-3306ab6cc220)

### 📊 Streamlit Web CMS (HR Management Side)
![Dashboard Demo](https://github.com/user-attachments/assets/efa490ac-e2b2-4157-b727-e42ef80d024d)

</details>

---

## 🌟 Architecture & Key Features

This system follows a **Decoupled Architecture**, separating the user-facing application from the management interface.

* **Microservice A (Input Layer):** An asynchronous Telegram Bot (`main.py`) that guides candidates through the application process and handles document uploads.
* **Microservice B (CMS Layer):** A Streamlit-based Web Dashboard (`dashboard.py`) for HR managers to create vacancies, review applicants, and track the pipeline.
* **Bulletproof PDF Parsing:** Utilizes in-memory processing (`io.BytesIO`) to prevent OS-level file locking (e.g., `WinError 32`), ensuring extreme stability even with corrupted PDF files.
* **AI Engine (Groq / Llama 3):** Extracts candidate skills, English proficiency, and outputs strictly structured JSON.
* **Automated Cloud Storage:** Directly uploads recommended CVs to Google Drive folders via OAuth 2.0 without leaving footprint files on the local server.

---

## 🛠️ Tech Stack
* **Backend:** Python 3.11/3.12
* **Asynchronous Framework:** Aiogram 3.x
* **Frontend CMS:** Streamlit & Pandas
* **Database:** SQLite3 (Local Single Source of Truth)
* **AI / LLM:** Groq API (Llama-3.3-70b-versatile)
* **Cloud Integration:** Google Drive API v3

---

## 🚀 Installation & Local Setup

**1. Clone and Prepare the Environment:**
```
git clone https://github.com/Lyte3890/ai-hr-recruitment-system.git
cd ai-hr-recruitment-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```
2. Configure API Keys:
Create a .env file in the root directory:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```
3. Configure Google Drive API:
Place your client_secret.json in the root directory. Upon the first launch, the script will prompt browser authentication and generate a token.json session file.

4. Run Locally:
Due to the decoupled nature, run services in separate terminals:

Bot: ```./run_bot.sh``` (Linux/Mac) or double-click ```RUN_BOT.bat``` (Windows)

Dashboard: ```./run_dashboard.sh``` (Linux/Mac) or double-click ```RUN_DASHBOARD.bat``` (Windows)

Server Deployment Guide (Production / VPS)

Follow these step-by-step terminal commands to connect to your remote Linux VPS (Ubuntu/Debian) and deploy the system 24/7.

1. Connect to your Server via SSH

Open your local terminal and connect to your VPS using your server's IP address:
```
ssh root@your_server_ip
```
2. Install System Dependencies

Update system packages and install git, python3-venv, and required build tools:
```
sudo apt update && sudo apt upgrade -y
sudo apt install git python3 python3-pip python3-venv build-essential -y
```
3. Clone and Initialize the Project

Navigate to the production directory, clone the repository, and build a clean virtual environment:
```
cd /opt
sudo git clone https://github.com/Lyte3890/ai-hr-recruitment-system.git
cd ai-hr-recruitment-system

# Create and activate environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```
(Remember to create your ```.env``` file using nano .env and upload your ```client_secret.json``` to this folder).

4. Configure Systemd Daemon for 24/7 Bot Operation

To ensure the Telegram bot runs continuously in the background and restarts automatically if the server reboots, configure it as a background system service.

Create a service file:
```
sudo nano /etc/systemd/system/hr_bot.service
```
Insert the following configuration:
```
[Unit]
Description=AI HR Recruitment Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/opt/ai-hr-recruitment-system
Environment="PATH=/opt/ai-hr-recruitment-system/venv/bin"
ExecStart=/opt/ai-hr-recruitment-system/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Enable and start your background service:
```
sudo systemctl daemon-reload
sudo systemctl enable hr_bot
sudo systemctl start hr_bot
```
To monitor bot server logs in real-time, use:
```
sudo journalctl -u hr_bot.service -f

```
🔗 Scaling: Beyond Telegram (Multi-Platform Integration)

The current repository uses Telegram as the primary interface. However, the core logic is designed to be platform-agnostic. To connect Slack, Discord, WhatsApp, or a Web Frontend, follow this architectural pattern:

Abstract the Core Logic: Move the AI processing, PDF parsing, Google Drive upload, and SQLite database insertion from ```main.py``` into a separate handler file (e.g.,``` hr_core.py```).

Create API Gateways: Build lightweight wrapper scripts for each platform:

``` bot_telegram.py``` (Current implementation)

 ```bot_slack.py``` (Using slack_sdk to listen for file uploads)

```pi_webhook.py``` (Using FastAPI/Flask to accept POST requests with PDF payloads from a custom website).

Unified Processing: Regardless of where the PDF comes from (Telegram, Slack, Web), the wrapper passes the file byte-stream to ```hr_core.py(process_candidate_cv)```. The CMS Dashboard (```dashboard.py``` requires zero changes, as it simply reads the unified ```hr_database.db```.
