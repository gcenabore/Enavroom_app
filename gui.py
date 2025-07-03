from tkinter import Tk
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
from bookingsystem import Booking, BookingSystem, get_distance, LOCATIONS, DISTANCE_MATRIX, ROUTE_IMAGE_MAP 

PURPLE_DARK = "#360042"
HIGHLIGHT_COLOR = "#6A0DAD"
GRAY_LIGHT = "#F0F0F0"
WHITE = "#FFFFFF"
TEXT_COLOR = "#333333"
RED_COLOR = "#FF0000"
GREEN_COLOR = "#008000"

FONT_TITLE = ("Arial", 12, "bold")
FONT_SUBTITLE = ("Arial", 8, "bold")
FONT_NORMAL = ("Arial", 7)
FONT_PRICE = ("Arial", 12, "bold")
FONT_BUTTON = ("Arial", 10, "bold")
FONT_HEADER = ("Arial", 18, "bold") # For page titles
FONT_BODY = ("Arial", 10)

_image_references = {}


IMAGE_BASE_PATH = os.path.join(os.path.expanduser('~'), 'enavroom_assets')

def load_image(filename, size=None, is_circular=False, fill_color=(200, 200, 200)):
    """
    Loads an image, optionally resizes it, and can make it circular.
    Uses a global dictionary to keep references.
    Provides a placeholder if the image is not found or fails to load.
    """
    filepath = os.path.join(IMAGE_BASE_PATH, filename)
    img_key = f"{filepath}_{size[0]}x{size[1]}_{is_circular}" if size else f"{filepath}_{is_circular}"

    if img_key in _image_references:
        return _image_references[img_key]

    pil_img = None
    try:
        if os.path.exists(filepath):
            pil_img = Image.open(filepath)
            if size:
                pil_img = pil_img.resize(size, Image.LANCZOS)
        else:
            print(f"DEBUG: Image file not found: {filepath}. Creating placeholder.")
            raise FileNotFoundError # Trigger fallback to placeholder creation

        if is_circular:
            # Create a circular image
            mask = Image.new('L', pil_img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + pil_img.size, fill=255)
            # Apply mask to the image, assuming RGBA for transparency
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            pil_img.putalpha(mask)

    except (FileNotFoundError, Exception) as e:
        # print(f"ERROR: Could not load or process image {filepath}: {e}. Creating fallback placeholder.")
        if size is None: size = (50, 50) # Default size for placeholder if not provided
        pil_img = Image.new('RGB', size, fill_color)
        d = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype("arial.ttf", int(size[1] * 0.3))
        except IOError:
            font = ImageFont.load_default()

        text = filename.split('.')[0]
        if len(text) > 10: text = text[:7] + "..."
        try:
            bbox = d.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError: # Fallback for older Pillow versions
            text_width, text_height = d.textsize(text, font=font)

        x = (size[0] - text_width) / 2
        y = (size[1] - text_height) / 2
        d.text((x, y), text, fill=(0,0,0), font=font)

    if pil_img:
        photo = ImageTk.PhotoImage(pil_img)
        _image_references[img_key] = photo
        return photo
    return None # Should not happen if placeholder is created

