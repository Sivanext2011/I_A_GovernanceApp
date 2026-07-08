# Desktop Mail Client

Windows desktop application for sending governance mails via local Outlook. Connects to the backend API for data and uses `win32com` to send through your configured Outlook account — no Graph API token needed.

## Setup

```bash
cd desktop-client
pip install -r requirements.txt
```

## Configuration

Edit `API_BASE` in `app.py` to point to your backend:
```python
API_BASE = "http://seliiuvd07044.seli.gic.ericsson.se:3000/api"
```

## Run

```bash
python app.py
```

Or double-click `GovernanceMailClient.bat` on your desktop.

## Requirements
- Windows with Outlook installed and configured
- Network access to the backend API
- Python 3.10+
- pywin32, requests

## Features

### Mail Tab
- **Team filter**: Select Overall, Billing, Charging, SDC Billing&MW, SDC CS&DFE
- **View toggle**: Missing Savings / Pending Feedback
- **Month filters**: PAT Months (activity period) and Savings Months (recorded period) — for Missing Savings only
- **Select All / Deselect All**: Bulk selection
- **Preview**: Opens first selected mail in Outlook for review
- **Send Selected**: Sends mail to selected practitioners via Outlook
- **Send All**: Sends to all listed practitioners
- **Escalate Selected**: Sends escalation mail to managers with defaulter list
- **Manager CC**: Automatically CC's the line manager (from mapping data)

### Upload Tab
- Upload PAT, Mapping, Savings, Download files to the backend
- Check upload status

### Mail Templates

#### Missing Savings
- **To**: Practitioner
- **CC**: Line Manager
- **Subject**: Action Required - Savings needs to be recorded in N365
- **Body**: PAT activity table

#### Pending Feedback
- **To**: Practitioner
- **CC**: Line Manager
- **Subject**: Action Required - Pending Feedback
- **Body**: Overdue feedback table

#### Escalation
- **To**: Manager
- **Subject**: Escalation: Team Members with [type]
- **Body**: Table of defaulting team members

## Troubleshooting

- **"Outlook.Application" error**: Ensure Outlook is installed and you've opened it at least once
- **Connection refused**: Check that the backend is running and accessible from your network
- **No data**: Upload datasets via the Upload tab or web frontend first
