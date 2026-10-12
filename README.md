# 💸 Expense Tracker (Streamlit)

Structure
- `backend.py` – Budget / User classes + JSON storage (your original logic)
- `app.py` – Streamlit frontend
- `requirements.txt`, `.streamlit/config.toml`

Run locally
    pip install -r requirements.txt
    streamlit run app.py

Deploy free on Streamlit Community Cloud
1. Push this folder to a GitHub repo (keep `app.py` at the root).
2. Go to share.streamlit.io -> New app -> pick the repo, branch, `app.py`.
3. Click Deploy -> you get a public link.

Note: on Streamlit Cloud the disk resets when the app restarts/redeploys,
so JSON data can be lost. For permanent data, swap Storage for a database
(SQLite on a persistent host, Supabase, or Google Sheets).
