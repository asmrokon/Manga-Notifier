from csv import DictWriter, DictReader
from pathlib import Path
from datetime import datetime
import re

import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
from PIL import Image
from feedparser import parse
from winotify import Notification, audio



ctk.set_appearance_mode("light")
font = ("Comic Sans MS", 14)

""" 
All FUNCTIONS
"""




# Function to add manga
def add_manga():
    url = manga_entry.get().strip()
    try:
        reqs = requests.get(url).text
    except requests.exceptions.MissingSchema:
        return
    html = BeautifulSoup(reqs, 'html.parser')  # type: ignore
    manga_title, garbages = html.find("title").get_text().strip().split(" |") # type: ignore
    if "(" in manga_title:
        name, again_garbages = manga_title.split("(")
        with open(str(Path("csv_files/manga_list.csv").resolve()),"a",newline="") as f:
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": name.strip()})  # type: ignore
        MangaListLabel(manga_list_frame,name)
        manga_entry.delete(0,"end")
    else:
        with open(str(Path("csv_files/manga_list.csv").resolve()),"a",newline="") as f:
            writer = DictWriter(f, ["name"])
            writer.writerow({"name": manga_title.strip()})  # type: ignore
        MangaListLabel(manga_list_frame,manga_title[0])
        manga_entry.delete(0,"end")


# Display manga in the scrollable frame
def display_manga():
    with open(str(Path("csv_files/manga_list.csv").resolve()),"r") as f:
        rows = list(DictReader(f))
    for row in rows:
        MangaListLabel(manga_list_frame, row["name"])


def send_in_app_notifications(text):
    warning_img = ctk.CTkImage(light_image=Image.open("images/warning.png"))
                             
    notification_frame = ctk.CTkFrame(app)
    notification_frame.configure(
            border_width=1.5,
            border_color="black",
            fg_color="white"
        )
    notification_frame.place(x=10,y=10)
    notification_label = ctk.CTkLabel(notification_frame)
    notification_label.configure(
                                text=f"  {text}",
                                fg_color="transparent",
                                text_color="black",          
                                font=font,
                                image=warning_img,
                                compound="left"                               
                                )
    notification_label.pack(padx=10, pady=5)
    notification_frame.after(3000, lambda: notification_frame.destroy())

def display_notifications():
    with open(str(Path("csv_files/notifications.csv").resolve()),"r") as f:
        rows = list(DictReader(f))
    for row in rows[::-1]:
        NotificationLabel(notifications_list_frame,row["name"],row["last_alerted"])

def clear_notifications():
    print("Cleared")


# Check Manga feed after every 3 minutes
def check_manga():
    html = parse("https://www.mangaupdates.com/rss")
    time = datetime.now().strftime("%H:%M %d %B")

    with open(str(Path("csv_files/manga_list.csv").resolve()),"r") as f:
        rows = list(DictReader(f))
    for row in rows:
        if to_check(row["name"]):
            for entry in html.entries[:8]:
                if row["name"].lower() in str(entry.title).lower():
                    send_notification(row["name"])
                    with open(str(Path("csv_files/notifications.csv").resolve()),"a",newline="") as f:
                        writer = DictWriter(f,["name","last_alerted"])
                        writer.writerow({"name": row["name"],"last_alerted": time})
                        NotificationLabel(notifications_list_frame,row["name"],time)
    app.after(60000, check_manga)
    
def send_notification(name):
    toast = Notification(app_id="Manga Notifier",
                        title=f"New {name} Chapter Released!",
                        msg=f"{name} just dropped a new chapter! Time to read!",
                        duration="long",
                        icon=str(Path("images/logo_transparent.png").resolve())
                        )
    toast.set_audio(audio.Reminder, loop=False)
    toast.show()



def to_check(name):
    with open(str(Path("csv_files/notifications.csv").resolve()),"r") as f:
        rows = list(DictReader(f))
        notification_names = []
    for row in rows:
        notification_names.append(row["name"].lower())
    if name.lower() in notification_names:
        for row in rows[::-1]:
            if name.lower() == row["name"].lower():
                last_alerted = re.search(r'(?P<hour>\d{1,2}):(?P<min>\d{1,2})\s+(?P<date>\d{1,2})\s+(?P<month>[A-Za-z]+)', row["last_alerted"])
                if last_alerted:
                    diff = time_difference(2025,last_alerted.group("month"),last_alerted.group("date"),last_alerted.group("hour"),last_alerted.group("min"))
                    if diff > 2:
                        return True
                    else:
                        return False
    else:
        return True

def time_difference(last_year,last_month,last_date,last_hour,last_min):
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
        "december": 12
            }

    last_alerted_time = datetime(int(last_year), months[f"{last_month.lower()}"], int(last_date), int(last_hour), int(last_min))        
    now  = datetime.now()                         
    duration = now - last_alerted_time                                                 
    return duration.days



""" 
APP GUI CODE
"""
# Main Window
app = ctk.CTk()
app.title("Manga Notifier")
app.configure(fg_color="white")
app.geometry("700x300")


