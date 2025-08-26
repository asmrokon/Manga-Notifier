from datetime import datetime
from csv import DictReader, DictWriter
from os import path, remove
from io import BytesIO
from PIL import Image
from time import sleep
import sys
from threading import Thread


from winotify import Notification, audio
import requests


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS  # type: ignore
    else:
        script_dir = path.abspath(path.dirname(__file__))
        base_path = path.dirname(script_dir)

    return path.join(base_path, relative_path)


def get_csv_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        exe_dir = path.dirname(sys.executable)
        return path.join(exe_dir, relative_path)
    else:
        script_dir = path.abspath(path.dirname(__file__))
        base_path = path.dirname(script_dir)
        return path.join(base_path, relative_path)


def get_covers_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        exe_dir = path.dirname(sys.executable)
        full_path = path.join(
            exe_dir, "resources", "images", "cover_images", relative_path
        )
    else:
        script_dir = path.abspath(path.dirname(__file__))
        base_path = path.dirname(script_dir)
        full_path = path.join(
            base_path, "resources", "images", "cover_images", relative_path
        )
    return full_path


# Path to resources folder
BASE_DIR = path.abspath(path.dirname(__file__))
RESOURCES_DIR = path.join(BASE_DIR, "resources")

manga_list_csv_path = get_csv_path(
    path.join("resources", "csv_files", "manga_list.csv")
)
notifications_csv_path = get_csv_path(
    path.join("resources", "csv_files", "notifications.csv")
)
icon_img_path = get_resource_path(
    path.join("resources", "images", "app_icons", "logo_transparent.png")
)


# Gets Manga Information from Mangadex
def get_manga_data(title):
    url = "https://api.mangadex.org/manga"

    # Parameters for the request
    params = {
        "title": title,
        "limit": min(10, 10),
        "status[]": ["ongoing"],
        "includes[]": ["cover_art", "author", "artist"],
        "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
        "order[followedCount]": "desc",
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        manga_list = []
        for manga_data in data.get("data", []):
            manga_info = extract_manga_info(manga_data)
            if manga_info:
                manga_list.append(manga_info)

        return manga_list

    except Exception as e:
        print(f"Error searching manga: {e}")
        return []


# Extracts manga info from data
def extract_manga_info(manga_data):
    try:
        manga_id = manga_data["id"]
        attrs = manga_data["attributes"]
        relationships = manga_data.get("relationships", [])

        # Get title English or Japanese or 1st available title
        all_title = attrs.get("title", {})
        if "en" in all_title:
            title = all_title["en"]
        elif "ja" in all_title:
            title = all_title["ja"]
        else:
            title = list(all_title.values())[0]

        # Get authors and artists name
        authors = []
        artists = []
        cover_filename = None

        for rel in relationships:
            if rel.get("type") == "author":
                author_name = rel.get("attributes", {}).get("name")
                if author_name and author_name not in authors:
                    authors.append(author_name)
            elif rel.get("type") == "artist":
                artist_name = rel.get("attributes", {}).get("name")
                if artist_name and artist_name not in artists:
                    artists.append(artist_name)
            elif rel.get("type") == "cover_art":
                cover_filename = rel.get("attributes", {}).get("fileName")

        # Get description
        desc_obj = attrs.get("description", {})
        if "en" in desc_obj:
            description = desc_obj["en"]
        elif desc_obj:
            # Take the first available description
            description = list(desc_obj.values())[0]
        else:
            description = None

        # Build cover image URL from manga id and cover filename
        cover_url = None
        if cover_filename:
            cover_url = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_filename}.256.jpg"

        return {
            "title": title,
            "manga_id": manga_id,
            "authors": authors,
            "artists": artists,
            "description": description,
            "cover_url": cover_url,
        }

    except Exception as e:
        print(f"Error extracting manga info: {e}")
        return None


# gets latest chapter from manga_id
def get_latest_chapter(manga_id):
    try:
        url = f"https://api.mangadex.org/manga/{manga_id}/feed"
        params = {
            "limit": 1,
            "order[chapter]": "desc",
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
        }

        response = requests.get(url, params=params)
        data = response.json()

        chapters = data.get("data", [])
        if chapters:
            chapter_num = chapters[0]["attributes"].get("chapter")
            if chapter_num:
                return float(chapter_num)
            else:
                return None
        return None

    except Exception as e:
        print(f"Error getting latest chapter: {e}")
        return None


# Loads image from link
def load_image(url, callback):
    def worker():
        response = requests.get(url)
        bytes = BytesIO(response.content)
        image = Image.open(bytes)
        callback(image)

    Thread(target=worker, daemon=True).start()


# Display manga in the scrollable frame
def get_rows_from_csv(file_path):
    with open(file_path, "r") as f:
        return list(DictReader(f))


# Check Manga feed
def check_feed(callback):
    manga_list = get_rows_from_csv(manga_list_csv_path)
    to_be_notified = []

    def worker():
        for manga in manga_list:
            sleep(1)
            last_latest_chapter = manga["latest_chapter"]
            latest_chapter = get_latest_chapter(manga["manga_id"])
            if last_latest_chapter and latest_chapter:
                if float(latest_chapter) > float(last_latest_chapter):
                    to_be_notified.append(
                        {
                            "title": manga["title"],
                            "latest_chapter": latest_chapter,
                            "rel_time": datetime.now().strftime("%H:%M %d %B"),
                        }
                    )
                    update_manga_latest_chapter(manga["manga_id"], latest_chapter)
                    update_notifications_list(
                        manga["title"],
                        latest_chapter,
                        datetime.now().strftime("%H:%M %d %B"),
                    )
                    send_notification(manga["title"])
        if callback:
            callback(to_be_notified)

    Thread(target=worker, daemon=True).start()


