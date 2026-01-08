# New file: core/report.py
from datetime import datetime

class Report:
    def __init__(self, id, reporter_username, subject, content, status="New"):
        self.id = id
        self.reporter_username = reporter_username
        self.subject = subject
        self.content = content
        self.status = status
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")