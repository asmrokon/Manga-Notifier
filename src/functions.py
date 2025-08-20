from datetime import datetime
import re
from pathlib import Path
from csv import DictReader, DictWriter

from feedparser import parse
from winotify import Notification, audio
import requests
from bs4 import BeautifulSoup


# Function to add manga
def extract_name_from_url(url):
    if url == "":
        return False, "Enter a link before pressing Add."
    if "myanimelist.net" not in url and "mangaupdates.com" not in url:
        return False, "Error: Please enter a valid site link."
    if "manga" not in url and "series" not in url:
        return False, "Error: Please enter a valid manga link."

    try:
        reqs = requests.get(url).text
    except requests.exceptions.MissingSchema:
        return False, "Failed: URL is Invalid"
    except requests.exceptions.ConnectionError:
        return False, "Could not fetch – check your connection."

    html = BeautifulSoup(reqs, "html.parser")  # type: ignore
    if "myanimelist.net" in url:
        try:
            manga_title, garbages = html.find("title").get_text().strip().split(" |")  # type: ignore
        except ValueError:
            return False, "Could not get manga title. Please check the link."
    elif "mangaupdates.com" in url:
        try:
            manga_title, garbages = html.find("title").get_text().strip().split("- MangaUpdates")  # type: ignore
        except ValueError:
            return False, "Could not get manga title. Please check the link."
    if "(" in manga_title:  # type: ignore
        name, again_garbages = manga_title.split("(")  # type: ignore
        with open(
            str(Path("csv_files/manga_list.csv").resolve()), "a", newline=""
        ) as f:
            if check(name.strip(), "manga_list"):
                return False, f"{name} already in the list"
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": name.strip()})  # type: ignore
        return True, name.strip()

    else:
        with open(
            str(Path("csv_files/manga_list.csv").resolve()), "a", newline=""
        ) as f:
            if check(manga_title.strip(), "manga_list"):  # type: ignore
                return False, f"{name} already in the list"  # type: ignore
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": manga_title.strip()})  # type: ignore
        return True, manga_title.strip()  # type: ignore


# Display manga in the scrollable frame
def get_rows_from_csv(file_name):
    with open(str(Path(f"csv_files/{file_name}").resolve()), "r") as f:
        rows = list(DictReader(f))
        return rows


# Check Manga feed after every 3 minutes
def check_rss_feed():
    html = parse("https://www.mangaupdates.com/rss")
    time = datetime.now().strftime("%H:%M %d %B")
    rows = get_rows_from_csv("manga_list.csv")
    to_be_notified = []
    for row in rows:
        if check(row["name"], "notification"):
            for entry in html.entries:
                if row["name"].lower() in str(entry.title).lower():
                    send_notification(row["name"])
                    with open(
                        str(Path("csv_files/notifications.csv").resolve()),
                        "a",
                        newline="",
                    ) as f:
                        writer = DictWriter(f, ["name", "last_alerted"])
                        writer.writerow({"name": row["name"], "last_alerted": time})
                        to_be_notified.append({"name": row["name"], "time": time})
    if len(to_be_notified) >= 1:
        return to_be_notified


def send_notification(name):
    toast = Notification(
        app_id="Manga Notifier",
        title=f"New {name} Chapter Released!",
        msg=f"{name} just dropped a new chapter! Time to read!",
        duration="long",
        icon=str(Path("images/logo_transparent.png").resolve()),
    )
    toast.set_audio(audio.Reminder, loop=False)
    toast.show()


def check(name, mode):
    if mode.lower() == "notification":
        with open(str(Path("csv_files/notifications.csv").resolve()), "r") as f:
            rows = list(DictReader(f))
            notification_names = []
        for row in rows:
            notification_names.append(row["name"].lower())
        if name.lower() in notification_names:
            for row in rows[::-1]:
                if name.lower() == row["name"].lower():
                    last_alerted = re.search(
                        r"(?P<hour>\d{1,2}):(?P<min>\d{1,2})\s+(?P<date>\d{1,2})\s+(?P<month>[A-Za-z]+)",
                        row["last_alerted"],
                    )
                    if last_alerted:
                        diff = time_difference(
                            2025,
                            last_alerted.group("month"),
                            last_alerted.group("date"),
                            last_alerted.group("hour"),
                            last_alerted.group("min"),
                        )
                        if diff > 2:
                            return True
                        else:
                            return False
        else:
            return True
    elif mode.lower() == "manga_list":
        with open(str(Path("csv_files/manga_list.csv").resolve()), "r") as f:
            names = []
            for row in list(DictReader(f)):
                names.append(row["name"].lower())
        if name.lower() in names:
            return True
        else:
            return False


def time_difference(last_year, last_month, last_date, last_hour, last_min):
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    last_alerted_time = datetime(
        int(last_year),
        months[f"{last_month.lower()}"],
        int(last_date),
        int(last_hour),
        int(last_min),
    )
    now = datetime.now()
    duration = now - last_alerted_time
    return duration.days