# Tabs
tabs = ctk.CTkTabview(app)
tabs.configure(
    width=480,
    height=300,
    fg_color="white",
    border_color="black",
    segmented_button_fg_color="white",
    segmented_button_unselected_color="white",
    segmented_button_selected_color="light grey",
    text_color="black",
    segmented_button_selected_hover_color="light grey",
    segmented_button_unselected_hover_color="white"
    
)
tabs._segmented_button.configure(font=("Comic Sans MS", 16))
tabs.pack(expand=True, fill="both", padx=0, pady=0)

manga_tab = tabs.add("Manga List")


# Entry frame
manga_entry_frame = ctk.CTkFrame(manga_tab)
manga_entry_frame.configure(fg_color="white")
manga_entry_frame.pack(fill="x", pady=(30,10), padx=110)

manga_entry = ctk.CTkEntry(manga_entry_frame)
manga_entry.configure(placeholder_text="Enter manga link here",
                      font=font,
                      fg_color="white",
                      border_color="black",
                      border_width=1.5,
                      corner_radius=13,
                      height=45                          
                      )
manga_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

# Scrollable frame for manga list
manga_list_frame = ctk.CTkScrollableFrame(manga_tab)
manga_list_frame.configure(
    fg_color="transparent",
    border_width=1.5,
    border_color="black",
    corner_radius=13,
    scrollbar_button_color="light grey",
    scrollbar_button_hover_color="grey",

)
manga_list_frame.pack(expand=True, fill="both", pady=1, padx=110)

# Class for Manga list
class MangaListLabel:
    def __init__(self, list_frame, name):
        self.list_frame = list_frame
        self.name = name
        self.frame = ctk.CTkFrame(self.list_frame)
        self.frame.configure(
            border_width=1.5,
            border_color="black",
            fg_color="white"
        )
        self.frame.pack(fill="x", pady=4)

        self.label = ctk.CTkLabel(self.frame, text=self.name, font=font)
        self.label.pack(side="left", padx=5, pady=5)

        self.remove_button = ctk.CTkButton(self.frame)
        self.remove_button.configure(
            text="Remove",
            width=60,         
            font=font,
            fg_color="white",
            text_color="black",
            border_color="black",
            border_width=1.5,
            hover_color="light grey",
            command=self.remove
        )
        self.remove_button.pack(side="right", padx=5)

    def remove(self):
        self.frame.destroy()
        names = []
        with open(str(Path("csv_files/manga_list.csv").resolve()),"r") as f:
            for row in DictReader(f):                        
                if row["name"] != self.name:
                    names.append(row["name"])

        with open(str(Path("csv_files/manga_list.csv").resolve()),"w",newline="") as f:
            writer = DictWriter(f, ["name"])
            writer.writeheader()
            for name in names:
                writer.writerow({"name": name})


display_manga()


add_button = ctk.CTkButton(manga_entry_frame,)
add_button.configure(text="Add",
                     command=add_manga,
                     font=("Comic Sans MS", 14, "bold"),
                     fg_color="transparent",
                     text_color="black",
                     border_color="black",
                     border_width=1.5,
                     hover_color="light grey",
                     height=45,
                     width=60,
                     corner_radius=13
                     )
add_button.pack(side="right")

# Notification tab
notifications_tab = tabs.add("Notifications")
notifications_tab.configure()

tabs.set("Manga List")

clear_notification_button = ctk.CTkButton(notifications_tab)
clear_notification_button.configure(
            text="Clear All Notifications",
            width=60,         
            font=("Comic Sans MS", 14, "bold"),
            fg_color="white",
            text_color="black",
            border_color="black",
            border_width=1.5,
            hover_color="light grey",
            height=45,
            corner_radius=13,
            command=clear_notifications
)

clear_notification_button.place(x=10,y=0)

notifications_list_frame = ctk.CTkScrollableFrame(notifications_tab)
notifications_list_frame.configure(
    fg_color="transparent",
    border_width=1.5,
    border_color="black",
    corner_radius=13,
    scrollbar_button_color="light grey",
    scrollbar_button_hover_color="grey",

)
notifications_list_frame.pack(expand=True, fill="both", pady=(50,0), padx=110)    

class NotificationLabel:
    def __init__(self,list_frame, name, time):
        self.name = name
        self.time = time
        self.list_frame = list_frame
        self.frame = ctk.CTkFrame(self.list_frame)
        self.frame.configure(
            border_width=1.5,
            border_color="black",
            fg_color="white"
        )
        self.frame.pack(fill="x", pady=4)

        self.label = ctk.CTkLabel(self.frame)
        self.label.configure(
            text=f"A new chapter of {self.name} has been released",
            font=font,
            height=35
        )
        self.label.pack(side="left", padx=5, pady=5)

        self.time_label = ctk.CTkLabel(self.frame)
        self.time_label.configure(
            text=self.time,
            font=("Comic Sans MS", 13)
        )
        self.time_label.pack(side="right",padx=10, pady=5)

display_notifications()

app.after(30000, check_manga)

# Run the app
app.mainloop()