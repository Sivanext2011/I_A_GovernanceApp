# Desktop Mail Client

Windows desktop app that fetches Missing Savings & Pending Feedback data from the backend API and sends mails via local Outlook.

## Setup

```bash
cd desktop-client
pip install -r requirements.txt
```

## Configuration

Edit `API_BASE` in `app.py` to point to your backend:
```python
API_BASE = "http://seliiuvd07044.seli.gic.ericsson.se:8000/api"
```

## Run

```bash
python app.py
```

## Requirements
- Windows with Outlook installed and configured
- Network access to the backend API
- Python 3.10+

## Features
- Fetch Missing Savings / Pending Feedback from backend
- Select individual or all practitioners
- Preview mail in Outlook before sending
- Send to selected or all
- CC to line manager (Missing Savings)
- Mail format matches the governance templates