# Update notifications.csv
def update_notifications_list(title, latest_chapter, time):
    with open(notifications_csv_path, "a", newline="") as f:
        writer = DictWriter(f, ["title", "latest_chapter", "rel_time"])
        writer.writerow(
            {"title": title, "latest_chapter": latest_chapter, "rel_time": time}
        )


# Updates manga's latest chapter info
def update_manga_latest_chapter(manga_id, latest_chapter):
    manga_dict_list = []
    manga_rows = get_rows_from_csv(manga_list_csv_path)
    for manga in manga_rows:
        if manga_id == manga["manga_id"]:
            manga_dict_list.append(
                {
                    "title": manga["title"],
                    "manga_id": manga_id,
                    "latest_chapter": latest_chapter,
                    "authors": manga["authors"],
                    "artists": manga["artists"],
                    "description": manga["description"],
                    "cover_name": manga["cover_name"],
                }
            )
        elif manga_id != manga["manga_id"]:
            manga_dict_list.append(manga)
    with open(manga_list_csv_path, "w", newline="") as f:
        writer = DictWriter(
            f,
            [
                "title",
                "manga_id",
                "latest_chapter",
                "authors",
                "artists",
                "description",
                "cover_name",
            ],
        )
        writer.writeheader()
        writer.writerows(manga_dict_list)


def wrap_text(text, limit):
    if len(text) > limit:
        return f"{text[:35]}..."
    else:
        return text


def send_notification(title):
    toast = Notification(
        app_id="Manga Notifier",
        title=f"New {title} Chapter Released!",
        msg=f"{title} just dropped a new chapter! Time to read!",
        duration="long",
        icon=icon_img_path,
    )
    toast.set_audio(audio.Reminder, loop=False)
    toast.show()


def check_manga_list(manga_id):
    with open(manga_list_csv_path, "r") as f:
        manga_ids = []
        for row in list(DictReader(f)):
            manga_ids.append(row["manga_id"].lower())
    if manga_id.lower() not in manga_ids:
        return True
    elif manga_id in manga_ids:
        return False


# Writes manga info on manga_list.csv
def write_manga_info(
    title, manga_id, latest_chapter, authors, artists, description, cover_url
):
    cover_name = convert_title_into_file_name(title)
    save_cover(cover_name, cover_url)
    description = process_description(description, "store")
    with open(manga_list_csv_path, "a", newline="") as f:
        writer = DictWriter(
            f,
            [
                "title",
                "manga_id",
                "latest_chapter",
                "authors",
                "artists",
                "description",
                "cover_name",
            ],
        )
        writer.writerow(
            {
                "title": title,
                "manga_id": manga_id,
                "latest_chapter": latest_chapter,
                "authors": authors,
                "artists": artists,
                "description": description,
                "cover_name": cover_name,
            }
        )


# replaces description's line break with <br>
def process_description(description, mode):
    if mode.lower() == "store":
        return description.replace("\n", "<br>")
    elif mode.lower() == "display":
        return description.replace("<br>", "\n")


# saves images in resources/images/cover_images/
def save_cover(cover_name, url):
    filepath = get_covers_path(cover_name)

    response = requests.get(url)
    response.raise_for_status()

    with open(filepath, "wb") as file:
        file.write(response.content)


# converts title for cover name
def convert_title_into_file_name(title):
    garbages = [
    ".", ",", ":", ";", "!", "?", "\"", "'", "“", "”", "‘", "’",
    "(", ")", "[", "]", "{", "}",
    "+", "-", "±", "*", "/", "×", "÷",
    "=", "<", ">", "≠", "≤", "≥",
    "%", "$", "¥", "£", "€",
    "~", "|", "_", "@", "#", "&", "^", "\\", "/", "…",
    "「", "」", "『", "』", "、", "。", "・", "〜",
    "！", "？", "：", "；",
    "♥", "★", "☆", "♪", "♬",
    "→", "←", "↑", "↓",
    "／", "＼", "°", "©", "®", "™"
]

    title = title.lower().strip()
    for garbage in garbages:
        if garbage in title:
            title = title.replace(garbage, "")

    return f"{title.strip().replace(" ","_")}.jpg"


def remove_manga(manga_id, cover_name):
    rows = get_rows_from_csv(manga_list_csv_path)
    not_to_remove = []
    for row in rows:
        if row["manga_id"] != manga_id:
            not_to_remove.append(row)

    remove_cover(cover_name)
    with open(manga_list_csv_path, "w", newline="") as f:
        writer = DictWriter(
            f,
            [
                "title",
                "manga_id",
                "latest_chapter",
                "authors",
                "artists",
                "description",
                "cover_name",
            ],
        )
        writer.writeheader()
        writer.writerows(not_to_remove)


def remove_cover(cover_name):
    cover_path = get_covers_path(cover_name)
    if path.exists(cover_path):
        remove(cover_path)
