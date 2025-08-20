# Built in modules
from csv import DictWriter, DictReader
from pathlib import Path
from ctypes import windll

# Third Party modules
import customtkinter as ctk
from PIL import Image

# Functions
from src.functions import (
    extract_name_from_url,
    get_rows_from_csv,
    check_rss_feed,
)


windll.shell32.SetCurrentProcessExplicitAppUserModelID("manga_notifier.1")

ctk.set_default_color_theme("themes/dark_theme.json")
ctk.set_appearance_mode("dark")
font = ("Comic Sans MS", 14)


def run_app():
    """
    All FUNCTIONS
    """

    def add_manga():
        success, text = extract_name_from_url(manga_entry.get().strip())
        if success:
            MangaListLabel(manga_list_frame, text)
            manga_entry.delete(0, "end")
            send_in_app_notifications("New Manga Added!", "plus.png")
        if not success:
            send_in_app_notifications(text, "warning.png")

    def display_manga_ui():
        rows = get_rows_from_csv("manga_list.csv")
        for row in rows:
            MangaListLabel(manga_list_frame, row["name"])

    def send_in_app_notifications(text, image):
        notification_frame = ctk.CTkFrame(app)
        notification_frame.configure(border_width=1.5)
        notification_frame.place(x=10, y=10)
        notification_label = ctk.CTkLabel(notification_frame)
        notification_label.configure(
            text=f"  {text}",
            fg_color="transparent",
            font=font,
            image=ctk.CTkImage(Image.open(str(Path(f"images/{image}").resolve()))),
            compound="left",
        )
        notification_label.pack(padx=10, pady=5)
        notification_frame.after(3000, lambda: notification_frame.destroy())

    def display_notification_list():
        rows = get_rows_from_csv("notifications.csv")
        for row in rows[::-1]:
            NotificationLabel(
                notifications_list_frame, row["name"], row["last_alerted"]
            )

    def clear_notifications():
        with open(
            str(Path("csv_files/notifications.csv").resolve()), "w", newline=""
        ) as f:
            writer = DictWriter(f, ["name", "last_alerted"])
            writer.writeheader()
        for widget in notifications_list_frame.winfo_children():
            widget.destroy()
        send_in_app_notifications("Cleared!", "success.png")

    def check_feed():
        dict_list = check_rss_feed()  # type: ignore
        if dict_list:
            for dict in dict_list:
                NotificationLabel(notifications_list_frame, dict["name"], dict["time"])
        app.after(60000, check_feed)

    """ 
    APP GUI CODE
    """
    # Main Window
    app = ctk.CTk()
    app.title("Manga Notifier")
    app.iconbitmap(str(Path("images/logo_transparent.ico").resolve()))
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
    search_entry_frame.pack(fill="x", pady=(30, 10), padx=110)

    search_entry = ctk.CTkEntry(search_entry_frame)
    search_entry.configure(
        placeholder_text="Enter Manga name",
        border_width=1.5,
        corner_radius=13,
        height=45,
    )
    search_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

    # Scrollable frame for manga list
    search_list_frame = ctk.CTkScrollableFrame(manga_search)
    search_list_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    search_list_frame.pack(expand=True, fill="both", pady=(1, 10), padx=110)

    search_button = ctk.CTkButton(
        search_entry_frame,
    )
    search_button.configure(
        text="Search",
        command=add_manga,
        font=("Comic Sans MS", 15, "bold"),
        border_width=1.5,
        height=45,
        width=60,
        corner_radius=13,
    )
    search_button.pack(side="right")

    # Manga List Tab
    manga_list_tab = tabs.add("Manga List")

    # Entry frame
    manga_entry_frame = ctk.CTkFrame(manga_list_tab)
    manga_entry_frame.configure(border_width=0)
    manga_entry_frame.pack(fill="x", pady=(30, 10), padx=110)

    manga_entry = ctk.CTkEntry(manga_entry_frame)
    manga_entry.configure(
        placeholder_text="Enter MyAnimeList or MangaUpdates link",
        border_width=1.5,
        corner_radius=13,
        height=45,
    )
    manga_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

    # Scrollable frame for manga list
    manga_list_frame = ctk.CTkScrollableFrame(manga_list_tab)
    manga_list_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    manga_list_frame.pack(expand=True, fill="both", pady=(1, 10), padx=110)

    # Class for Manga list
    class MangaListLabel:
        def __init__(self, list_frame, name):
            self.list_frame = list_frame
            self.name = name
            self.frame = ctk.CTkFrame(self.list_frame)
            self.frame.configure(border_width=1.5, fg_color="#3d3d3d", height=40)
            self.frame.pack(fill="x", pady=4)

            self.label = ctk.CTkLabel(self.frame, text=self.name, height=40)
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
            names = []
            with open(str(Path("csv_files/manga_list.csv").resolve()), "r") as f:
                for row in DictReader(f):
                    if row["name"] != self.name:
                        names.append(row["name"])

            with open(
                str(Path("csv_files/manga_list.csv").resolve()), "w", newline=""
            ) as f:
                writer = DictWriter(f, ["name"])
                writer.writeheader()
                for name in names:
                    writer.writerow({"name": name})
            send_in_app_notifications(
                f"{self.name} has been removed from your list", "trash.png"
            )

    display_manga_ui()

    add_button = ctk.CTkButton(
        manga_entry_frame,
    )
    add_button.configure(
        text="Add",
        command=add_manga,
        font=("Comic Sans MS", 15, "bold"),
        border_width=1.5,
        height=45,
        width=60,
        corner_radius=13,
    )
    add_button.pack(side="right")

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
        image=ctk.CTkImage(Image.open(str(Path("images/trash.png").resolve()))),
        compound="left",
    )

    clear_notification_button.pack(fill="x", pady=(10, 10), padx=110, side="bottom")

    notifications_list_frame = ctk.CTkScrollableFrame(notifications_tab)
    notifications_list_frame.configure(
        fg_color="transparent",
        border_width=1.5,
        corner_radius=13,
        scrollbar_button_color="light grey",
        scrollbar_button_hover_color="grey",
    )
    notifications_list_frame.pack(expand=True, fill="both", pady=(30, 0), padx=110)

    class NotificationLabel:
        def __init__(self, list_frame, name, time):
            self.name = name
            self.time = time
            self.list_frame = list_frame
            self.frame = ctk.CTkFrame(self.list_frame)
            self.frame.configure(border_width=1.5, fg_color="#3d3d3d")
            self.frame.pack(fill="x", pady=4)

            self.label = ctk.CTkLabel(self.frame)
            self.label.configure(
                text=f"A new chapter of {self.name} has been released", height=40
            )
            self.label.pack(side="left", padx=13, pady=5)

            self.time_label = ctk.CTkLabel(self.frame)
            self.time_label.configure(text=self.time, font=("Comic Sans MS", 13))
            self.time_label.pack(side="right", padx=10, pady=5)

    display_notification_list()

    app.after(30000, check_feed)

    # Run the app
    app.mainloop()
