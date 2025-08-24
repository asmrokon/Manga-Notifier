# Built in modules
from csv import DictWriter, DictReader
from ctypes import windll
from os import path

# Third Party modules
import customtkinter as ctk
from PIL import Image

# Functions
from functions import (
    get_rows_from_csv,
    check_feed,
    get_manga_data,
    load_image,
    get_latest_chapter,
    check_manga_list,
    write_manga_info,
    wrap_text,
)

# Path to resources folder
BASE_DIR = path.dirname(path.dirname(__file__))
RESOURCES_DIR = path.join(BASE_DIR, "resources")

manga_list_csv_path = path.join(RESOURCES_DIR, "csv_files", "manga_list.csv")
notifications_csv_path = path.join(RESOURCES_DIR, "csv_files", "notifications.csv")
theme_path = path.join(RESOURCES_DIR, "themes", "dark_theme.json")
warning_img_path = path.join(RESOURCES_DIR, "images", "warning.png")
trash_img_path = path.join(RESOURCES_DIR, "images", "trash.png")
success_img_path = path.join(RESOURCES_DIR, "images", "success.png")
plus_img_path = path.join(RESOURCES_DIR, "images", "plus.png")
logo_ico_path = path.join(RESOURCES_DIR, "images", "logo_transparent.ico")

one_piece_cover_path = path.join(RESOURCES_DIR, "images", "1onepiece.jpg")


windll.shell32.SetCurrentProcessExplicitAppUserModelID("manga_notifier.1")

ctk.set_default_color_theme(theme_path)
ctk.set_appearance_mode("dark")
font = ("Comic Sans MS", 14)


