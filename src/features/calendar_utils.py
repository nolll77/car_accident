import datetime
import pandas as pd


def get_french_holidays(year: int) -> list[datetime.date]:
    """Return list of French public holidays for a given year.
    Fixed: 1/1, 1/5, 8/5, 14/7, 15/8, 1/11, 11/11, 25/12
    Variable: Easter Monday, Ascension (Easter+39 days)
    Use the anonymous Gregorian computus algorithm for Easter."""

    holidays = [
        datetime.date(year, 1, 1),
        datetime.date(year, 5, 1),
        datetime.date(year, 5, 8),
        datetime.date(year, 7, 14),
        datetime.date(year, 8, 15),
        datetime.date(year, 11, 1),
        datetime.date(year, 11, 11),
        datetime.date(year, 12, 25),
    ]

    # Computus for Easter
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    month = (h + el - 7 * m + 114) // 31
    day = ((h + el - 7 * m + 114) % 31) + 1

    easter_sunday = datetime.date(year, month, day)
    easter_monday = easter_sunday + datetime.timedelta(days=1)
    ascension = easter_sunday + datetime.timedelta(days=39)

    holidays.extend([easter_monday, ascension])

    return sorted(holidays)


def is_ferie(date: datetime.date) -> bool:
    """Check if a date is a French public holiday."""
    if not isinstance(date, datetime.date) or pd.isna(date):
        return False
    holidays = get_french_holidays(date.year)
    return date in holidays


def is_vacances_scolaires(date: datetime.date, zone: str = "C") -> bool:
    """Approximate French school holidays. Use simplified rules:
    - Toussaint: last week of October + first week of November
    - Noël: last 2 weeks of December
    - Hiver: 2 weeks in February (varies by zone)
    - Printemps: 2 weeks in April (varies by zone)
    - Été: July 5 - August 31
    """
    if not isinstance(date, datetime.date) or pd.isna(date):
        return False

    m, d = date.month, date.day

    # Toussaint: last week of October + first week of November
    if (m == 10 and d >= 25) or (m == 11 and d <= 7):
        return True

    # Noël: last 2 weeks of December
    if m == 12 and d >= 18:
        return True

    # Hiver: 2 weeks in February (approximate as mid-Feb)
    if m == 2 and 10 <= d <= 24:
        return True

    # Printemps: 2 weeks in April (approximate as mid-April)
    if m == 4 and 10 <= d <= 24:
        return True

    # Été: July 5 - August 31
    if (m == 7 and d >= 5) or m == 8:
        return True

    return False
