import asyncio
import os
import json
import sqlite3
import logging
import io
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from groq import AsyncGroq

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as OAuthCreds
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from pypdf import PdfReader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("Critical: Tokens not found in .env")

def check_candidate_exists(tg_id, vacancy_title):
    conn = sqlite3.connect("hr_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM candidates WHERE tg_id = ? AND vacancy = ?", (tg_id, vacancy_title))
    result = cursor.fetchone()
    conn.close()
    return result

SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = None
if os.path.exists('token.json'):
    creds = OAuthCreds.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

drive_service = build('drive', 'v3', credentials=creds)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

class HRState(StatesGroup):
    waiting_for_cv = State()

def get_dynamic_vacancy_keyboard():
    conn = sqlite3.connect("hr_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM vacancies")
    vacancies_data = cursor.fetchall()
    conn.close()
    
    keyboard_buttons = []
    for vac_id, title in vacancies_data:
        keyboard_buttons.append([InlineKeyboardButton(text=f"📂 {title}", callback_data=f"job_{vac_id}")])
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    try:
        kb = get_dynamic_vacancy_keyboard()
        if not kb.inline_keyboard:
            await message.answer("📭 No open positions at the moment. Please check back later.")
            return
            
        await message.answer(
            "Welcome to the AI Recruitment System! 📂\n\n"
            "Step 1: Select the position you are applying for:",
            reply_markup=kb
        )
    except sqlite3.OperationalError:
        await message.answer("🔧 System is initializing. Please start the dashboard first.")

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚫 Action cancelled. Type /start to see vacancies again.")

@dp.callback_query(F.data.startswith("job_"))
async def handle_vacancy_selection(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        vac_id = int(call.data.replace("job_", ""))
        
        conn = sqlite3.connect("hr_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT title, requirements FROM vacancies WHERE id = ?", (vac_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            await call.message.edit_text("❌ This position has been closed.")
            return
            
        chosen_vacancy, requirements = result
        
        if check_candidate_exists(call.from_user.id, chosen_vacancy):
            await call.message.edit_text(f"⚠️ You have already applied for **{chosen_vacancy}**.\n\nType /start to choose another position.")
            return
        
        await state.update_data(vacancy=chosen_vacancy, requirements=requirements)
        await state.set_state(HRState.waiting_for_cv)
        
        await call.message.edit_text(
            f"🎯 **Selected Position:** {chosen_vacancy}\n\n"
            f"Step 2: Please upload your CV in PDF format.\n\n"
            f"*(Sent the wrong one? Type /cancel)*"
        )
    except Exception as e:
        logging.error(f"Callback Error: {e}")
        await call.message.answer("❌ Internal error occurred.")

@dp.message(F.document, HRState.waiting_for_cv)
async def handle_pdf(message: Message, state: FSMContext):
    user_data = await state.get_data()
    target_vacancy = user_data.get("vacancy")
    
    if check_candidate_exists(message.from_user.id, target_vacancy):
        await message.answer("⚠️ Application already exists for this role.")
        await state.clear()
        return

    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("❌ Please upload a valid PDF file.")
        return

    requirements_str = user_data.get("requirements", "")
    req_list = [r.strip() for r in requirements_str.split(',') if r.strip()]

    processing_msg = await message.answer("⏳ Processing your document via AI... Please wait.")

    local_pdf_path = message.document.file_name

    try:
        pdf_file = await bot.get_file(message.document.file_id)
        await bot.download_file(pdf_file.file_path, local_pdf_path)

        # БРОНЕБІЙНЕ ЧИТАННЯ PDF З МЕНЕДЖЕРОМ ПАМ'ЯТІ (Fix для Windows)
        resume_text = ""
        with open(local_pdf_path, "rb") as pdf_file_obj:
            reader = PdfReader(pdf_file_obj)
            for i, page in enumerate(reader.pages):
                try:
                    extracted = page.extract_text()
                    if extracted:
                        resume_text += extracted + " "
                except Exception as page_error:
                    logging.warning(f"Skipped page {i} due to internal PDF error: {page_error}")
                
        resume_text = resume_text.replace("\n", " ")

        if not resume_text.strip():
            await processing_msg.edit_text("❌ Failed to extract text from the PDF. The file might be scanned or corrupted.")
            if os.path.exists(local_pdf_path):
                os.remove(local_pdf_path)
            await state.clear()
            return

        DYNAMIC_PROMPT = f"""You are an expert technical parser.
        Extract candidate data for the role: {target_vacancy}.
        
        Return ONLY a JSON object. Format:
        {{
            "name": "Full Name",
            "skills": ["Skill1", "Skill2", "Skill3"],
            "english_level": "B2"
        }}"""

        response = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": DYNAMIC_PROMPT},
                {"role": "user", "content": f"Resume Text:\n{resume_text}"}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            temperature=0.1
        )

        try:
            data = json.loads(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"JSON Parse Error: {e}")
            data = {"name": "Unknown", "skills": [], "english_level": "Unknown"}

        extracted_skills_str = ", ".join(data.get("skills", []))
        resume_lower = resume_text.lower()
        
        match_count = 0
        for req in req_list:
            if req.lower() in resume_lower or any(req.lower() in s.lower() for s in data.get("skills", [])):
                match_count += 1
                
        match_percentage = int((match_count / len(req_list)) * 100) if req_list else 100
        
        if match_percentage >= 60:
            verdict = f"✅ RECOMMENDED ({match_percentage}% Match)"
        else:
            verdict = f"❌ REJECTED ({match_percentage}% Match)"

        drive_file_link = "Not Saved (Rejected)"

        if "✅" in verdict:
            folder_metadata = {'name': data.get('name', 'Unknown_Candidate'), 'mimeType': 'application/vnd.google-apps.folder'}
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')

            # Читаємо файл в оперативну пам'ять і одразу закриваємо доступ до диска
            with open(local_pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            media = MediaIoBaseUpload(io.BytesIO(pdf_bytes), mimetype='application/pdf')
            uploaded_file = drive_service.files().create(
                body={'name': local_pdf_path, 'parents': [folder_id]}, 
                media_body=media, fields='webViewLink'
            ).execute()

            drive_service.permissions().create(fileId=folder_id, body={'type': 'anyone', 'role': 'reader'}).execute()
            drive_file_link = uploaded_file.get('webViewLink')

        conn = sqlite3.connect("hr_database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO candidates (tg_id, name, vacancy, skills, match_score, english, verdict, drive_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (message.from_user.id, data.get('name'), target_vacancy, extracted_skills_str, match_percentage, data.get('english_level'), verdict, drive_file_link))
        conn.commit()
        conn.close()

        applicant_report = (
            f"✅ **Documents successfully submitted!**\n\n"
            f"Thank you, your application for **{target_vacancy}** is registered.\n"
            f"HR will review your profile shortly."
        )

        await processing_msg.edit_text(applicant_report, parse_mode="Markdown")
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
        await state.clear()

    except Exception as e:
        logging.error(f"Global PDF Error: {e}")
        await processing_msg.edit_text("❌ Technical error occurred during processing. Please try again later.")
        if os.path.exists(local_pdf_path):
            try:
                os.remove(local_pdf_path)
            except:
                pass
        await state.clear()

async def main():
    logging.info("HR Engine v8.0 (Final Architecture) started.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())