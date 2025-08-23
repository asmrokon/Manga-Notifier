from datetime import datetime
import re
from csv import DictReader, DictWriter
from os import path
from io import BytesIO
from PIL import Image

from feedparser import parse
from winotify import Notification, audio
import requests
from bs4 import BeautifulSoup



# Path to resources folder
BASE_DIR = path.dirname(path.dirname(__file__))
RESOURCES_DIR = path.join(BASE_DIR, "resources")

manga_list_csv_path = path.join(RESOURCES_DIR, "csv_files", "manga_list.csv")
notifications_csv_path = path.join(RESOURCES_DIR, "csv_files", "notifications.csv")
icon_img_path = path.join(RESOURCES_DIR, "images", "logo_transparent.png")


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
        "order[followedCount]": "desc"
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
                artist_name = rel.get("attributes",{}).get("name")
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
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
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


# Extract name from url
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
            manga_list_csv_path, "a", newline=""
        ) as f:
            if check_manga_list(name.strip(), "manga_list"):
                return False, f"{name} already in the list"
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": name.strip()})  # type: ignore
        return True, name.strip()

    else:
        with open(
            manga_list_csv_path, "a", newline=""
        ) as f:
            if check_manga_list(manga_title.strip(), "manga_list"):  # type: ignore
                return False, f"{manga_title.strip()} already in the list"  # type: ignore
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": manga_title.strip()})  # type: ignore
        return True, manga_title.strip()  # type: ignore

# Loads image from link
def load_image(url):
    response = requests.get(url)
    bytes = BytesIO(response.content)
    image = Image.open(bytes)
    return image

# Display manga in the scrollable frame
def get_rows_from_csv(file_name):
    with open(path.join(RESOURCES_DIR, "csv_files", f"{file_name}"), "r") as f:
        rows = list(DictReader(f))
        return rows


# Check Manga feed after every 3 minutes
def check_rss_feed():
    html = parse("https://www.mangaupdates.com/rss")
    time = datetime.now().strftime("%H:%M %d %B")
    rows = get_rows_from_csv("manga_list.csv")
    to_be_notified = []
    for row in rows:
        if check_manga_list(row["name"], "notification"):
            for entry in html.entries:
                if row["name"].lower() in str(entry.title).lower():
                    send_notification(row["name"])
                    with open(
                        notifications_csv_path,
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
        icon=icon_img_path,
    )
    toast.set_audio(audio.Reminder, loop=False)
    toast.show()


def check_manga_list(manga_id,mode=""):
    with open(manga_list_csv_path, "r") as f:
            manga_ids = []
            for row in list(DictReader(f)):
                manga_ids.append(row["manga_id"].lower())
    if manga_id.lower() not in manga_ids:
        return True
    elif manga_id in manga_ids:
        return False
# Writes manga info on manga_list.csv
def write_manga_info(title,manga_id,latest_chapter):
    with open(manga_list_csv_path,"a",newline="") as f:
        writer = DictWriter(f,["title","manga_id","latest_chapter"])
        writer.writerow({"title":title,"manga_id":manga_id,"latest_chapter":latest_chapter})


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
