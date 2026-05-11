"""
Desktop Client - Missing Savings & Pending Feedback Mail Sender
Connects to backend API and sends mails via local Outlook (win32com).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
        self.root.geometry("1200x750")
        self.api = APIClient(API_BASE)
        self.records = []
        self.selected = set()

        self._build_ui()
        self._load_teams()

    def _build_ui(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Mail
        mail_frame = ttk.Frame(self.notebook)
        self.notebook.add(mail_frame, text="  Mail  ")
        self._build_mail_tab(mail_frame)

        # Tab 2: Upload
        upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(upload_frame, text="  Upload Data  ")
        self._build_upload_tab(upload_frame)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, padding=5).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_mail_tab(self, parent):
        # Top frame - controls
        top = ttk.Frame(parent, padding=10)
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

        # Month filters frame
        month_frame = ttk.LabelFrame(parent, text="Month Filters (Missing Savings only)", padding=8)
        month_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        pat_row = ttk.Frame(month_frame)
        pat_row.pack(fill=tk.X, pady=2)
        ttk.Label(pat_row, text="PAT Months (activity):", width=25, anchor=tk.W).pack(side=tk.LEFT)
        self.pat_months_listbox = tk.Listbox(pat_row, selectmode=tk.MULTIPLE, height=3, exportselection=False)
        self.pat_months_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        sav_row = ttk.Frame(month_frame)
        sav_row.pack(fill=tk.X, pady=2)
        ttk.Label(sav_row, text="Savings Months (recorded):", width=25, anchor=tk.W).pack(side=tk.LEFT)
        self.savings_months_listbox = tk.Listbox(sav_row, selectmode=tk.MULTIPLE, height=3, exportselection=False)
        self.savings_months_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(month_frame, text="Clear Month Filters", command=self._clear_month_filters).pack(anchor=tk.W, pady=(5, 0))

        # Action buttons row
        btn_frame = ttk.Frame(parent, padding=(10, 0, 10, 5))
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Deselect All", command=self._deselect_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(btn_frame, text="Preview", command=self._preview_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Send Selected", command=self._send_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Send All", command=self._send_all).pack(side=tk.LEFT, padx=2)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y)
        ttk.Button(btn_frame, text="⚠ Escalate Selected", command=self._escalate_selected).pack(side=tk.LEFT, padx=2)

        # Table
        cols = ("select", "name", "email", "department", "count", "manager")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="extended")
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

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5, side=tk.LEFT)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT, pady=5)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

    def _build_upload_tab(self, parent):
        frame = ttk.Frame(parent, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Upload Datasets to Backend", font=("", 14, "bold")).pack(pady=(0, 20))

        files = [
            ("PAT File", "pat", "PAT Details sheet"),
            ("Mapping File", "mapping", "Export sheet"),
            ("Savings File", "savings", "Savings - Line Manager sheet"),
            ("Download File", "download", "Pending feedback data"),
        ]

        self.upload_labels = {}
        for label, file_type, desc in files:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=8)
            ttk.Label(row, text=f"{label}:", width=15, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Label(row, text=f"({desc})", foreground="gray").pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(row, text="Browse & Upload", command=lambda ft=file_type, lb=label: self._upload_file(ft, lb)).pack(side=tk.LEFT, padx=5)
            status_lbl = ttk.Label(row, text="", foreground="green")
            status_lbl.pack(side=tk.LEFT, padx=10)
            self.upload_labels[file_type] = status_lbl

        ttk.Separator(frame).pack(fill=tk.X, pady=20)
        ttk.Button(frame, text="Check Upload Status", command=self._check_upload_status).pack()

        self.upload_status_text = tk.Text(frame, height=6, width=60, state=tk.DISABLED)
        self.upload_status_text.pack(pady=10)

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
            # Group by signum
            grouped = {}
            for rec in records:
                if rec["signum"] not in grouped:
                    grouped[rec["signum"]] = []
                grouped[rec["signum"]].append(rec)
            self.records = grouped
            for signum, items in grouped.items():
                first = items[0]
                self.tree.insert("", tk.END, iid=signum, values=(
                    "☐", first["name"], first["email"], first["department"],
                    len(items), ""
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
            messagebox.showwarning("No Selection", "Select at least one record.")
            return
        view = self.view_var.get()
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

    def _escalate_selected(self):
        """Escalate: send mail to manager with list of their defaulting team members."""
        if not self.selected:
            messagebox.showwarning("No Selection", "Select at least one record to escalate.")
            return
        if not messagebox.askyesno("Confirm Escalation", f"Escalate {len(self.selected)} record(s) to their manager(s)?"):
            return

        view = self.view_var.get()
        escalation_type = "missing_savings" if view == "Missing Savings" else "pending_feedback"

        # Group selected by manager
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
                # Get manager from tree values
                vals = self.tree.item(item_id, "values")
                mgr_email = vals[5] if len(vals) > 5 and vals[5] else ""
                # If no manager in table, try API
                if not mgr_email:
                    # Skip if no manager info available
                    continue
                if mgr_email not in manager_groups:
                    manager_groups[mgr_email] = {"mgr_name": "", "members": []}
                detail = f"{len(items)} overdue feedback items"
                manager_groups[mgr_email]["members"].append({
                    "name": items[0]["name"], "email": items[0]["email"], "detail": detail
                })

        if not manager_groups:
            messagebox.showwarning("No Managers", "Could not find manager emails for selected records.")
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
        messagebox.showinfo("Escalation Complete", f"Sent to {sent} manager(s)\nFailed: {failed}")

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
            items = self.records.get(item_id, [])
            if not items or not items[0]["email"]:
                return None, None, None, None
            to = [items[0]["email"]]
            cc = []
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
        messagebox.showerror("Upload Error", error)

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
            f"PAT:      {'✓ Loaded' if status['pat'] else '✗ Not loaded'} ({status['pat_rows']} rows)",
            f"Mapping:  {'✓ Loaded' if status['mapping'] else '✗ Not loaded'} ({status['mapping_rows']} rows)",
            f"Savings:  {'✓ Loaded' if status['savings'] else '✗ Not loaded'} ({status['savings_rows']} rows)",
            f"Download: {'✓ Loaded' if status['download'] else '✗ Not loaded'} ({status['download_rows']} rows)",
        ]
        self.upload_status_text.insert(tk.END, "\n".join(lines))
        self.upload_status_text.config(state=tk.DISABLED)

    def _show_error(self, msg):
        self.status_var.set("Error")
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
