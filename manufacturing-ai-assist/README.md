
# Manufacturing AI Assist

Conversational assistant + persona workflows for **Sales AE**, **Supply Chain Manager**, and **Plant Manager**.
Includes a small simulation API so actions update KPIs.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### Start services
Terminal A — API
```bash
export MFG_API_URL=http://localhost:8000
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```
Terminal B — UI
```bash
streamlit run streamlit_app.py
```
