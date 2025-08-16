from csv import DictWriter, DictReader

import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
from PIL import Image



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
        show_notifications("Invalid URL!")
        return
    html = BeautifulSoup(reqs, 'html.parser')  # type: ignore
    title = html.find("title").get_text().strip().split(" |") # type: ignore
    with open("manga_list.csv","a",newline="") as f:
        writer = DictWriter(f, ["name"])
        writer.writerow({"name": title[0]})
    MangaListLabel(manga_list_frame,title[0])
    manga_entry.delete(0,"end")

# Display manga in the scrollable frame
def display_manga():
    with open("manga_list.csv","r") as f:
        rows = list(DictReader(f))
        names = []
        for row in rows:
            names.append(row["name"])
    for name in names:
        MangaListLabel(manga_list_frame, name)

def show_notifications(text):
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
    with open("notifications.csv","r") as f:
        rows = list(DictReader(f))
    for row in rows:
        NotificationLabel(notifications_list_frame,row["name"],row["time"])

def clear_notifications():
    print("Cleared")


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
        with open("manga_list.csv","r") as f:
            for row in DictReader(f):                        
                if row["name"] != self.name:
                    names.append(row["name"])

        with open("manga_list.csv","w",newline="") as f:
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


display_notifications()



# Run the app
app.mainloop()