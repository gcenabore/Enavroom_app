import json
import uuid
import math

# --- Booking System Logic (Copied from previous code) ---
LOCATIONS = ["PUP Main", "CEA", "Hasmin", "iTech", "COC", "PUP LHS", "Condotel"]

DISTANCE_MATRIX = {
    ("PUP Main", "CEA"): 2.0, 
    ("PUP Main", "Hasmin"): 1.5, 
    ("PUP Main", "iTech"): 1.2,
    ("PUP Main", "COC"): 1.0, 
    ("PUP Main", "PUP LHS"): 1.7, 
    ("PUP Main", "Condotel"): 1.5,
    ("CEA", "Hasmin"): 2.0, 
    ("CEA", "iTech"): 5.0, 
    ("CEA", "COC"): 4.5,
    ("CEA", "PUP LHS"): 4.0, 
    ("CEA", "Condotel"): 4.5,
    ("Hasmin", "iTech"): 4.0, 
    ("Hasmin", "COC"): 3.5, 
    ("Hasmin", "PUP LHS"): 0.5,
    ("Hasmin", "Condotel"): 1.5,
    ("iTech", "COC"): 0.5, 
    ("iTech", "PUP LHS"): 2.5, 
    ("iTech", "Condotel"): 0.5,
    ("COC", "PUP LHS"): 2.0, 
    ("COC", "Condotel"): 1.0,
    ("PUP LHS", "Condotel"): 2.0,
}

ROUTE_IMAGE_MAP = {
    ("PUP Main", "CEA"): "pup_main_to_cea.jpg",
    ("CEA", "PUP Main"): "pup_main_to_cea.jpg",

    ("PUP Main", "Hasmin"): "pup_main_to_hasmin.jpg",
    ("Hasmin", "PUP Main"): "pup_main_to_hasmin.jpg",

    ("PUP Main", "iTech"): "pup_main_to_itech.jpg",
    ("iTech", "PUP Main"): "pup_main_to_itech.jpg",

    ("PUP Main", "COC"): "pup_main_to_coc.jpg",
    ("COC", "PUP Main"): "pup_main_to_coc.jpg",

    ("PUP Main", "PUP LHS"): "pup_main_to_pup_lhs.png",
    ("PUP LHS", "PUP Main"): "pup_main_to_pup_lhs.png",

    ("PUP Main", "Condotel"): "pup_main_to_condotel.jpg",
    ("Condotel", "PUP Main"): "pup_main_to_condotel.jpg",

    ("CEA", "Hasmin"): "cea_to_hasmin.jpg",
    ("Hasmin", "CEA"): "cea_to_hasmin.jpg",

    ("CEA", "iTech"): "cea_to_itech.jpg",
    ("iTech", "CEA"): "cea_to_itech.jpg",

    ("CEA", "COC"): "cea_to_coc.jpg",
    ("COC", "CEA"): "cea_to_coc.jpg",

    ("CEA", "PUP LHS"): "cea_to_pup_lhs.jpg",
    ("PUP LHS", "CEA"): "cea_to_pup_lhs.jpg",

    ("CEA", "Condotel"): "cea_to_condotel.jpg",
    ("Condotel", "CEA"): "cea_to_condotel.jpg",

    ("Hasmin", "iTech"): "hasmin_to_itech.jpg",
    ("iTech", "Hasmin"): "hasmin_to_itech.jpg",

    ("Hasmin", "COC"): "hasmin_to_coc.jpg",
    ("COC", "Hasmin"): "hasmin_to_coc.jpg",

    ("Hasmin", "PUP LHS"): "hasmin_to_pup_lhs.jpg",
    ("PUP LHS", "Hasmin"): "hasmin_to_pup_lhs.jpg",

    ("Hasmin", "Condotel"): "hasmin_to_condotel.jpg",
    ("Condotel", "Hasmin"): "hasmin_to_condotel.jpg",

    ("iTech", "COC"): "itech_to_coc.jpg",
    ("COC", "iTech"): "itech_to_coc.jpg",

    ("iTech", "PUP LHS"): "itech_to_pup_lhs.jpg",
    ("PUP LHS", "iTech"): "itech_to_pup_lhs.jpg",

    ("iTech", "Condotel"): "itech_to_condotel.jpg",
    ("Condotel", "iTech"): "itech_to_condotel.jpg",

    ("COC", "PUP LHS"): "coc_to_pup_lhs.jpg",
    ("PUP LHS", "COC"): "coc_to_pup_lhs.jpg",

    ("COC", "Condotel"): "coc_to_condotel.jpg",
    ("Condotel", "COC"): "coc_to_condotel.jpg",

    ("PUP LHS", "Condotel"): "pup_lhs_to_condotel.jpg",
    ("Condotel", "PUP LHS"): "pup_lhs_to_condotel.jpg"
}

