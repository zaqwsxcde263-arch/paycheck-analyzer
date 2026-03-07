"""Application configuration."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "paycheck.db"))
DEFAULT_CURRENCY = "USD"
AVAILABLE_CURRENCIES = ["USD", "RUB", "BYN", "EUR", "JPY"]
