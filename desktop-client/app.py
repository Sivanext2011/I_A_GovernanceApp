"""
Desktop Client - Missing Savings & Pending Feedback Mail Sender
Connects to backend API and sends mails via local Outlook (win32com).
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
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

    def get_missing_savings(self, team="Overall"):
        r = requests.get(f"{self.base}/governance/missing-savings", params={"team": team}, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_pending_feedback(self, team="Overall"):
        r = requests.get(f"{self.base}/governance/pending-feedback", params={"team": team}, timeout=30)
        r.raise_for_status()
        return r.json()

    def get_teams(self):
        r = requests.get(f"{self.base}/dashboard/teams", timeout=10)
        r.raise_for_status()
        return r.json()["teams"]


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


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Governance Mail Client")
        self.root.geometry("1100x700")
        self.api = APIClient(API_BASE)
        self.records = []
        self.selected = set()

        self._build_ui()
        self._load_teams()

    def _build_ui(self):
        # Top frame - controls
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Team:").pack(side=tk.LEFT)
        self.team_var = tk.StringVar(value="Overall")
        self.team_combo = ttk.Combobox(top, textvariable=self.team_var, width=20, state="readonly")
        self.team_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="View:").pack(side=tk.LEFT, padx=(20, 0))
        self.view_var = tk.StringVar(value="Missing Savings")
        self.view_combo = ttk.Combobox(top, textvariable=self.view_var, values=["Missing Savings", "Pending Feedback"], width=20, state="readonly")
        self.view_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Fetch Data", command=self._fetch_data).pack(side=tk.LEFT, padx=10)

        # Action buttons
        btn_frame = ttk.Frame(top)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Preview Selected", command=self._preview_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Send Selected", command=self._send_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Send All", command=self._send_all).pack(side=tk.LEFT, padx=2)

        # Table
        cols = ("select", "name", "email", "department", "count", "manager")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("select", text="✓")
        self.tree.heading("name", text="Name")
        self.tree.heading("email", text="Email")
        self.tree.heading("department", text="Department")
        self.tree.heading("count", text="Items")
        self.tree.heading("manager", text="Manager CC")
        self.tree.column("select", width=30, anchor=tk.CENTER)
        self.tree.column("name", width=200)
        self.tree.column("email", width=250)
        self.tree.column("department", width=150)
        self.tree.column("count", width=60, anchor=tk.CENTER)
        self.tree.column("manager", width=250)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, padding=5).pack(fill=tk.X, side=tk.BOTTOM)

    def _load_teams(self):
        try:
            teams = self.api.get_teams()
            self.team_combo["values"] = teams
        except Exception:
            self.team_combo["values"] = ["Overall", "Billing", "Charging", "SDC Billing&MW", "SDC CS&DFE"]

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
                    data = self.api.get_missing_savings(team)
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
            # Group by signum
            grouped = {}
            for rec in records:
                if rec["signum"] not in grouped:
                    grouped[rec["signum"]] = []
                grouped[rec["signum"]].append(rec)
            self.records = grouped
            for signum, items in grouped.items():
                first = items[0]
                manager_email = self._get_manager_from_mapping(signum, items)
                self.tree.insert("", tk.END, iid=signum, values=(
                    "☐", first["name"], first["email"], first["department"],
                    len(items), manager_email
                ))
        self.status_var.set(f"Loaded {len(self.tree.get_children())} records")

    def _get_manager_from_mapping(self, signum, items):
        # Manager email not in pending feedback response, return empty
        # The backend escalate endpoint handles manager lookup
        return ""

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
            messagebox.showwarning("No Selection", "Select at least one record.")
            return
        view = self.view_var.get()
        # Preview first selected in Outlook
        item_id = list(self.selected)[0]
        to, cc, subject, body = self._build_mail(item_id, view)
        if to:
            try:
                OutlookMailer.preview(to, cc, subject, body)
            except Exception as e:
                messagebox.showerror("Outlook Error", str(e))

    def _send_selected(self):
        if not self.selected:
            messagebox.showwarning("No Selection", "Select at least one record.")
            return
        if not messagebox.askyesno("Confirm", f"Send mail to {len(self.selected)} recipient(s)?"):
            return
        self._send_mails(list(self.selected))

    def _send_all(self):
        all_items = list(self.tree.get_children())
        if not all_items:
            return
        if not messagebox.askyesno("Confirm", f"Send mail to ALL {len(all_items)} recipient(s)?"):
            return
        self._send_mails(all_items)

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
        messagebox.showinfo("Complete", f"Sent: {sent}\nFailed: {failed}")

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
            # Pending Feedback
            items = self.records.get(item_id, [])
            if not items or not items[0]["email"]:
                return None, None, None, None
            to = [items[0]["email"]]
            cc = []  # Manager CC handled if available
            subject = "Action Required - Pending Feedback"
            body = build_pending_feedback_html(items[0]["name"], items)
            return to, cc, subject, body

    def _show_error(self, msg):
        self.status_var.set("Error")
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