_temp_matrix = {}
for (loc1, loc2), dist in DISTANCE_MATRIX.items():
    _temp_matrix[(loc1, loc2)] = dist
    _temp_matrix[(loc2, loc1)] = dist
    
DISTANCE_MATRIX = _temp_matrix


VEHICLE_SURCHARGES = {
    "Enavroom-vroom": 0,
    "Car (4-seater)": 20,
    "Car (6-seater)": 30
}

BASE_PRICES = {
    "Enavroom-vroom": 75,
    "Car (4-seater)": 250,
    "Car (6-seater)": 450
}

def get_distance(start, end):
    if start == end:
        return 0
    distance = DISTANCE_MATRIX.get((start, end))
    if distance is None:
        distance = DISTANCE_MATRIX.get((end, start), 0)
    return distance

class Booking:
    def __init__(self, vehicle_type, start, end, distance, cost, payment_method="Cash", status ="active"):

        self.id = str(uuid.uuid4())[:8]
        self.vehicle_type = vehicle_type
        self.start = start
        self.end = end
        self.distance = distance
        self.cost = cost
        self.payment_method = payment_method
        self.status = status

    def to_dict(self):
        return self.__dict__

class BookingSystem:
    def __init__(self, file="bookings.json"):
        self.file = file
        self.bookings = []
        self.load()

    def calculate_cost(self, vehicle_type, distance):
        base_fare = BASE_PRICES.get(vehicle_type, 75)
        if distance > 1:
            additional_km = math.ceil(distance - 1)
            base_fare += additional_km * 10
        surcharge = VEHICLE_SURCHARGES.get(vehicle_type, 0)
        return base_fare + surcharge

    def book(self, vehicle_type, start, end, payment_method="Cash"):
        distance = get_distance(start, end)
        cost = self.calculate_cost(vehicle_type, distance)
        booking = Booking(vehicle_type, start, end, distance, cost, payment_method)
        self.bookings.append(booking)
        print(f"DEBUG: New booking created: {booking.to_dict()}")
        return booking


    def cancel(self, booking_id):
        for booking in self.bookings:
            if booking.id == booking_id:
                booking.status = "cancelled"
                self.save()
                self.log_to_txt(booking, action="Cancelled")  # <- NEW
                return True
        return False


    def save(self):
        with open(self.file, "w") as f:
            json.dump([b.to_dict() for b in self.bookings], f, indent=2)

    def log_to_txt(self, booking, action="Booked"):
        log_entry = (
            f"{action.upper()} | ID: {booking.id} | "
            f"{booking.vehicle_type} | {booking.start} → {booking.end} | "
            f"{booking.distance:.1f} km | ₱{booking.cost:.2f} | "
            f"{booking.payment_method} | STATUS: {booking.status}\n"
        )
        with open("booking_log.txt", "a", encoding="utf-8") as log_file:  # <-- add encoding
            log_file.write(log_entry)

    def load(self):
        try:
            with open(self.file, "r") as f:
                data = json.load(f)
                self.bookings = [Booking(**d) for d in data]
        except:
            self.bookings = []

    def clear_all(self):
        self.bookings = []
        self.save()