# --- Main Application Class ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Enavroom App")
        self.geometry("375x667") # Typical mobile app size
        self.resizable(False, False)
        self.configure(bg=PURPLE_DARK)

        self.frames = {}
        self.booking_system = BookingSystem()
        
        # State variables to pass data between pages
        self.current_booking_details = {
            "vehicle_type": "",
            "pickup_location": "",
            "dropoff_location": "",
            "distance": 0,
            "cost": 0,
            "payment_method": "Cash",
            "booking_id": None
        }

        # Create container frame for all pages
        container = tk.Frame(self, bg=PURPLE_DARK)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Initialize all pages and store them in self.frames
        for F in (StartPage, HomePage, MessagePage, NotificationPage, HistoryPage,
                  BookEnavroomPage, BookEnacarPage, PUandDOPage, MapPage,
                  LoadingPage, WeFoundDriverEnacarPage, WeFoundDriverEnavroomPage, DonePage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage") # Start with the StartPage

    def show_frame(self, page_name):
        """Shows a frame for the given page name and updates its content if needed."""
        frame = self.frames[page_name]
        # Call an update method on the frame if it exists and is needed
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()
        print(f"DEBUG: Showing frame: {page_name}")

    def exit_app(self):
        """Prompts user and exits the application."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.destroy()

    def update_booking_details(self, **kwargs):
        """Updates the current booking details dictionary."""
        self.current_booking_details.update(kwargs)
        print(f"DEBUG: Booking details updated: {self.current_booking_details}")

# --- Common Helper for Binding Widgets Recursively ---
def bind_widgets_recursively(widget, func):
    """Binds a function to a widget and all its children."""
    widget.bind("<Button-1>", func)
    for child in widget.winfo_children():
        bind_widgets_recursively(child, func)

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=PURPLE_DARK)

        # Enavroom Logo
        logo_img_size = (250, 80)
        logo_img = load_image("logo_enavroom.png", size=logo_img_size)

        if logo_img:
            logo_label = tk.Label(self, image=logo_img, bg=PURPLE_DARK)
            logo_label.image = logo_img
            logo_label.place(relx=0.5, rely=0.35, anchor=tk.CENTER)
        else:
            tk.Label(self, text="ENAVROOM", font=("Arial", 28, "bold"), bg=PURPLE_DARK, fg=WHITE).place(relx=0.5, rely=0.35, anchor=tk.CENTER)

        # Start Button
        start_button = tk.Button(self, text="Start", font=FONT_BUTTON,
                                 command=lambda: controller.show_frame("HomePage"),
                                 bg=WHITE, fg=TEXT_COLOR,
                                 width=15, height=2,
                                 relief="flat", bd=0, cursor="hand2",
                                 highlightbackground=GRAY_LIGHT,
                                 highlightthickness=1,
                                 border=0,
                                 overrelief="raised")
        start_button.place(relx=0.5, rely=0.65, anchor=tk.CENTER)

        # Exit Button
        exit_button = tk.Button(self, text="Exit", font=FONT_BUTTON,
        command=controller.exit_app,
        bg=WHITE, fg=TEXT_COLOR,
        width=15, height=2,
        relief="flat", bd=0, cursor="hand2",
        highlightbackground=GRAY_LIGHT,
        highlightthickness=1,
        border=0,
        overrelief="raised")
        exit_button.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        # --- Top Header Frame ---
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=100)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        logo_header_img = load_image("logo_enavroom.png", (250, 80))
        if logo_header_img:
            logo_label = tk.Label(header_frame, image=logo_header_img, bg=PURPLE_DARK, bd=0, relief="flat")
            logo_label.image = logo_header_img
            logo_label.pack(pady=10)
        else:
            tk.Label(header_frame, text="ENNAVROOM", font=("Arial", 28, "bold"), fg=WHITE, bg=PURPLE_DARK).pack(pady=10)

        # --- Main Content Area Frame ---
        content_frame_homepage = tk.Frame(self, bg=GRAY_LIGHT)
        content_frame_homepage.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Service Selection Icons
        service_icons_frame = tk.Frame(content_frame_homepage, bg=WHITE, relief="solid", bd=1)
        service_icons_frame.pack(pady=20, padx=20, fill=tk.X)

        def create_service_button(parent, filename, text, command_page, vehicle_type_data=None):
            tk_icon = load_image(filename, size=(60, 60), is_circular=True, fill_color=PURPLE_DARK)
            button_frame = tk.Frame(parent, bg=WHITE)

            if tk_icon:
                icon_label = tk.Label(button_frame, image=tk_icon, bg=WHITE, cursor="hand2")
                icon_label.image = tk_icon
                icon_label.pack(pady=(10, 5))
            else:
                icon_label = tk.Label(button_frame, text=text[0], font=("Arial", 20, "bold"),
                                      bg=PURPLE_DARK, fg=WHITE, width=3, height=2,
                                      relief="solid", bd=1, cursor="hand2")
                icon_label.pack(pady=(10, 5))

            text_label = tk.Label(button_frame, text=text, font=("Arial", 12), fg=TEXT_COLOR, bg=WHITE, cursor="hand2")
            text_label.pack(pady=(0, 10))

            # Bind events to the frame and its children
            def command_wrapper(event):
                if vehicle_type_data:
                    self.controller.update_booking_details(vehicle_type=vehicle_type_data)
                self.controller.show_frame(command_page)

            bind_widgets_recursively(button_frame, command_wrapper)
            return button_frame

        # Moto Taxi Button
        moto_taxi_button_frame = create_service_button(service_icons_frame, "moto_taxi.png", "Moto Taxi", "BookEnavroomPage", "Enavroom-vroom")
        moto_taxi_button_frame.pack(side=tk.LEFT, expand=True, padx=15, pady=10)

        # Car Button (I'm making this default to 4-seater, but could add choice later)
        car_button_frame = create_service_button(service_icons_frame, "car.png", "Car", "BookEnacarPage", "Car (4-seater)")
        car_button_frame.pack(side=tk.LEFT, expand=True, padx=15, pady=10)

        # --- Bottom Navigation Bar Frame ---
        nav_frame = tk.Frame(self, bg=WHITE, height=70, bd=1, relief=tk.RAISED)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM)
        nav_frame.pack_propagate(False)

        nav_buttons_container = tk.Frame(nav_frame, bg=WHITE)
        nav_buttons_container.pack(expand=True)

        def create_nav_button(parent, filename, text, command):
            tk_icon = load_image(filename, size=(30, 30))
            if tk_icon:
                button = tk.Button(parent, image=tk_icon, text=text, compound=tk.TOP,
                                     font=("Arial", 10), fg=TEXT_COLOR, bg="white",
                                     command=command, bd=0, relief=tk.FLAT,
                                     activebackground=GRAY_LIGHT, activeforeground=PURPLE_DARK,
                                     cursor="hand2")
                button.image = tk_icon
                return button
            return None

        home_button = create_nav_button(nav_buttons_container, "home.png", "HOME", lambda: messagebox.showinfo("Navigation", "Already on Home Page!"))
        if home_button:
            home_button.pack(side=tk.LEFT, padx=20)

        messages_button = create_nav_button(nav_buttons_container, "message.png", "MESSAGES", lambda: controller.show_frame("MessagePage"))
        if messages_button:
            messages_button.pack(side=tk.LEFT, padx=20)

        history_button = create_nav_button(nav_buttons_container, "history.png", "HISTORY", lambda: controller.show_frame("HistoryPage"))
        if history_button:
            history_button.pack(side=tk.LEFT, padx=20)


class MessagePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Messages", lambda: controller.show_frame("HomePage"))

        tk.Label(self, text="You have no new messages.", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=50)

        tk.Button(self, text="View Notifications", font=FONT_BUTTON,
                  command=lambda: controller.show_frame("NotificationPage"),
                  bg=PURPLE_DARK, fg=WHITE, padx=20, pady=10).pack(pady=10)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

class NotificationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Notifications", lambda: controller.show_frame("MessagePage"))

        tk.Label(self, text="No new notifications.", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=50)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Booking History", lambda: controller.show_frame("HomePage"))

        self.history_list_frame = tk.Frame(self, bg=WHITE, bd=1, relief="solid")
        self.history_list_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.update_history_display()

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def on_show(self):
        """Called when the frame is shown."""
        self.update_history_display()

    def update_history_display(self):
        # Clear previous history entries
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()

        bookings = self.controller.booking_system.bookings
        if not bookings:
            tk.Label(self.history_list_frame, text="No past bookings yet.", font=FONT_NORMAL, bg=WHITE, fg=TEXT_COLOR).pack(pady=20)
            return

        for i, booking in enumerate(bookings):

            if booking.status == "cancelled":
                bg_color = "#eb868f" #red for cancelled bookings
    
            else:
                bg_color = "#75e990" if i % 2 == 0 else WHITE
            
            booking_frame = tk.Frame(self.history_list_frame, bg=bg_color, bd=1, relief="groove")
            booking_frame.pack(fill="x", padx=5, pady=2)
   
            tk.Label(booking_frame, text=f"Booking ID: {booking.id}", font=FONT_SUBTITLE, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Vehicle: {booking.vehicle_type}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Route: {booking.start} to {booking.end}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Distance: {booking.distance:.1f} km", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Cost: ₱{booking.cost:.2f} ({booking.payment_method})", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            
            # Add a separator
            if i < len(bookings) - 1:
                ttk.Separator(self.history_list_frame, orient="horizontal").pack(fill="x", padx=5, pady=5)

class BookEnavroomPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.current_selected_vehicle_frame = None
        self.selected_vehicle_type = "Enavroom-vroom" # Fixed for this page
        self.selected_payment_method = tk.StringVar(value="Cash")

        # Location and distance will be set when PUandDOPage is shown
        self.pickup_location_display = "PUP Main"
        self.dropoff_location_display = "PUP LHS"
        self.trip_distance = get_distance(self.pickup_location_display, self.dropoff_location_display)

        self._create_header("Book Enavroom", lambda: controller.show_frame("HomePage"))

        self._create_map_section("travel_enavroom.png")

        self.scrollable_content_frame = tk.Frame(self, bg=GRAY_LIGHT)
        self.scrollable_content_frame.pack(fill="both", expand=True)

        tk.Label(self.scrollable_content_frame, text="Service Details", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR) \
            .pack(pady=(10, 10))
        
        self.vehicle_option_frames = [] # Still keeping this for selection logic, but only one option for Enavroom

        vehicle_config = {"type": "Enavroom-vroom", "icon": "enavroom.png", "title": "Enavroom-vroom", "passengers": "1", "description": "Beat the traffic on a motorcycle ride."}
        calculated_price = self.controller.booking_system.calculate_cost(vehicle_config["type"], self.trip_distance)
        option_data = {
            "icon": vehicle_config["icon"],
            "title": vehicle_config["title"],
            "passengers": vehicle_config["passengers"],
            "description": vehicle_config["description"],
            "price": f"{calculated_price:.2f}"
        }
        frame = self._create_service_option(self.scrollable_content_frame, **option_data)
        frame.pack(fill="x", padx=60, pady=5)
        self.vehicle_option_frames.append((frame, vehicle_config["type"]))
        bind_widgets_recursively(frame, lambda e, f=frame, t=vehicle_config["type"]: self._select_vehicle_option(f, t))
        
        # Automatically select Enavroom-vroom when page loads
        self.on_show()

        self._create_payment_method_section()

        book_now_button = tk.Button(self.scrollable_content_frame, text="Book Now", command=self._on_book_now,
                                     font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                     padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=30, pady=(10, 10))

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def _create_map_section(self, map_filename):
        map_img = load_image(map_filename, (375, 160))
        if map_img:
            map_label = tk.Label(self, image=map_img, bg=GRAY_LIGHT)
            map_label.image = map_img
            map_label.pack(fill="x", pady=(0, 0))
        else:
            map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Tried: {map_filename})",
                                             font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
            map_placeholder_label.pack(fill="x", expand=False, pady=(0,0))

    def _create_service_option(self, parent, icon, title, passengers, description, price):
        frame = tk.Frame(parent, bg=WHITE, bd=1, relief="solid",
                         highlightbackground="light grey", highlightthickness=1,
                         padx=8, pady=6)

        icon_size = (30, 30)
        icon_image = load_image(icon, icon_size)

        if icon_image:
            icon_label = tk.Label(frame, image=icon_image, bg=WHITE)
            icon_label.image = icon_image
            icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")
        else:
            fallback_text = title[0] if title else "?"
            fallback_label = tk.Label(frame, text=fallback_text, font=("Arial", 16, "bold"), bg=WHITE, fg=PURPLE_DARK, width=3, height=2, bd=1, relief="solid")
            fallback_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")

        text_frame = tk.Frame(frame, bg=WHITE)
        text_frame.grid(row=0, column=1, rowspan=2, sticky="nw")

        tk.Label(text_frame, text=f"{title}", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=f"• {passengers} passengers", font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=description, font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w", wraplength=170, justify="left").pack(fill="x", expand=True)

        tk.Label(frame, text=f"₱{price}", font=FONT_PRICE, bg=WHITE, fg=PURPLE_DARK).grid(row=0, column=2, padx=(8, 0), sticky="ne")

        frame.grid_columnconfigure(1, weight=1)
        return frame

    def _create_payment_method_section(self):
        payment_frame = tk.Frame(self.scrollable_content_frame, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        payment_frame.pack(fill="x", padx=30, pady=(10, 10))

        cash_img = load_image("cash_2.png", (30, 30))
        cash_button_frame = tk.Frame(payment_frame, bg=WHITE)
        cash_button_frame.pack(side="left", expand=True, padx=10)
        if cash_img:
            cash_icon_label = tk.Label(cash_button_frame, image=cash_img, bg=WHITE)
            cash_icon_label.image = cash_img
            cash_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(cash_button_frame, text="C", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(cash_button_frame, text="Cash", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(cash_button_frame, lambda e: self._select_payment_method("Cash"))

        wallet_img = load_image("wallet_2.png", (30, 30))
        wallet_button_frame = tk.Frame(payment_frame, bg=WHITE)
        wallet_button_frame.pack(side="left", expand=True, padx=10)
        if wallet_img:
            wallet_icon_label = tk.Label(wallet_button_frame, image=wallet_img, bg=WHITE)
            wallet_icon_label.image = wallet_img
            wallet_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(wallet_button_frame, text="W", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(wallet_button_frame, text="Wallet", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(wallet_button_frame, lambda e: self._select_payment_method("Wallet"))

    def _select_vehicle_option(self, selected_frame, vehicle_type_name):
        if self.current_selected_vehicle_frame:
            self.current_selected_vehicle_frame.config(highlightbackground="light grey", highlightthickness=1)
        selected_frame.config(highlightbackground=HIGHLIGHT_COLOR, highlightthickness=2)
        self.current_selected_vehicle_frame = selected_frame
        # self.selected_vehicle_type is already fixed for this page
        print(f"Selected vehicle: {vehicle_type_name}")

    def _select_payment_method(self, method):
        self.selected_payment_method.set(method)
        print(f"Selected payment method: {method}")

    def _on_book_now(self):
        final_cost = self.controller.booking_system.calculate_cost(self.selected_vehicle_type, self.trip_distance)
        self.controller.update_booking_details(
            vehicle_type=self.selected_vehicle_type,
            pickup_location=self.pickup_location_display,
            dropoff_location=self.dropoff_location_display,
            distance=self.trip_distance,
            cost=final_cost,
            payment_method=self.selected_payment_method.get()
        )
        # book_enavroom.py -> PUandDO.py
        self.controller.show_frame("PUandDOPage")

    def on_show(self):
        # Auto-select the vehicle type for this specific page
        if self.vehicle_option_frames:
            # Assumes the first (and only) frame is the Enavroom option
            self._select_vehicle_option(self.vehicle_option_frames[0][0], self.vehicle_option_frames[0][1])

class BookEnacarPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.current_selected_vehicle_frame = None
        # Default to 4-seater, but can be changed by user if options are present
        self.selected_vehicle_type = "Car (4-seater)" 
        self.selected_payment_method = tk.StringVar(value="Cash")

        self.pickup_location_display = "PUP Main"
        self.dropoff_location_display = "PUP LHS"
        self.trip_distance = get_distance(self.pickup_location_display, self.dropoff_location_display)

        self._create_header("Book Enacar", lambda: controller.show_frame("HomePage"))

        self._create_map_section("travel_enacar.png")

        self.scrollable_content_frame = tk.Frame(self, bg=GRAY_LIGHT)
        self.scrollable_content_frame.pack(fill="both", expand=True)

        tk.Label(self.scrollable_content_frame, text="Service Details", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR) \
            .pack(pady=(10, 10))
        
        self.vehicle_option_frames = [] 

        # Car options
        vehicle_configs = [
            {"type": "Car (4-seater)", "icon": "enacar_2.png", "title": "Car (4-seater)", "passengers": "4", "description": "Get around town affordably, up to 4 passengers."},
            {"type": "Car (6-seater)", "icon": "enacar_2.png", "title": "Car (6-seater)", "passengers": "6", "description": "Roomy and affordable rides for up to six."},
        ]

        for config in vehicle_configs:
            calculated_price = self.controller.booking_system.calculate_cost(config["type"], self.trip_distance)
            option_data = {
                "icon": config["icon"],
                "title": config["title"],
                "passengers": config["passengers"],
                "description": config["description"],
                "price": f"{calculated_price:.2f}"
            }
            frame = self._create_service_option(self.scrollable_content_frame, **option_data)
            frame.pack(fill="x", padx=60, pady=5)
            self.vehicle_option_frames.append((frame, config["type"]))
            bind_widgets_recursively(frame, lambda e, f=frame, t=config["type"]: self._select_vehicle_option(f, t))
        
        # Auto-select the default car type on show
        self.on_show()

        self._create_payment_method_section()

        book_now_button = tk.Button(self.scrollable_content_frame, text="Book Now", command=self._on_book_now,
                                     font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                     padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=30, pady=(10, 10))

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def _create_map_section(self, map_filename):
        map_img = load_image(map_filename, (375, 160))
        if map_img:
            map_label = tk.Label(self, image=map_img, bg=GRAY_LIGHT)
            map_label.image = map_img
            map_label.pack(fill="x", pady=(0, 0))
        else:
            map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Tried: {map_filename})",
                                             font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
            map_placeholder_label.pack(fill="x", expand=False, pady=(0,0))

    def _create_service_option(self, parent, icon, title, passengers, description, price):
        frame = tk.Frame(parent, bg=WHITE, bd=1, relief="solid",
                         highlightbackground="light grey", highlightthickness=1,
                         padx=8, pady=6)

        icon_size = (30, 30)
        icon_image = load_image(icon, icon_size)

        if icon_image:
            icon_label = tk.Label(frame, image=icon_image, bg=WHITE)
            icon_label.image = icon_image
            icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")
        else:
            fallback_text = title[0] if title else "?"
            fallback_label = tk.Label(frame, text=fallback_text, font=("Arial", 16, "bold"), bg=WHITE, fg=PURPLE_DARK, width=3, height=2, bd=1, relief="solid")
            fallback_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")

        text_frame = tk.Frame(frame, bg=WHITE)
        text_frame.grid(row=0, column=1, rowspan=2, sticky="nw")

        tk.Label(text_frame, text=f"{title}", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=f"• {passengers} passengers", font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=description, font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w", wraplength=170, justify="left").pack(fill="x", expand=True)

        tk.Label(frame, text=f"₱{price}", font=FONT_PRICE, bg=WHITE, fg=PURPLE_DARK).grid(row=0, column=2, padx=(8, 0), sticky="ne")

        frame.grid_columnconfigure(1, weight=1)
        return frame

    def _create_payment_method_section(self):
        payment_frame = tk.Frame(self.scrollable_content_frame, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        payment_frame.pack(fill="x", padx=30, pady=(10, 10))

        cash_img = load_image("cash_2.png", (30, 30))
        cash_button_frame = tk.Frame(payment_frame, bg=WHITE)
        cash_button_frame.pack(side="left", expand=True, padx=10)
        if cash_img:
            cash_icon_label = tk.Label(cash_button_frame, image=cash_img, bg=WHITE)
            cash_icon_label.image = cash_img
            cash_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(cash_button_frame, text="C", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(cash_button_frame, text="Cash", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(cash_button_frame, lambda e: self._select_payment_method("Cash"))

        wallet_img = load_image("wallet_2.png", (30, 30))
        wallet_button_frame = tk.Frame(payment_frame, bg=WHITE)
        wallet_button_frame.pack(side="left", expand=True, padx=10)
        if wallet_img:
            wallet_icon_label = tk.Label(wallet_button_frame, image=wallet_img, bg=WHITE)
            wallet_icon_label.image = wallet_img
            wallet_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(wallet_button_frame, text="W", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(wallet_button_frame, text="Wallet", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(wallet_button_frame, lambda e: self._select_payment_method("Wallet"))

    def _select_vehicle_option(self, selected_frame, vehicle_type_name):
        if self.current_selected_vehicle_frame:
            self.current_selected_vehicle_frame.config(highlightbackground="light grey", highlightthickness=1)
        selected_frame.config(highlightbackground=HIGHLIGHT_COLOR, highlightthickness=2)
        self.current_selected_vehicle_frame = selected_frame
        # self.selected_vehicle_type is already fixed for this page
        print(f"Selected vehicle: {vehicle_type_name}")

    def _select_payment_method(self, method):
        self.selected_payment_method.set(method)
        print(f"Selected payment method: {method}")

    def _on_book_now(self):
        final_cost = self.controller.booking_system.calculate_cost(self.selected_vehicle_type, self.trip_distance)
        self.controller.update_booking_details(
            vehicle_type=self.selected_vehicle_type,
            pickup_location=self.pickup_location_display,
            dropoff_location=self.dropoff_location_display,
            distance=self.trip_distance,
            cost=final_cost,
            payment_method=self.selected_payment_method.get()
        )
        # book_enacar.py -> PUandDO.py
        self.controller.show_frame("PUandDOPage")

    def on_show(self):
        # Auto-select the first car type by default when page loads
        if self.vehicle_option_frames:
            # Select the first car option by default (Car 4-seater)
            self._select_vehicle_option(self.vehicle_option_frames[0][0], self.vehicle_option_frames[0][1])

class PUandDOPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.pickup_var = tk.StringVar(self)
        self.dropoff_var = tk.StringVar(self)

        self._create_header("Pickup & Dropoff", lambda: self._go_back_to_booking_page())

        tk.Label(self, text="Select Locations", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=(20, 10))

        # Pickup Location
        pickup_frame = tk.Frame(self, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        pickup_frame.pack(fill="x", padx=30, pady=5)

        pickup_menu = ttk.OptionMenu(pickup_frame, self.pickup_var, LOCATIONS[0], *LOCATIONS, command=self._on_pickup_selected)
        self.pickup_menu = pickup_menu  # Optional: Store reference
        pickup_menu.config(width=30)
        pickup_menu.pack(fill="x")

        # Dropoff Location
        dropoff_frame = tk.Frame(self, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        dropoff_frame.pack(fill="x", padx=30, pady=5)
        tk.Label(dropoff_frame, text="Dropoff Location:", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack(anchor="w")

        dropoff_menu = ttk.OptionMenu(dropoff_frame, self.dropoff_var, LOCATIONS[1], *LOCATIONS, command=self._update_cost)
        self.dropoff_menu = dropoff_menu  # Store for dynamic updates
        dropoff_menu.config(width=30)
        dropoff_menu.pack(fill="x")

        self.cost_label = tk.Label(self, text="Estimated Cost: ₱0.00", font=FONT_PRICE, bg=GRAY_LIGHT, fg=PURPLE_DARK)
        self.cost_label.pack(pady=20)

        book_now_button = tk.Button(self, text="Book Now", command=self._on_book_now,
        font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
        padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=30, pady=(10, 10))

    def _on_pickup_selected(self, selected_pickup):
        drop_menu = self.dropoff_menu["menu"]
        drop_menu.delete(0, "end")  # Clear current drop-off options

        for location in LOCATIONS:
            if location != selected_pickup:
                drop_menu.add_command(label=location, command=lambda loc=location: self.dropoff_var.set(loc))

        # If current dropoff equals pickup, reset it to another option
        if self.dropoff_var.get() == selected_pickup:
            for alt in LOCATIONS:
                if alt != selected_pickup:
                    self.dropoff_var.set(alt)
                    break

        self._update_cost()


    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def _go_back_to_booking_page(self):
        # Determine which booking page to go back to based on the current vehicle type
        vehicle_type = self.controller.current_booking_details.get("vehicle_type")
        if "Enavroom" in vehicle_type:
            self.controller.show_frame("BookEnavroomPage")
        elif "Car" in vehicle_type:
            self.controller.show_frame("BookEnacarPage")
        else:
            # Fallback in case vehicle type isn't set
            self.controller.show_frame("HomePage")

    def _update_cost(self, *args):
        pickup = self.pickup_var.get()
        dropoff = self.dropoff_var.get()
        vehicle_type = self.controller.current_booking_details.get("vehicle_type", "Enavroom-vroom") # Default if not set

        distance = get_distance(pickup, dropoff)
        cost = self.controller.booking_system.calculate_cost(vehicle_type, distance)
        self.cost_label.config(text=f"Estimated Cost: ₱{cost:.2f}")

        # Update controller's booking details
        self.controller.update_booking_details(
            pickup_location=pickup,
            dropoff_location=dropoff,
            distance=distance,
            cost=cost
        )

    def _on_book_now(self):
        # Trigger the actual booking logic, then navigate to MapPage
        current_details = self.controller.current_booking_details
        if not current_details["pickup_location"] or not current_details["dropoff_location"]:
            messagebox.showwarning("Missing Information", "Please select both pickup and drop-off locations.")
            return
        
        # This is where the actual booking happens
        new_booking = self.controller.booking_system.book(
            current_details["vehicle_type"],
            current_details["pickup_location"],
            current_details["dropoff_location"],
            current_details["payment_method"]
        )
        self.controller.update_booking_details(booking_id=new_booking.id) # Store booking ID

        # PUandDO.py -> map.py
        self.controller.show_frame("MapPage")

    def on_show(self):
        # Set default locations or previously selected locations on show
        details = self.controller.current_booking_details
        self.pickup_var.set(details.get("pickup_location", LOCATIONS[0]))
        self.dropoff_var.set(details.get("dropoff_location", LOCATIONS[1]))
        self._update_cost() # Recalculate cost based on potentially updated locations

class MapPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)
        self._create_header("Confirm Route", lambda: controller.show_frame("PUandDOPage"))

        self.map_label = tk.Label(self, bg=GRAY_LIGHT)
        self.map_label.pack(fill="both", expand=True, pady=(10, 0))


        # Display route details
        self.route_label = tk.Label(self, text="", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR, wraplength=300)
        self.route_label.pack(pady=(10, 5))

        self.cost_label = tk.Label(self, text="", font=FONT_PRICE, bg=GRAY_LIGHT, fg=PURPLE_DARK)
        self.cost_label.pack(pady=(0, 10))

        book_now_button = tk.Button(self, text="Book Now", command=self._on_book_now,
        font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
        padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=30, pady=(10, 10))

    
    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def on_show(self):

    # Update route and cost details
        details = self.controller.current_booking_details
        pickup = details.get('pickup_location')
        dropoff = details.get('dropoff_location')
        distance = details.get('distance')
        cost = details.get('cost')

        # Determine map image based on pickup/dropoff
        image_name = ROUTE_IMAGE_MAP.get((pickup, dropoff), "default_map.png")
        map_img = load_image(image_name, (375, 300))

        if map_img:
            self.map_label.configure(image=map_img)
            self.map_label.image = map_img
        else:
            self.map_label.configure(text=f"No map for route\n({pickup} → {dropoff})", image='', font=("Arial", 12), fg="gray")

        self.route_label.config(text=f"From: {pickup}\nTo: {dropoff}\nDistance: {distance:.1f} km")
        self.cost_label.config(text=f"Total Cost: ₱{cost:.2f}")

    def _on_book_now(self):
        # map.py -> loading_page.py
        self.controller.show_frame("LoadingPage")

class LoadingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.loading_label = tk.Label(self, text="Finding a driver...", font=("Arial", 20, "bold"), bg=GRAY_LIGHT, fg=TEXT_COLOR)
        self.loading_label.pack(pady=100)

        # Simple animation for loading dots
        self.dots_count = 0
        self.after_id = None # To store the after method ID for cancellation

        cancel_button = tk.Button(self, text="Cancel Booking", command=self._on_cancel_booking,
                                   font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                   padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        cancel_button.pack(pady=30)

    def on_show(self):
        self.dots_count = 0
        self._animate_loading()
        # Schedule the transition after a delay (e.g., 3 seconds)
        # Cancel any previous pending transition
        if hasattr(self, 'transition_id') and self.transition_id:
            self.after_cancel(self.transition_id)
        self.transition_id = self.after(3000, self._transition_to_driver_found) # 3 seconds delay

    def on_hide(self):
        # Stop animation when leaving the page
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, 'transition_id') and self.transition_id:
            self.after_cancel(self.transition_id)
            self.transition_id = None

    def _animate_loading(self):
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.loading_label.config(text=f"Finding a driver{dots}")
        self.after_id = self.after(500, self._animate_loading) # Update every 500ms

    def _transition_to_driver_found(self):
        self.on_hide() # Stop animation and pending transitions
        vehicle_type = self.controller.current_booking_details.get("vehicle_type")
        if "Car" in vehicle_type:
            self.controller.show_frame("WeFoundDriverEnacarPage")
        else: # Default to Enavroom-vroom
            self.controller.show_frame("WeFoundDriverEnavroomPage")

    def _on_cancel_booking(self):
        # cancel booking -> home_page.py
        booking_id = self.controller.current_booking_details.get("booking_id")
        if booking_id and self.controller.booking_system.cancel(booking_id):
            messagebox.showinfo("Cancelled", "Your booking has been cancelled.")
        else:
            messagebox.showwarning("Error", "Could not cancel booking or no active booking found.")
        self.controller.show_frame("HomePage")
        self.on_hide() # Stop any ongoing animations/timers

class WeFoundDriverBasePage(tk.Frame):
    """Base class for 'We Found Your Driver' pages."""
    def __init__(self, parent, controller, vehicle_type_display, driver_icon):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.vehicle_type_display = vehicle_type_display
        self.driver_icon = driver_icon

        self._create_header("Driver Found!", lambda: self._on_cancel_ride()) # "Cancel Ride"

        tk.Label(self, text=f"We found your driver for your {self.vehicle_type_display}!", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR, wraplength=300).pack(pady=20)

        # Driver icon
        driver_img = load_image(self.driver_icon, (100, 100), is_circular=True)
        if driver_img:
            driver_label = tk.Label(self, image=driver_img, bg=GRAY_LIGHT)
            driver_label.image = driver_img
            driver_label.pack(pady=10)
        else:
            tk.Label(self, text="Driver Pic", font=("Arial", 16), bg="lightgray", width=10, height=5).pack(pady=10)

        tk.Label(self, text="Driver Name: John Doe", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)
        tk.Label(self, text="Plate No: ABC 123", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)
        tk.Label(self, text="ETA: 5 mins", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)

        self.cancel_button = tk.Button(self, text="Cancel Ride", command=self._on_cancel_ride,
                                         font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                         padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        self.cancel_button.pack(pady=(20, 10))

        self.after_id_transition = None # To hold transition to DonePage

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)
        
        # Adding a simple 'x' button for consistency in cancelling at this stage
        cancel_btn = tk.Button(header_frame, text="X", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14), cursor="hand2")
        cancel_btn.place(relx=0.9, rely=0.5, anchor="center") # Top right corner

    def on_show(self):
        # Automatically transition to DonePage after a delay
        if self.after_id_transition:
            self.after_cancel(self.after_id_transition)
        self.after_id_transition = self.after(5000, self._transition_to_done) # 5 seconds delay to done page

    def on_hide(self):
        if self.after_id_transition:
            self.after_cancel(self.after_id_transition)
            self.after_id_transition = None

    def _on_cancel_ride(self):
        # If cancel button clicked -> HomePage
        booking_id = self.controller.current_booking_details.get("booking_id")
        if booking_id and self.controller.booking_system.cancel(booking_id):
            messagebox.showinfo("Ride Cancelled", "Your ride has been cancelled.")
        else:
            messagebox.showwarning("Error", "Could not cancel ride or no active booking found.")
        self.controller.show_frame("HomePage")
        self.on_hide()

    def _transition_to_done(self):
        self.on_hide()
        self.controller.show_frame("DonePage")


class WeFoundDriverEnacarPage(WeFoundDriverBasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Car", "driver_car.png") # Driver icon specific to car

class WeFoundDriverEnavroomPage(WeFoundDriverBasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Enavroom-vroom", "driver_moto.png") # Driver icon specific to moto


class DonePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Ride Completed!", lambda: self.controller.show_frame("HomePage")) # Back to home

        tk.Label(self, text="Your ride is complete!", font=("Arial", 20, "bold"), bg=GRAY_LIGHT, fg=GREEN_COLOR).pack(pady=50)
        
        # Summary of the booking
        self.summary_label = tk.Label(self, text="", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR, wraplength=300, justify="center")
        self.summary_label.pack(pady=20)

        done_button = tk.Button(self, text="Done", command=lambda: controller.show_frame("HomePage"),
                                font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        done_button.pack(pady=(20, 10))

        exit_button = tk.Button(self, text="Exit Application", command=controller.exit_app,
                                font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        exit_button.pack(pady=5)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def on_show(self):
        # Display final booking details
        details = self.controller.current_booking_details
        summary_text = (
            f"Vehicle: {details.get('vehicle_type', 'N/A')}\n"
            f"From: {details.get('pickup_location', 'N/A')}\n"
            f"To: {details.get('dropoff_location', 'N/A')}\n"
            f"Distance: {details.get('distance', 0):.1f} km\n"
            f"Total Paid: ₱{details.get('cost', 0):.2f} ({details.get('payment_method', 'N/A')})"
        )
        self.summary_label.config(text=summary_text)
        # Clear current booking details after showing the done page
        self.controller.current_booking_details = {
            "vehicle_type": "", "pickup_location": "", "dropoff_location": "",
            "distance": 0, "cost": 0, "payment_method": "Cash", "booking_id": None
        }

# --- Main execution block ---
if __name__ == "__main__":
    # Define dummy image files and their sizes for automatic creation
    # Make sure these names match the ones used in the UI code
    dummy_images = {
        "enavroom_logo.png": (250, 80), # For StartPage and HomePage header logo
        "moto_taxi.png": (60, 60),      # For HomePage service icon (should be circular)
        "car.png": (60, 60),            # For HomePage service icon (should be circular)
        "home.png": (30, 30),           # For navigation bar icon
        "message.png": (30, 30),        # For navigation bar icon
        "history.png": (30, 30),        # For navigation bar icon
        "arrow.png": (25, 25),          # For back button
        "enavroom.png": (30, 30),       # Booking page Enavroom-vroom icon (not circular)
        "enacar_2.png": (50, 50),       # Booking page Car icon (not circular)
        "cash_2.png": (30, 30),         # Booking page cash icon
        "wallet_2.png": (30, 30),       # Booking page wallet icon
        "main_lhs_map.png": (375, 160), # Booking page map (generic map)
        "driver_moto.png": (100, 100),  # Driver icon for moto (circular)
        "driver_car.png": (100, 100)    # Driver icon for car (circular)
    }

    # Ensure the IMAGE_BASE_PATH exists
    if not os.path.exists(IMAGE_BASE_PATH):
        os.makedirs(IMAGE_BASE_PATH)
        print(f"Created directory: {IMAGE_BASE_PATH}")

    # Create dummy image files if they don't exist
    for img_name, img_size in dummy_images.items():
        filepath = os.path.join(IMAGE_BASE_PATH, img_name)
        if not os.path.exists(filepath):
            try:
                # Specific dummy image generation for better visual representation
                if "enavroom_logo.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='purple')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "ENAVROOM", fill=(255,255,255), font=font)
                elif "moto_taxi.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color='orange')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(255, 165, 0)) # Orange circle background
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.4))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.2, img_size[1]*0.3), "Bike", fill=(0,0,0), font=font)
                elif "car.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color='blue')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(0, 0, 255)) # Blue circle background
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.4))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.25, img_size[1]*0.3), "Car", fill=(255,255,255), font=font)
                elif "enavroom.png" in img_name: # Rectangle
                    dummy_img = Image.new('RGB', img_size, color='purple')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "E-V", fill=(255,255,255), font=font)
                elif "enacar_2.png" in img_name: # Rectangle
                    dummy_img = Image.new('RGB', img_size, color='darkgreen')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Car", fill=(255,255,255), font=font)
                elif "cash_2.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='green')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Cash", fill=(255,255,255), font=font)
                elif "wallet_2.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='blue')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Wal", fill=(255,255,255), font=font)
                elif "arrow.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color = 'darkgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.7))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((int(img_size[0]*0.2), -2), "<", fill=(0,0,0), font=font)
                elif "driver_moto.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color = 'red')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(255, 0, 0)) # Red circle
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.3))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.1, img_size[1]*0.35), "Driver", fill=(255,255,255), font=font)
                elif "driver_car.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color = 'darkblue')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(0, 0, 139)) # Dark blue circle
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.3))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.15, img_size[1]*0.35), "Driver", fill=(255,255,255), font=font)
                elif "_icon.png" in img_name or ".png" in img_name: # Generic icon placeholder for nav bar, etc.
                    dummy_img = Image.new('RGB', img_size, color='lightgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    text_to_draw = img_name.split('.')[0][0].upper()
                    if "message" in img_name: text_to_draw = "Msg"
                    d.text((5,5), text_to_draw, fill=(0,0,0), font=font)
                else: # Default for other images, e.g., maps
                    dummy_img = Image.new('RGB', img_size, color = 'lightgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.15))
                    except IOError:
                        font = ImageFont.load_default()
                    text_on_map = img_name.replace(".png", "").replace("_", " ").title()
                    bbox = d.textbbox((0, 0), text_on_map, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (img_size[0] - text_width) / 2
                    y = (img_size[1] - text_height) / 2
                    d.text((x, y), text_on_map, fill=(0,0,0), font=font)
                
                dummy_img.save(filepath)
                print(f"Created dummy image: {filepath}")
            except Exception as e:
                print(f"Could not create dummy image {filepath}: {e}")

    app = App()
    app.mainloop()

