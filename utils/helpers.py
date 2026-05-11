"""通用工具函数"""

from datetime import datetime, date
import calendar


def format_datetime(dt_str: str | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime(fmt)
    except (ValueError, TypeError):
        return dt_str


def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_month_calendar(year: int, month: int) -> list[list[int]]:
    """返回 6 行 x 7 列的月历矩阵（含上月/下月填充 0）"""
    return calendar.monthcalendar(year, month)


def clamp(value, lo, hi):
    return max(lo, min(hi, value))
