# Automation Savings Governance & Monetization Analytics Platform

Enterprise-grade web application for tracking automation savings, governance compliance, and monetization analytics.

## Architecture

```
backend/          FastAPI + pandas + MSAL + reportlab
frontend/         React + TypeScript + TailwindCSS + Plotly.js
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Azure AD App Registration (for Graph API features)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
copy .env.example .env       # Edit with your Azure credentials
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:5173 and proxies API calls to the backend.

### Docker Deployment

```bash
docker-compose up --build
```

Access at http://localhost (frontend) and http://localhost:8000/api/docs (API docs).

## Azure App Registration

1. Go to Azure Portal → Azure Active Directory → App registrations
2. New registration:
   - Name: `Automation Savings Governance`
   - Supported account types: Single tenant
   - Redirect URI: Leave blank (device code flow)
3. Under Authentication:
   - Enable "Allow public client flows" = Yes
4. Under API Permissions, add:
   - Microsoft Graph → Delegated:
     - `User.Read`
     - `User.ReadBasic.All`
     - `Mail.Send`
5. Copy Application (client) ID and Directory (tenant) ID to `.env`

## Features

| Feature | Description |
|---------|-------------|
| Missing Savings Governance | Identifies practitioners with PAT activities but no savings |
| Pending Feedback | Tracks overdue feedback with escalation |
| Monetization Analytics | Executive KPI dashboard with YTD calculations |
| Leaderboard | Top practitioners with photo integration |
| Exports | Excel, PDF, and PNG chart exports |
| Mail Automation | Outlook reminders via Graph API |
| Multi-team Analytics | Filter by Billing, Charging, SDC teams |

## API Documentation

Once running, visit http://localhost:8000/api/docs for interactive Swagger UI.

## File Upload Requirements

| File | Sheet Name | Key Fields |
|------|-----------|------------|
| PAT | PAT Details | PAT ID, Activity Status, Automation Assisted, Department, Practitioner |
| Mapping | Export | Month, Corporate ID, Emp Name, Ericsson Email Address, Billability Hours, Level 6 |
| Savings | Savings - Line Manager | Signum, Feedback Date Month, Automation Saving, Reuse Saving, L4ORG, L5ORG, L6ORG |
| Download | (first sheet) | Feedback Id, Asset Name, Signum, Download Date, Due Date, Overdue Duration, L4ORG, L5ORG, L6ORG |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_CLIENT_ID` | Azure AD Application (client) ID |
| `AZURE_TENANT_ID` | Azure AD Directory (tenant) ID |
| `DEBUG` | Enable debug logging (true/false) |
