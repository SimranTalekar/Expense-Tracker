"""
Expense Tracker - Backend
-------------------------
Same logic as the original CLI version (Budget / User classes, JSON storage,
categories, total + category-wise spending) but with NO input()/print(),
so any UI (Streamlit, Flask, CLI...) can use it.

Improvements over the CLI version:
  * Budget is saved (it was lost on exit before)
  * Each expense gets an ID so it can be deleted
  * Per-user data files, so a public link doesn't mix everyone's data
  * Safe (atomic) file writes + validation
  * Old expense_tracker.json (plain list) files are auto-migrated
"""

import json
import os
import re
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(os.getenv("EXPENSE_DATA_DIR", "data"))
DATE_FORMAT = "%d/%m/%Y"  # DD/MM/YYYY, same as your original

CATEGORIES = {
    "Food": "🍔",
    "Transport": "🚌",
    "Rent": "🏠",
    "Education": "📚",
    "Shopping": "🛍️",
    "Others": "🧾",
}


def _safe_name(name: str) -> str:
    """Turn a username into a safe filename."""
    cleaned = re.sub(r"[^a-z0-9_-]", "", (name or "").strip().lower())
    return cleaned[:30] or "guest"


class Storage:
    """Loads/saves one user's data in data/<username>.json"""

    def __init__(self, username: str = "guest"):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path = DATA_DIR / f"{_safe_name(username)}.json"
        self.data = self._load()

    def _load(self) -> dict:
        default = {"budget": 0, "expenses": []}
        if not self.path.exists():
            return default
        try:
            content = self.path.read_text(encoding="utf-8")
            raw = json.loads(content) if content.strip() else default
        except (json.JSONDecodeError, OSError):
            return default

        # Migrate old format: a plain list of expenses
        if isinstance(raw, list):
            raw = {"budget": 0, "expenses": raw}

        raw.setdefault("budget", 0)
        raw.setdefault("expenses", [])
        for exp in raw["expenses"]:
            exp.setdefault("ID", uuid.uuid4().hex[:8])
        return raw

    def save(self) -> None:
        # Write to a temp file first, then swap -> no corrupted JSON on crash
        fd, tmp = tempfile.mkstemp(dir=DATA_DIR, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)
        os.replace(tmp, self.path)


class Budget:
    """Monthly budget (was: input() inside __init__)."""

    def __init__(self, storage: Storage):
        self.storage = storage

    @property
    def budget(self) -> int:
        return int(self.storage.data.get("budget", 0))

    def set_budget(self, amount: int) -> None:
        amount = int(amount)
        if amount < 0:
            raise ValueError("Budget cannot be negative.")
        self.storage.data["budget"] = amount
        self.storage.save()


class User(Budget):
    """All expense operations."""

    @property
    def expenses(self) -> list:
        return self.storage.data["expenses"]

    def add_expense(self, exp_date, category: str, amount: int, description: str = "") -> dict:
        if isinstance(exp_date, (date, datetime)):
            exp_date = exp_date.strftime(DATE_FORMAT)
        amount = int(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0.")
        if category not in CATEGORIES:
            category = "Others"

        expense = {
            "ID": uuid.uuid4().hex[:8],
            "Date": exp_date,
            "Category": category,
            "Amount": amount,
            "Description": description.strip(),
        }
        self.expenses.append(expense)
        self.storage.save()
        return expense

    def delete_expense(self, expense_id: str) -> bool:
        before = len(self.expenses)
        self.storage.data["expenses"] = [e for e in self.expenses if e["ID"] != expense_id]
        self.storage.save()
        return len(self.expenses) < before

    def total_spending(self) -> int:
        return sum(e["Amount"] for e in self.expenses)

    def category_spending(self) -> dict:
        """Same 6 categories as before. Unknown ones are counted under Others."""
        totals = {c: 0 for c in CATEGORIES}
        for e in self.expenses:
            cat = e["Category"].title()
            totals[cat if cat in totals else "Others"] += e["Amount"]
        return totals

    def month_spending(self, year: int, month: int) -> int:
        total = 0
        for e in self.expenses:
            try:
                d = datetime.strptime(e["Date"], DATE_FORMAT)
            except ValueError:
                continue
            if d.year == year and d.month == month:
                total += e["Amount"]
        return total

    def remaining(self) -> int:
        today = date.today()
        return self.budget - self.month_spending(today.year, today.month)
