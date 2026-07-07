# -*- coding: utf-8 -*-
"""
Desktop Client - Missing Savings & Pending Feedback Mail Sender
Connects to backend API and sends mails via local Outlook (win32com).
Modern UI with ttkbootstrap theming.
"""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tooltip import ToolTip
import tkinter as tk
from tkinter import filedialog
import requests
import threading
import win32com.client

# --- Configuration ---
API_BASE = "http://seliiuvd07044.seli.gic.ericsson.se:8000/api"
SENDER_NAME = "R. Siva"


class OutlookMailer:
    """Send mail via local Outlook."""

    @staticmethod
    def send(to: list[str], cc: list[str], subject: str, html_body: str):
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = "; ".join(to)
        if cc:
            mail.CC = "; ".join([c for c in cc if c])
        mail.Subject = subject
        mail.HTMLBody = html_body
        mail.Send()

    @staticmethod
    def preview(to: list[str], cc: list[str], subject: str, html_body: str):
        """Open mail in Outlook for review before sending."""
        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)
        mail.To = "; ".join(to)
        if cc:
            mail.CC = "; ".join([c for c in cc if c])
        mail.Subject = subject
        mail.HTMLBody = html_body
        mail.Display()


class APIClient:
    """Fetch data from backend API."""

    def __init__(self, base_url: str):
        self.base = base_url

    def get_missing_savings(self, team="Overall", pat_months=None, savings_months=None):
        params = {"team": team}
        if pat_months:
            params["pat_months"] = ",".join(pat_months)
        if savings_months:
            params["savings_months"] = ",".join(savings_months)
        r = requests.get(f"{self.base}/governance/missing-savings", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_months(self):
        r = requests.get(f"{self.base}/dashboard/months", timeout=10)
        r.raise_for_status()
        return r.json()["months"]

    def get_pending_feedback(self, team="Overall"):
        r = requests.get(f"{self.base}/governance/pending-feedback", params={"team": team}, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_teams(self):
        r = requests.get(f"{self.base}/dashboard/teams", timeout=10)
        r.raise_for_status()
        return r.json()["teams"]

    def upload_file(self, file_type: str, filepath: str):
        with open(filepath, "rb") as f:
            r = requests.post(f"{self.base}/uploads/{file_type}", files={"file": f}, timeout=60)
        r.raise_for_status()
        return r.json()

    def get_upload_status(self):
        r = requests.get(f"{self.base}/uploads/status", timeout=10)
        r.raise_for_status()
        return r.json()

    def download_doc(self, doc_type: str, save_path: str, period: str = "monthly"):
        """Download a document from the backend."""
        if doc_type == "monthly-savings":
            url = f"{self.base}/exports/docs/monthly-savings-report"
            r = requests.get(url, timeout=60, stream=True)
        else:
            url = f"{self.base}/exports/docs/asset-presentation"
            r = requests.get(url, params={"period": period}, timeout=60, stream=True)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def build_missing_savings_html(name: str, activities: list[dict]) -> str:
    rows = ""
    for act in activities:
        rows += f"<tr><td>{act['pat_id']}</td><td>{act['activity_name']}</td><td>{act['start_date']}</td><td>{act['end_date']}</td><td>{act['status']}</td></tr>"
    return f"""<p>Dear {name},</p>
<p>Our review indicates that you have completed the activities listed below and marked them as automation-assisted ("Yes") in PAT. However, the corresponding savings have not yet been recorded in N365.</p>
<p>Kindly update the savings in N365 at the earliest and confirm once completed.</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>PAT ID</th><th>Activity Name</th><th>Start Date &amp; Time</th><th>End Date &amp; Time</th><th>Activity Status</th></tr>
{rows}
</table>
<br/>
<p>Regards,<br/>{SENDER_NAME}</p>"""


def build_pending_feedback_html(name: str, items: list[dict]) -> str:
    rows = ""
    for item in items:
        rows += f"<tr><td>{item['feedback_id']}</td><td>{item.get('asset_registry_id', '')}</td><td>{item['asset_name']}</td><td>{item.get('download_date', '')}</td><td>{item['due_date']}</td><td>{item['overdue_duration']}</td></tr>"
    return f"""<p>Dear {name},</p>
<p>Below assets are pending feedback beyond due date:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>Feedback Id</th><th>Asset Registry Id</th><th>Asset Name</th><th>Download Date</th><th>Due Date</th><th>Overdue</th></tr>
{rows}
</table>
<br/>
<p>Kindly update or cancel.</p>
<p>Regards,<br/>{SENDER_NAME}</p>"""


def build_escalation_html(mgr_name: str, members: list[dict], escalation_type: str) -> str:
    issue = "missing savings submissions" if escalation_type == "missing_savings" else "pending feedback (overdue)"
    rows = ""
    for m in members:
        rows += f"<tr><td>{m['name']}</td><td>{m['email']}</td><td>{m['detail']}</td></tr>"
    return f"""<p>Dear {mgr_name},</p>
<p>This is an escalation notice. The following team member(s) have <strong>{issue}</strong> that require attention:</p>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
<tr style="background:#1F4E79;color:white;"><th>Name</th><th>Email</th><th>Details</th></tr>
{rows}
</table>
<p>Please follow up with them to ensure compliance.</p>
<p>Regards,<br/>{SENDER_NAME}</p>"""



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Governance Mail Client")
        self.root.geometry("1280x800")
        self.root.minsize(1000, 600)
        self.api = APIClient(API_BASE)
        self.records = []
        self.selected = set()

        # Apply custom styles
        self.style = ttk.Style()
        self._configure_styles()
        self._build_ui()
        self._load_teams()

    def _configure_styles(self):
        """Configure custom widget styles for a polished look."""
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 11))
        self.style.configure("Card.TFrame", relief="flat")
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=30,
        )
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        # Header bar
        header = ttk.Frame(self.root, bootstyle="primary")
        header.pack(fill=X, side=TOP)
        ttk.Label(
            header, text="  📧  Governance Mail Client",
            font=("Segoe UI", 14, "bold"),
            bootstyle="inverse-primary",
        ).pack(side=LEFT, padx=10, pady=8)
        ttk.Label(
            header, text="Automation Savings & Pending Feedback  ",
            font=("Segoe UI", 9),
            bootstyle="inverse-primary",
        ).pack(side=RIGHT, padx=10, pady=8)

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=(10, 5))

        # Tab 1: Mail
        mail_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(mail_frame, text="  📬  Mail  ")
        self._build_mail_tab(mail_frame)

        # Tab 2: Upload
        upload_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(upload_frame, text="  📁  Upload Data  ")
        self._build_upload_tab(upload_frame)

        # Tab 3: Downloads
        download_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(download_frame, text="  ⬇  Downloads  ")
        self._build_download_tab(download_frame)

        # Status bar
        status_frame = ttk.Frame(self.root, bootstyle="secondary")
        status_frame.pack(fill=X, side=BOTTOM)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            status_frame, textvariable=self.status_var,
            font=("Segoe UI", 9), bootstyle="inverse-secondary",
        ).pack(side=LEFT, padx=10, pady=4)

    def _build_mail_tab(self, parent):
        # Top controls in a card-like frame
        controls = ttk.Labelframe(parent, text="Controls", bootstyle="info", padding=12)
        controls.pack(fill=X, pady=(0, 8))

        row1 = ttk.Frame(controls)
        row1.pack(fill=X, pady=(0, 8))

        ttk.Label(row1, text="Team:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.team_var = tk.StringVar(value="Overall")
        self.team_combo = ttk.Combobox(
            row1, textvariable=self.team_var, width=22,
            state="readonly", bootstyle="info"
        )
        self.team_combo.pack(side=LEFT, padx=(5, 20))

        ttk.Label(row1, text="View:", font=("Segoe UI", 10)).pack(side=LEFT)
        self.view_var = tk.StringVar(value="Missing Savings")
        self.view_combo = ttk.Combobox(
            row1, textvariable=self.view_var,
            values=["Missing Savings", "Pending Feedback"],
            width=22, state="readonly", bootstyle="info"
        )
        self.view_combo.pack(side=LEFT, padx=5)

        fetch_btn = ttk.Button(
            row1, text="🔄  Fetch Data", command=self._fetch_data,
            bootstyle="success", width=14
        )
        fetch_btn.pack(side=LEFT, padx=(20, 0))
        ToolTip(fetch_btn, text="Fetch governance data from backend")

        # Month filters
        month_frame = ttk.Labelframe(parent, text="Month Filters (Missing Savings only)", bootstyle="secondary", padding=10)
        month_frame.pack(fill=X, pady=(0, 8))

        filters_row = ttk.Frame(month_frame)
        filters_row.pack(fill=X)
        filters_row.columnconfigure(1, weight=1)
        filters_row.columnconfigure(3, weight=1)

        ttk.Label(filters_row, text="PAT Months:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky=W, padx=(0, 5))
        self.pat_months_listbox = tk.Listbox(
            filters_row, selectmode=tk.MULTIPLE, height=3,
            exportselection=False, font=("Segoe UI", 9),
            relief="flat", highlightthickness=1
        )
        self.pat_months_listbox.grid(row=0, column=1, sticky=EW, padx=(0, 20))

        ttk.Label(filters_row, text="Savings Months:", font=("Segoe UI", 9)).grid(row=0, column=2, sticky=W, padx=(0, 5))
        self.savings_months_listbox = tk.Listbox(
            filters_row, selectmode=tk.MULTIPLE, height=3,
            exportselection=False, font=("Segoe UI", 9),
            relief="flat", highlightthickness=1
        )
        self.savings_months_listbox.grid(row=0, column=3, sticky=EW)

        ttk.Button(
            month_frame, text="Clear Filters", command=self._clear_month_filters,
            bootstyle="secondary-outline", width=14
        ).pack(anchor=W, pady=(8, 0))

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=X, pady=(0, 8))

        ttk.Button(btn_frame, text="☑ Select All", command=self._select_all, bootstyle="outline", width=12).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="☐ Deselect", command=self._deselect_all, bootstyle="outline", width=12).pack(side=LEFT, padx=2)
        ttk.Separator(btn_frame, orient=VERTICAL, bootstyle="secondary").pack(side=LEFT, padx=10, fill=Y, pady=2)
        ttk.Button(btn_frame, text="👁 Preview", command=self._preview_selected, bootstyle="info", width=10).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📤 Send Selected", command=self._send_selected, bootstyle="success", width=14).pack(side=LEFT, padx=2)
        ttk.Button(btn_frame, text="📤 Send All", command=self._send_all, bootstyle="success-outline", width=10).pack(side=LEFT, padx=2)
        ttk.Separator(btn_frame, orient=VERTICAL, bootstyle="secondary").pack(side=LEFT, padx=10, fill=Y, pady=2)
        ttk.Button(btn_frame, text="⚠ Escalate", command=self._escalate_selected, bootstyle="danger", width=12).pack(side=LEFT, padx=2)

        # Treeview table
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)

        cols = ("select", "name", "email", "department", "count", "manager")
        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            selectmode="extended", bootstyle="primary"
        )
        self.tree.heading("select", text="✓")
        self.tree.heading("name", text="Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("department", text="Department")
        self.tree.heading("count", text="Items")
        self.tree.heading("manager", text="Manager CC")
        self.tree.column("select", width=35, anchor=CENTER)
        self.tree.column("name", width=180)
        self.tree.column("email", width=240)
        self.tree.column("department", width=140)
        self.tree.column("count", width=60, anchor=CENTER)
        self.tree.column("manager", width=240)

        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview, bootstyle="primary-round")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill=BOTH, expand=True, side=LEFT)
        scrollbar.pack(fill=Y, side=RIGHT)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)


    def _build_upload_tab(self, parent):
        # Header
        ttk.Label(
            parent, text="Upload Datasets to Backend",
            style="Header.TLabel"
        ).pack(pady=(10, 5))
        ttk.Label(
            parent, text="Select and upload Excel files to the backend for processing",
            style="Subheader.TLabel", foreground="gray"
        ).pack(pady=(0, 20))

        files = [
            ("PAT File", "pat", "PAT Details sheet", "info"),
            ("Mapping File", "mapping", "Export sheet", "primary"),
            ("Savings File", "savings", "Savings - Line Manager sheet", "success"),
            ("Download File", "download", "Pending feedback data", "warning"),
        ]

        self.upload_labels = {}
        for label, file_type, desc, color in files:
            card = ttk.Frame(parent, padding=12)
            card.pack(fill=X, pady=4)

            ttk.Label(card, text=f"📄  {label}", font=("Segoe UI", 10, "bold")).pack(side=LEFT)
            ttk.Label(card, text=f"  ({desc})", font=("Segoe UI", 9), foreground="gray").pack(side=LEFT, padx=(0, 15))

            status_lbl = ttk.Label(card, text="", font=("Segoe UI", 9))
            status_lbl.pack(side=RIGHT, padx=10)
            self.upload_labels[file_type] = status_lbl

            ttk.Button(
                card, text="Browse & Upload",
                command=lambda ft=file_type, lb=label: self._upload_file(ft, lb),
                bootstyle=color, width=16
            ).pack(side=RIGHT, padx=5)

        ttk.Separator(parent, bootstyle="secondary").pack(fill=X, pady=20)

        status_section = ttk.Labelframe(parent, text="Backend Status", bootstyle="info", padding=12)
        status_section.pack(fill=X)

        ttk.Button(
            status_section, text="🔍  Check Upload Status",
            command=self._check_upload_status, bootstyle="info-outline"
        ).pack(anchor=W, pady=(0, 10))

        self.upload_status_text = tk.Text(
            status_section, height=5, width=60,
            state=tk.DISABLED, font=("Consolas", 10),
            relief="flat", padx=10, pady=8
        )
        self.upload_status_text.pack(fill=X)

    def _build_download_tab(self, parent):
        """Tab for downloading reports from backend."""
        ttk.Label(
            parent, text="Download Reports",
            style="Header.TLabel"
        ).pack(pady=(10, 5))
        ttk.Label(
            parent, text="Download the latest reports from the backend server",
            style="Subheader.TLabel", foreground="gray"
        ).pack(pady=(0, 30))

        # --- Excel Report ---
        excel_card = ttk.Labelframe(parent, text="  Monthly Savings Report  ", bootstyle="success", padding=16)
        excel_card.pack(fill=X, pady=8)

        info_row = ttk.Frame(excel_card)
        info_row.pack(fill=X, pady=(0, 10))
        ttk.Label(info_row, text="📊  Monthly_Savings_Report.xlsx", font=("Segoe UI", 10, "bold")).pack(side=LEFT)
        ttk.Label(info_row, text="Consolidated monthly savings data across all teams", font=("Segoe UI", 9), foreground="gray").pack(side=LEFT, padx=(15, 0))

        excel_btn_row = ttk.Frame(excel_card)
        excel_btn_row.pack(fill=X)
        self.excel_dl_label = ttk.Label(excel_btn_row, text="", font=("Segoe UI", 9))
        self.excel_dl_label.pack(side=RIGHT, padx=10)
        ttk.Button(
            excel_btn_row, text="⬇  Download Excel Report",
            command=self._download_excel_report,
            bootstyle="success", width=28
        ).pack(side=LEFT)

        # --- PPT Report with period selection ---
        ppt_card = ttk.Labelframe(parent, text="  Asset Presentation  ", bootstyle="warning", padding=16)
        ppt_card.pack(fill=X, pady=8)

        info_row2 = ttk.Frame(ppt_card)
        info_row2.pack(fill=X, pady=(0, 10))
        ttk.Label(info_row2, text="📑  Asset Presentation (PowerPoint)", font=("Segoe UI", 10, "bold")).pack(side=LEFT)
        ttk.Label(info_row2, text="Asset analytics presentation", font=("Segoe UI", 9), foreground="gray").pack(side=LEFT, padx=(15, 0))

        period_row = ttk.Frame(ppt_card)
        period_row.pack(fill=X, pady=(0, 10))
        ttk.Label(period_row, text="Period:", font=("Segoe UI", 10)).pack(side=LEFT, padx=(0, 8))
        self.ppt_period_var = tk.StringVar(value="monthly")
        period_combo = ttk.Combobox(
            period_row, textvariable=self.ppt_period_var,
            values=["monthly", "quarterly", "half-yearly", "year-end"],
            state="readonly", width=18, bootstyle="warning"
        )
        period_combo.pack(side=LEFT)

        ppt_btn_row = ttk.Frame(ppt_card)
        ppt_btn_row.pack(fill=X)
        self.ppt_dl_label = ttk.Label(ppt_btn_row, text="", font=("Segoe UI", 9))
        self.ppt_dl_label.pack(side=RIGHT, padx=10)
        ttk.Button(
            ppt_btn_row, text="⬇  Download Presentation",
            command=self._download_ppt_report,
            bootstyle="warning", width=28
        ).pack(side=LEFT)

    def _load_teams(self):
        try:
            teams = self.api.get_teams()
            self.team_combo["values"] = teams
        except Exception:
            self.team_combo["values"] = ["Overall", "Billing", "Charging", "SDC Billing&MW", "SDC CS&DFE"]
        self._load_months()

    def _load_months(self):
        try:
            months = self.api.get_months()
            self.pat_months_listbox.delete(0, tk.END)
            self.savings_months_listbox.delete(0, tk.END)
            for m in months:
                self.pat_months_listbox.insert(tk.END, m)
                self.savings_months_listbox.insert(tk.END, m)
        except Exception:
            pass

    def _clear_month_filters(self):
        self.pat_months_listbox.selection_clear(0, tk.END)
        self.savings_months_listbox.selection_clear(0, tk.END)

    def _get_selected_pat_months(self) -> list[str]:
        return [self.pat_months_listbox.get(i) for i in self.pat_months_listbox.curselection()]

    def _get_selected_savings_months(self) -> list[str]:
        return [self.savings_months_listbox.get(i) for i in self.savings_months_listbox.curselection()]


    def _fetch_data(self):
        self.status_var.set("Fetching data...")
        self.tree.delete(*self.tree.get_children())
        self.records = []
        self.selected = set()

        def fetch():
            try:
                team = self.team_var.get()
                view = self.view_var.get()
                if view == "Missing Savings":
                    pat_months = self._get_selected_pat_months()
                    savings_months = self._get_selected_savings_months()
                    data = self.api.get_missing_savings(team, pat_months or None, savings_months or None)
                else:
                    data = self.api.get_pending_feedback(team)
                self.root.after(0, lambda: self._populate(data, view))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=fetch, daemon=True).start()

    def _populate(self, data, view):
        records = data.get("records", [])
        if view == "Missing Savings":
            self.records = records
            for rec in records:
                self.tree.insert("", tk.END, iid=rec["signum"], values=(
                    "☐", rec["name"], rec["email"], rec["department"],
                    rec["pat_count"], rec.get("manager_email", "")
                ))
        else:
            grouped = {}
            for rec in records:
                if rec["signum"] not in grouped:
                    grouped[rec["signum"]] = []
                grouped[rec["signum"]].append(rec)
            self.records = grouped
            for signum, items in grouped.items():
                first = items[0]
                manager_email = first.get("manager_email", "")
                self.tree.insert("", tk.END, iid=signum, values=(
                    "☐", first["name"], first["email"], first["department"],
                    len(items), manager_email
                ))
        self.status_var.set(f"Loaded {len(self.tree.get_children())} records")

    def _on_tree_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        if item in self.selected:
            self.selected.discard(item)
            vals = list(self.tree.item(item, "values"))
            vals[0] = "☐"
            self.tree.item(item, values=vals)
        else:
            self.selected.add(item)
            vals = list(self.tree.item(item, "values"))
            vals[0] = "☑"
            self.tree.item(item, values=vals)
        self.status_var.set(f"{len(self.selected)} selected")

    def _select_all(self):
        for item in self.tree.get_children():
            self.selected.add(item)
            vals = list(self.tree.item(item, "values"))
            vals[0] = "☑"
            self.tree.item(item, values=vals)
        self.status_var.set(f"{len(self.selected)} selected")

    def _deselect_all(self):
        for item in self.tree.get_children():
            self.selected.discard(item)
            vals = list(self.tree.item(item, "values"))
            vals[0] = "☐"
            self.tree.item(item, values=vals)
        self.status_var.set("0 selected")


    def _preview_selected(self):
        if not self.selected:
            Messagebox.show_warning("Select at least one record.", "No Selection")
            return
        view = self.view_var.get()
        item_id = list(self.selected)[0]
        to, cc, subject, body = self._build_mail(item_id, view)
        if to:
            try:
                OutlookMailer.preview(to, cc, subject, body)
            except Exception as e:
                Messagebox.show_error(str(e), "Outlook Error")

    def _send_selected(self):
        if not self.selected:
            Messagebox.show_warning("Select at least one record.", "No Selection")
            return
        result = Messagebox.yesno(f"Send mail to {len(self.selected)} recipient(s)?", "Confirm Send")
        if result != "Yes":
            return
        self._send_mails(list(self.selected))

    def _send_all(self):
        all_items = list(self.tree.get_children())
        if not all_items:
            return
        result = Messagebox.yesno(f"Send mail to ALL {len(all_items)} recipient(s)?", "Confirm Send All")
        if result != "Yes":
            return
        self._send_mails(all_items)

    def _escalate_selected(self):
        """Escalate: send mail to manager with list of their defaulting team members."""
        if not self.selected:
            Messagebox.show_warning("Select at least one record to escalate.", "No Selection")
            return
        result = Messagebox.yesno(f"Escalate {len(self.selected)} record(s) to their manager(s)?", "Confirm Escalation")
        if result != "Yes":
            return

        view = self.view_var.get()
        escalation_type = "missing_savings" if view == "Missing Savings" else "pending_feedback"

        manager_groups: dict[str, dict] = {}

        for item_id in self.selected:
            if view == "Missing Savings":
                rec = next((r for r in self.records if r["signum"] == item_id), None)
                if not rec:
                    continue
                mgr_email = rec.get("manager_email", "")
                if not mgr_email:
                    continue
                if mgr_email not in manager_groups:
                    manager_groups[mgr_email] = {"mgr_name": "", "members": []}
                detail = f"{rec['pat_count']} PAT activities, 0 savings"
                manager_groups[mgr_email]["members"].append({
                    "name": rec["name"], "email": rec["email"], "detail": detail
                })
            else:
                items = self.records.get(item_id, [])
                if not items:
                    continue
                vals = self.tree.item(item_id, "values")
                mgr_email = vals[5] if len(vals) > 5 and vals[5] else ""
                if not mgr_email:
                    continue
                if mgr_email not in manager_groups:
                    manager_groups[mgr_email] = {"mgr_name": "", "members": []}
                detail = f"{len(items)} overdue feedback items"
                manager_groups[mgr_email]["members"].append({
                    "name": items[0]["name"], "email": items[0]["email"], "detail": detail
                })

        if not manager_groups:
            Messagebox.show_warning("Could not find manager emails for selected records.", "No Managers")
            return

        def do_escalate():
            sent = 0
            failed = 0
            for mgr_email, data in manager_groups.items():
                mgr_name = mgr_email.split("@")[0].replace(".", " ").title()
                body = build_escalation_html(mgr_name, data["members"], escalation_type)
                subject = f"Escalation: Team Members with {escalation_type.replace('_', ' ').title()}"
                try:
                    OutlookMailer.send([mgr_email], [], subject, body)
                    sent += 1
                except Exception:
                    failed += 1
            self.root.after(0, lambda: self._escalate_complete(sent, failed))

        self.status_var.set("Sending escalation mails...")
        threading.Thread(target=do_escalate, daemon=True).start()

    def _escalate_complete(self, sent, failed):
        self.status_var.set(f"Escalation done. Sent: {sent}, Failed: {failed}")
        Messagebox.show_info(f"Sent to {sent} manager(s)\nFailed: {failed}", "Escalation Complete")

    def _send_mails(self, item_ids):
        view = self.view_var.get()
        sent = 0
        failed = 0

        def do_send():
            nonlocal sent, failed
            for item_id in item_ids:
                to, cc, subject, body = self._build_mail(item_id, view)
                if not to:
                    failed += 1
                    continue
                try:
                    OutlookMailer.send(to, cc, subject, body)
                    sent += 1
                except Exception:
                    failed += 1
            self.root.after(0, lambda: self._send_complete(sent, failed))

        self.status_var.set("Sending mails...")
        threading.Thread(target=do_send, daemon=True).start()

    def _send_complete(self, sent, failed):
        self.status_var.set(f"Done. Sent: {sent}, Failed: {failed}")
        Messagebox.show_info(f"Sent: {sent}\nFailed: {failed}", "Complete")

    def _build_mail(self, item_id, view):
        if view == "Missing Savings":
            rec = next((r for r in self.records if r["signum"] == item_id), None)
            if not rec or not rec["email"]:
                return None, None, None, None
            to = [rec["email"]]
            cc = [rec.get("manager_email", "")] if rec.get("manager_email") else []
            subject = "Action Required - Savings needs to be recorded in N365"
            body = build_missing_savings_html(rec["name"], rec.get("pat_activities", []))
            return to, cc, subject, body
        else:
            items = self.records.get(item_id, [])
            if not items or not items[0]["email"]:
                return None, None, None, None
            to = [items[0]["email"]]
            cc = [items[0].get("manager_email", "")] if items[0].get("manager_email") else []
            subject = "Action Required - Pending Feedback"
            body = build_pending_feedback_html(items[0]["name"], items)
            return to, cc, subject, body


    def _upload_file(self, file_type, label):
        filepath = filedialog.askopenfilename(
            title=f"Select {label}",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filepath:
            return
        self.status_var.set(f"Uploading {label}...")

        def do_upload():
            try:
                result = self.api.upload_file(file_type, filepath)
                self.root.after(0, lambda: self._upload_success(file_type, result))
            except Exception as e:
                self.root.after(0, lambda: self._upload_error(file_type, str(e)))

        threading.Thread(target=do_upload, daemon=True).start()

    def _upload_success(self, file_type, result):
        rows = result.get("rows_loaded", 0)
        self.upload_labels[file_type].config(text=f"✓ {rows} rows loaded", foreground="green")
        self.status_var.set(f"Upload successful: {rows} rows")

    def _upload_error(self, file_type, error):
        self.upload_labels[file_type].config(text=f"✗ Failed", foreground="red")
        self.status_var.set("Upload failed")
        Messagebox.show_error(error, "Upload Error")

    def _check_upload_status(self):
        def fetch():
            try:
                status = self.api.get_upload_status()
                self.root.after(0, lambda: self._show_upload_status(status))
            except Exception as e:
                self.root.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=fetch, daemon=True).start()

    def _show_upload_status(self, status):
        self.upload_status_text.config(state=tk.NORMAL)
        self.upload_status_text.delete("1.0", tk.END)
        lines = [
            f"  PAT:      {'✓ Loaded' if status['pat'] else '✗ Not loaded'}  ({status['pat_rows']} rows)",
            f"  Mapping:  {'✓ Loaded' if status['mapping'] else '✗ Not loaded'}  ({status['mapping_rows']} rows)",
            f"  Savings:  {'✓ Loaded' if status['savings'] else '✗ Not loaded'}  ({status['savings_rows']} rows)",
            f"  Download: {'✓ Loaded' if status['download'] else '✗ Not loaded'}  ({status['download_rows']} rows)",
        ]
        self.upload_status_text.insert(tk.END, "\n".join(lines))
        self.upload_status_text.config(state=tk.DISABLED)

    def _download_excel_report(self):
        """Download Monthly Savings Report from backend."""
        save_path = filedialog.asksaveasfilename(
            title="Save Monthly Savings Report",
            initialfile="Monthly_Savings_Report.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if not save_path:
            return
        self.status_var.set("Downloading Monthly Savings Report...")
        self.excel_dl_label.config(text="⏳ Downloading...", foreground="orange")

        def do_download():
            try:
                self.api.download_doc("monthly-savings", save_path)
                self.root.after(0, lambda: self._excel_download_success(save_path))
            except Exception as e:
                self.root.after(0, lambda: self._excel_download_error(str(e)))

        threading.Thread(target=do_download, daemon=True).start()

    def _excel_download_success(self, save_path):
        self.excel_dl_label.config(text="✓ Downloaded", foreground="green")
        self.status_var.set(f"Downloaded to: {save_path}")

    def _excel_download_error(self, error):
        self.excel_dl_label.config(text="✗ Failed", foreground="red")
        self.status_var.set("Download failed")
        Messagebox.show_error(error, "Download Error")

    def _download_ppt_report(self):
        """Download Asset Presentation for selected period."""
        period = self.ppt_period_var.get()
        filename = f"Asset_{period.replace('-', '_').title()}.pptx"
        save_path = filedialog.asksaveasfilename(
            title=f"Save Asset Presentation ({period})",
            initialfile=filename,
            defaultextension=".pptx",
            filetypes=[("PowerPoint files", "*.pptx"), ("All files", "*.*")]
        )
        if not save_path:
            return
        self.status_var.set(f"Downloading Asset Presentation ({period})...")
        self.ppt_dl_label.config(text="⏳ Downloading...", foreground="orange")

        def do_download():
            try:
                self.api.download_doc("asset-ppt", save_path, period)
                self.root.after(0, lambda: self._ppt_download_success(save_path))
            except Exception as e:
                self.root.after(0, lambda: self._ppt_download_error(str(e)))

        threading.Thread(target=do_download, daemon=True).start()

    def _ppt_download_success(self, save_path):
        self.ppt_dl_label.config(text="✓ Downloaded", foreground="green")
        self.status_var.set(f"Downloaded to: {save_path}")

    def _ppt_download_error(self, error):
        self.ppt_dl_label.config(text="✗ Failed", foreground="red")
        self.status_var.set("Download failed")
        Messagebox.show_error(error, "Download Error")

    def _show_error(self, msg):
        self.status_var.set("Error")
        Messagebox.show_error(msg, "Error")


if __name__ == "__main__":
    app = ttk.Window(
        title="Governance Mail Client",
        themename="cosmo",
        size=(1280, 800),
        minsize=(1000, 600),
    )
    App(app)
    app.mainloop()
