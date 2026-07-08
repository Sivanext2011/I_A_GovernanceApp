# Automation Savings Governance & Monetization Analytics Platform

Enterprise-grade web application for tracking automation savings, governance compliance, and monetization analytics.

## Architecture

```
backend/          FastAPI + pandas + reportlab + Plotly (kaleido)
frontend/         React + TypeScript + TailwindCSS + Plotly.js
desktop-client/   Python + tkinter + win32com (Outlook integration)
```

## Quick Start

### Docker Deployment (Recommended)

```bash
git clone https://github.com/Sivanext2011/I_A_GovernanceApp.git
cd I_A_GovernanceApp

# Create persistent data directories
mkdir -p /tmp/governance-data/{uploads,exports,photos,logs}

# Create network and run containers
docker network create governance-net
docker build -t governance-backend ./backend
docker build -t governance-frontend ./frontend

docker run -d --name governance-backend --network governance-net \
  -v /tmp/governance-data/uploads:/app/uploads \
  -v /tmp/governance-data/exports:/app/exports \
  -v /tmp/governance-data/photos:/app/photos \
  -v /tmp/governance-data/logs:/app/logs \
  governance-backend

docker run -d --name governance-frontend --network governance-net -p 3000:80 governance-frontend
```

Access at `http://<hostname>:3000`

### Manual Setup (Development)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

### Desktop Client (Windows - Outlook Mail)

```bash
cd desktop-client
pip install -r requirements.txt
python app.py
```

Or double-click `GovernanceMailClient.bat` (shortcut on desktop).

## Features

### Dashboard
- Overall KPI tiles (Total Savings, Savings %, Downloads, Pending Feedback, Billability)
- Team-wise statistics table (when Overall selected)
- Monthly Savings Trend (bar chart, all teams when Overall)
- Savings % Trend (bar chart)
- Department wise Savings (Overall only)
- Downloads vs Reuse chart
- Top Practitioners Leaderboard with photos

### Missing Savings Governance
- Identifies practitioners with automation-assisted PAT activities but no savings in N365
- Collapsible practitioner list with PAT activity details
- Independent PAT month and Savings month filters
- Preview mail / Send selected / Send all / Escalate to manager
- CC to line manager on all mails
- Exclude specific PAT records (trash icon)

### Pending Feedback Governance
- Tracks overdue feedback with full details (Feedback Id, Asset Registry Id, Asset Name, Download Date, Due Date, Overdue Duration)
- Grouped by practitioner (collapsible)
- Preview / Send / Escalate options
- CC to line manager
- Exclude specific records (trash icon)

### Monetization Analytics
- Year-to-Date KPI tiles
- Current Month KPI tiles
- Monthly Savings Trend / Savings % Trend
- Department wise Savings (Overall only)
- Downloads vs Reuse
- Pending Feedback Trend (stored monthly)
- Month exclude option
- Record Pending Feedback Count button

### Leaderboard
- Top practitioners with photo integration
- Upload photo option per practitioner
- Photos stored locally and persist across restarts

### Exports
- **Excel**: KPI Summary, Team Stats, Leaderboard (top 50), Monthly Trend, Raw Savings Data
- **PDF**: Full report with charts (as images), team stats table, current month KPIs, monthly trend table, leaderboard with photos (top 30)
- **PNG**: Individual chart exports

### Settings & Data Management
- File upload (PAT, Mapping, Savings, Download)
- Auto-detection of file type by sheet name
- Auto-load on container restart (from volume mount)
- Microsoft Graph Authentication (token-based)
- **Savings Overrides**: Update Reuse/Automation Saving for specific Feedback IDs (persistent)
- **Permanent Exclusion List**: Exclude PAT IDs and Feedback IDs permanently (applied on every reload)

### Desktop Client (Windows)
- Fetches data from backend API
- Sends mail via local Outlook (win32com) — no Graph API needed
- Preview mail in Outlook before sending
- Send to selected / Send all / Escalate to manager
- CC to line manager for both Missing Savings and Pending Feedback
- Upload datasets to backend
- PAT month and Savings month filters

## Mail Templates

### Missing Savings
- **Subject**: Action Required - Savings needs to be recorded in N365
- **Body**: PAT activity table (PAT ID, Activity Name, Start/End Date, Status)
- **CC**: Line manager
- **Signed**: R. Siva

### Pending Feedback
- **Subject**: Action Required - Pending Feedback
- **Body**: Feedback table (Feedback Id, Asset Registry Id, Asset Name, Download Date, Due Date, Overdue)
- **CC**: Line manager
- **Signed**: R. Siva