def run_app():
    """
    All FUNCTIONS
    """

    # Adds manga to list
    def add_manga(title, manga_id):
        # gets latest chapter
        latest_chapter = get_latest_chapter(manga_id)

        # check if manga is already in the list
        if check_manga_list(manga_id):
            write_manga_info(title, manga_id, latest_chapter)
            MangaListLabel(manga_list_frame, title)
            send_in_app_notifications("New Manga Added!", "plus.png")
        elif not check_manga_list(manga_id):
            send_in_app_notifications("Failed: Already in the list", "warning.png")

    def display_manga_ui():
        rows = get_rows_from_csv(manga_list_csv_path)
        for row in rows:
            MangaListLabel(manga_list_frame, row["title"])

    def send_in_app_notifications(text, image):
        notification_frame = ctk.CTkFrame(app)
        notification_frame.configure(border_width=1.5)
        notification_frame.place(x=10, y=10)
        notification_label = ctk.CTkLabel(notification_frame)
        notification_label.configure(
            text=f"  {text}",
            fg_color="transparent",
            font=font,
            image=ctk.CTkImage(
                Image.open(path.join(RESOURCES_DIR, "images", f"{image}"))
            ),
            compound="left",
        )
        notification_label.pack(padx=10, pady=5)
        notification_frame.after(3000, lambda: notification_frame.destroy())

    def display_notification_list():
        rows = get_rows_from_csv(notifications_csv_path)
        for row in rows[::-1]:
            NotificationLabel(
                notifications_list_frame,
                row["title"],
                row["rel_time"],
                row["latest_chapter"],
            )

    def clear_notifications():
        for widget in notifications_list_frame.winfo_children():
            widget.destroy()
        with open(notifications_csv_path, "w", newline="") as f:
            writer = DictWriter(f, ["title", "latest_chapter", "rel_time"])
            writer.writeheader()
        send_in_app_notifications("Cleared!", "success.png")

    def call_check_feed():
        dict_list = check_feed()
        if dict_list:
            for dict in dict_list:
                NotificationLabel(
                    notifications_list_frame,
                    dict["title"],
                    dict["rel_time"],
                    dict["latest_chapter"],
                )
        app.after(600000, call_check_feed)

    def search_manga(event=None):
        title = search_entry.get().strip()

        # deletes old search result
        for _ in search_result_frame.winfo_children():
            _.destroy()
        app.update_idletasks()

        # creates Searching... textbox
        searching_label = ctk.CTkLabel(
            search_result_frame,
            text="Searching...",
            fg_color="transparent",
            padx=20,
            font=("Comic Sans MS", 18, "bold"),
        )
        searching_label.pack(anchor="n", side="top")
        app.update_idletasks()

        # returns a list of title, authors, artists, latest_chapter, description, cover_url of 10 mangas
        manga_list = get_manga_data(title)

        # deletes searching_label
        searching_label.destroy()

        # shows search result
        create_result_entry(manga_list)

    # creates search result
    def create_result_entry(manga_list):
        # creates frame for each manga
        for manga in manga_list:
            create_result_frame(manga)

    # creates frame for each manga inside search result scrollable frame
    def create_result_frame(manga):
        description = manga["description"]
        if len(description) > 650:
            description = f"{manga["description"][:650]}..."

        single_result_frame = ctk.CTkFrame(
            search_result_frame,
            height=255,
        )
        single_result_frame.pack(
            fill="x",
            padx=10,
            pady=7,
        )
        single_result_frame.grid_columnconfigure(1, weight=1)

        # text frame that will contain all texts
        text_frame = ctk.CTkFrame(single_result_frame)
        text_frame.configure(
            fg_color="transparent",
            border_width=0,
        )
        text_frame.grid(column=1, padx=(10, 10), pady=(5, 5), sticky="nsew")

        # Display title
        display_title(text_frame, manga["title"])

        # Display Authors and artists detail
        display_authors_and_artists(text_frame, manga["authors"], manga["artists"])

        # display Descriptions
        display_description(text_frame, description)

        # Loads manga cover
        load_cover(single_result_frame, manga["cover_url"])

        def pass_info_to_add_manga():
            add_manga(manga["title"], manga["manga_id"])

        # Create manga add button
        add_button = ctk.CTkButton(single_result_frame)
        add_button.configure(
            text="",
            command=pass_info_to_add_manga,
            font=("Comic Sans MS", 15, "bold"),
            border_width=0,
            height=45,
            width=60,
            fg_color="transparent",
            hover_color="#2B2B2B",
            image=ctk.CTkImage(Image.open(plus_img_path), size=(30, 30)),
        )
        add_button.grid(sticky="en", padx=3, pady=3, row=0, column=2)

    # Loads manga cover
    def load_cover(frame, url):
        cover_label = ctk.CTkLabel(frame, text="Loading...")
        cover_label.grid(column=0, row=0, padx=(3, 10), pady=2)
        cover_image = load_image(url)
        if cover_image:
            cover_label.configure(
                image=ctk.CTkImage(cover_image, size=(170, 255)), text=""
            )
        else:
            cover_label.configure(text="Failed loading")

    def display_title(frame, title):
        title_label = ctk.CTkLabel(frame)
        title_label.configure(
            text=f"{title}",
            font=("Comic Sans MS", 17, "bold"),
            justify="left",
            wraplength=650,
        )
        title_label.grid(sticky="nw", pady=(1, 2))

    def display_authors_and_artists(frame, artists, authors):
        author_and_artist_label = ctk.CTkLabel(frame)
        author_and_artist_label.configure(
            text=f"Authors: {", ".join(authors)}\nArtists: {", ".join(artists)}",
            justify="left",
        )
        author_and_artist_label.grid(sticky="nw", pady=(0, 7))

    def display_description(frame, description):
        desc = ctk.CTkLabel(frame)
        desc.configure(
            text=description, justify="left", wraplength=650, fg_color="transparent"
        )
        desc.grid(
            sticky="nw",
            pady=(0, 3),
            padx=(0, 10),
        )

    """ 
    APP GUI CODE
    """
    # Main Window
    app = ctk.CTk()
    app.title("Manga Notifier")
    app.iconbitmap(logo_ico_path)
    app.geometry("750x400")

    # Tabs
    tabs = ctk.CTkTabview(app)
    tabs.configure(
        width=480,
        height=300,
        border_width=0,
    )
    tabs._segmented_button.configure(font=("Comic Sans MS", 16))
    tabs.pack(expand=True, fill="both", padx=0, pady=0)

    # Manga Adding Tab
    manga_search = tabs.add("Search Manga")

    # Title Entry frame
    search_entry_frame = ctk.CTkFrame(manga_search)
    search_entry_frame.configure(border_width=0)
    search_entry_frame.pack(fill="x", pady=(30, 10), padx=130)

    search_entry = ctk.CTkEntry(search_entry_frame)
    search_entry.configure(
        placeholder_text="Enter Manga name",
        border_width=1.5,
        corner_radius=13,
        height=45,
    )
    search_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
    search_entry.bind("<Return>", search_manga)

    # Scrollable frame for manga list
    search_result_frame = ctk.CTkScrollableFrame(manga_search)
    search_result_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    search_result_frame.pack(expand=True, fill="both", pady=(1, 10), padx=130)

    search_button = ctk.CTkButton(
        search_entry_frame,
    )
    search_button.configure(
        text="Search",
        command=search_manga,
        font=("Comic Sans MS", 15, "bold"),
        border_width=1.5,
        height=45,
        width=60,
        corner_radius=13,
    )
    search_button.pack(side="right")

    # Manga List Tab
    manga_list_tab = tabs.add("Manga List")

    # Scrollable frame for manga list
    manga_list_frame = ctk.CTkScrollableFrame(manga_list_tab)
    manga_list_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    manga_list_frame.pack(expand=True, fill="both", pady=(30, 10), padx=130)

    # Class for Manga list
    class MangaListLabel:
        def __init__(self, list_frame, title):
            self.list_frame = list_frame
            self.title = title
            self.frame = ctk.CTkFrame(self.list_frame)
            self.frame.configure(border_width=1.5, fg_color="#3d3d3d", height=40)
            self.frame.pack(fill="x", pady=4)

            self.label = ctk.CTkLabel(self.frame, text=self.title, height=40)
            self.label.pack(side="left", padx=13, pady=5)

            self.remove_button = ctk.CTkButton(self.frame)
            self.remove_button.configure(
                text="Remove",
                width=60,
                border_width=1.5,
                command=self.remove,
                font=("Comic Sans MS", 15, "bold"),
                height=35,
            )
            self.remove_button.pack(side="right", padx=5)

        def remove(self):
            self.frame.destroy()
            dicts = []
            with open(manga_list_csv_path, "r") as f:
                for row in DictReader(f):
                    if row["title"] != self.title:
                        dicts.append(row)

            with open(manga_list_csv_path, "w", newline="") as f:
                writer = DictWriter(f, ["title", "manga_id", "latest_chapter"])
                writer.writeheader()
                writer.writerows(dicts)
            send_in_app_notifications(
                f"{self.title} has been removed from your list", "trash.png"
            )

    display_manga_ui()

    # Notification tab
    notifications_tab = tabs.add("Notifications")
    notifications_tab.configure()

    tabs.set("Search Manga")

    clear_notification_button = ctk.CTkButton(notifications_tab)
    clear_notification_button.configure(
        text="Clear All Notifications",
        width=60,
        font=("Comic Sans MS", 15, "bold"),
        border_width=1.5,
        height=45,
        corner_radius=13,
        command=clear_notifications,
        image=ctk.CTkImage(Image.open(trash_img_path)),
        compound="left",
    )

    clear_notification_button.pack(fill="x", pady=(10, 10), padx=130, side="bottom")

    notifications_list_frame = ctk.CTkScrollableFrame(notifications_tab)
    notifications_list_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    notifications_list_frame.pack(expand=True, fill="both", pady=(30, 0), padx=130)

    class NotificationLabel:
        def __init__(self, list_frame, name, time, latest_chapter):
            self.name = name
            self.time = time
            self.list_frame = list_frame
            self.latest_chapter = latest_chapter
            self.frame = ctk.CTkFrame(self.list_frame)
            self.frame.configure(border_width=1.5, fg_color="#3d3d3d")
            self.frame.pack(fill="x", pady=4)

            self.label = ctk.CTkLabel(self.frame)
            self.label.configure(
                text=f"A new chapter of {wrap_text(self.name,35)} has been released | New Chapter: {self.latest_chapter}",
                height=40,
            )
            self.label.pack(side="left", padx=13, pady=5)

            self.time_label = ctk.CTkLabel(self.frame)
            self.time_label.configure(text=self.time, font=("Comic Sans MS", 13))
            self.time_label.pack(side="right", padx=10, pady=5)

    display_notification_list()

    app.after(30000, call_check_feed)

    # Run the app
    app.mainloop()