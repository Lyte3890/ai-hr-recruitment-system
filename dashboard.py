import streamlit as st
import sqlite3
import pandas as pd

# Налаштування сторінки
st.set_page_config(page_title="AI HR Dashboard", page_icon="🧠", layout="wide")

def get_connection():
    return sqlite3.connect("hr_database.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Таблиця вакансій
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            requirements TEXT NOT NULL
        )
    """)
    # Таблиця кандидатів (Зверни увагу: tg_id більше НЕ UNIQUE)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,  
            name TEXT,
            vacancy TEXT,
            skills TEXT,
            match_score INTEGER,
            english TEXT,
            verdict TEXT,
            drive_link TEXT
        )
    """)
    conn.commit()
    conn.close()

# Ініціалізуємо базу при запуску
init_db()

st.title("🧠 AI Recruitment System Dashboard")
st.markdown("Automated candidate tracking and resume analysis.")

tab1, tab2 = st.tabs(["👥 Candidates Pipeline", "📝 Manage Vacancies"])

# ================= TAB 1: CANDIDATES =================
with tab1:
    st.subheader("Candidate Submissions")
    
    conn = get_connection()
    df = pd.read_sql_query("SELECT name, vacancy, match_score, english, verdict, skills, drive_link FROM candidates ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No candidates have applied yet. Add vacancies and share the bot link!")
    else:
        # Перейменовуємо колонки для красивого відображення
        display_df = df.rename(columns={
            "name": "Candidate Name",
            "vacancy": "Applied Role",
            "match_score": "Match Score (%)",
            "english": "English Level",
            "verdict": "AI Verdict",
            "skills": "Extracted Skills",
            "drive_link": "Resume (Drive)"
        })
        
        # Відображення таблиці з налаштуваннями колонок
        st.dataframe(
            display_df,
            column_config={
                "Resume (Drive)": st.column_config.LinkColumn("Open PDF"),
                "Match Score (%)": st.column_config.ProgressColumn(
                    "Match Score (%)", 
                    format="%d%%", 
                    min_value=0, 
                    max_value=100
                ),
                "AI Verdict": st.column_config.TextColumn("AI Verdict", width="medium")
            },
            hide_index=True,
            width="stretch"  # Фікс тієї самої помилки use_container_width
        )

# ================= TAB 2: VACANCIES =================
with tab2:
    col_form, col_list = st.columns([1, 1])
    
    with col_form:
        st.subheader("Add New Vacancy")
        with st.form("new_vacancy_form"):
            v_title = st.text_input("Job Title (e.g., Senior Python Developer)")
            v_reqs = st.text_area("Core Requirements (comma-separated, e.g., Python, SQL, Docker)")
            submitted = st.form_submit_button("Create Vacancy", use_container_width=True)
            
            if submitted:
                if v_title.strip() and v_reqs.strip():
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO vacancies (title, requirements) VALUES (?, ?)", (v_title.strip(), v_reqs.strip()))
                    conn.commit()
                    conn.close()
                    st.success(f"Vacancy '{v_title}' created successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields.")

    with col_list:
        st.subheader("Active Vacancies")
        conn = get_connection()
        vac_df = pd.read_sql_query("SELECT id, title, requirements FROM vacancies", conn)
        conn.close()
        
        if vac_df.empty:
            st.info("No active vacancies.")
        else:
            for index, row in vac_df.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{row['title']}**")
                        st.caption(f"Requirements: {row['requirements']}")
                    with col2:
                        if st.button("❌", key=f"del_{row['id']}", help="Delete vacancy"):
                            conn = get_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM vacancies WHERE id = ?", (row['id'],))
                            # Також видаляємо кандидатів, які подавалися на цю вакансію, щоб тримати базу чистою
                            cursor.execute("DELETE FROM candidates WHERE vacancy = ?", (row['title'],))
                            conn.commit()
                            conn.close()
                            st.rerun()