### Escalation
- **Subject**: Escalation: Team Members with [Missing Savings/Pending Feedback]
- **Body**: Table of defaulting team members (Name, Email, Details)
- **To**: Manager
- **Signed**: R. Siva

## File Upload Requirements

| File | Sheet Name | Key Fields |
|------|-----------|------------|
| PAT | PAT Details | PAT ID, Activity Name, Start Date & Time, End Date & Time, Activity Status, Automation Assisted, Department, Practitioner |
| Mapping | Export | Month, Pers.no., Corporate ID, Emp Name, Ericsson Email Address, Supervisor Personal No., Billability Hours, Level 6 |
| Savings | Savings - Line Manager | Feedback Id, Signum, Feedback Date Month, Automation Saving, Reuse Saving, L4ORG, L5ORG, L6ORG |
| Download | (first sheet) | Feedback Id, Asset Registry Id, Asset Name, Signum, Download Date, Due Date, Overdue Duration, L4ORG, L5ORG, L6ORG |

## Persistent Data (Volume Mounts)

| Path | Content |
|------|---------|
| `/app/uploads` | Uploaded Excel files (auto-loaded on restart) |
| `/app/exports` | Generated PDF/Excel/PNG exports |
| `/app/photos` | Practitioner photos (JPEG) |
| `/app/logs` | Exclusion list, savings overrides, pending feedback trend, token cache |

## API Documentation

Once running, visit `http://<hostname>:8000/api/docs` for interactive Swagger UI.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/uploads/{type}` | POST | Upload dataset (pat/mapping/savings/download) |
| `/api/uploads/status` | GET | Check loaded datasets |
| `/api/uploads/exclusions` | GET/POST/DELETE | Manage permanent exclusion list |
| `/api/uploads/savings-overrides` | GET/POST/DELETE | Manage savings value overrides |
| `/api/dashboard/kpis` | GET | Get KPIs for team/months |
| `/api/dashboard/kpis/ytd` | GET | Get YTD + current month KPIs |
| `/api/dashboard/team-stats` | GET | Get all teams' KPIs |
| `/api/dashboard/charts/*` | GET | Chart data (trend, dept comparison, etc.) |
| `/api/dashboard/leaderboard` | GET | Top practitioners |
| `/api/governance/missing-savings` | GET | Non-compliant practitioners |
| `/api/governance/pending-feedback` | GET | Overdue feedback records |
| `/api/exports/excel` | GET | Download Excel report |
| `/api/exports/pdf` | GET | Download PDF report |
| `/api/exports/png` | GET | Download chart PNG |
| `/api/photos/{signum}` | GET | Get practitioner photo |
| `/api/photos/upload/{signum}` | POST | Upload practitioner photo |
| `/api/mail/missing-savings/preview` | POST | Preview missing savings mails |
| `/api/mail/missing-savings/send` | POST | Send missing savings mails |
| `/api/mail/pending-feedback/preview` | POST | Preview pending feedback mails |
| `/api/mail/pending-feedback/send` | POST | Send pending feedback mails |
| `/api/mail/escalate` | POST | Escalate to managers |

## Department Classification

Teams are classified from the mapping/savings data:
- **Billing**: BCSS BOS SER SL BOS IN BE Billing
- **Charging**: BCSS BOS SER SL BOS Monetization EC1/EC2/EC3/ECEV
- **SDC Billing&MW**: BCSS BOS SER SL BOS SDC Billing&MW
- **SDC CS&DFE**: BCSS BOS SER SL BOS SDC CS&DFE

## Rebuild Commands

```bash
# Full rebuild
cd ~/I_A_GovernanceApp && git pull
docker rm -f governance-backend governance-frontend
docker build -t governance-backend ./backend
docker build --no-cache -t governance-frontend ./frontend
docker run -d --name governance-backend --network governance-net \
  -v /tmp/governance-data/uploads:/app/uploads \
  -v /tmp/governance-data/exports:/app/exports \
  -v /tmp/governance-data/photos:/app/photos \
  -v /tmp/governance-data/logs:/app/logs \
  governance-backend
docker run -d --name governance-frontend --network governance-net -p 3000:80 governance-frontend

# Backend only
docker rm -f governance-backend
docker build -t governance-backend ./backend
docker run -d --name governance-backend --network governance-net \
  -v /tmp/governance-data/uploads:/app/uploads \
  -v /tmp/governance-data/exports:/app/exports \
  -v /tmp/governance-data/photos:/app/photos \
  -v /tmp/governance-data/logs:/app/logs \
  governance-backend

# Frontend only
docker rm -f governance-frontend
docker build --no-cache -t governance-frontend ./frontend
docker run -d --name governance-frontend --network governance-net -p 3000:80 governance-frontend
```
