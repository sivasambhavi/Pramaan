## Pramaan

### Run the backend (FastAPI + Uvicorn)

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt

uvicorn app.main:app --app-dir backend --reload
```

The API will be available at `http://127.0.0.1:8000` (docs at `/docs`).

### Run the frontend (Streamlit)

In a separate terminal, from the project root:

```bash
source .venv/bin/activate  # reuse the same venv
streamlit run frontend/app.py
```

Streamlit will open in your browser (usually `http://localhost:8501`).
