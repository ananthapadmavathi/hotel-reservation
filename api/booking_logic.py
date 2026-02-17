import os
import random
from pymongo import MongoClient

# ==============================
# MongoDB Connection
# ==============================

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable not set")

client = MongoClient(MONGO_URI)
db = client["hotelDB"]
collection = db["bookings"]

# ==============================
# Room Model
# ==============================

ALL_ROOMS = {
    floor: (
        [1000 + i for i in range(1, 8)] if floor == 10
        else [floor * 100 + i for i in range(1, 11)]
    )
    for floor in range(1, 11)
}

MAX_BULK = 5


# ==============================
# Helper Functions
# ==============================

def get_next_booking_id():
    last = collection.find_one(sort=[("id", -1)])
    return 1 if not last else last["id"] + 1


def get_all_bookings():
    bookings = []
    for b in collection.find({}, {"_id": 0}):
        bookings.append(b)
    return bookings


def get_occupied():
    occ = []
    for b in collection.find():
        occ += b["rooms"]
    return set(occ)


def available_on_floor(floor):
    occ = get_occupied()
    return [r for r in ALL_ROOMS[floor] if r not in occ]


def room_exists(room: int) -> bool:
    return any(room in rooms for rooms in ALL_ROOMS.values())


def is_occupied(room: int) -> bool:
    return room in get_occupied()


# ==============================
# Booking Logic
# ==============================

def commit_single(room: int):
    bid = get_next_booking_id()
    collection.insert_one({
        "id": bid,
        "rooms": [room]
    })
    return [room], bid


def bulk_allocate(count: int):
    if count < 1:
        return None, "Invalid count"

    if count > MAX_BULK:
        return None, f"Bulk booking limit exceeded (max {MAX_BULK})"

    free_by_floor = {f: available_on_floor(f) for f in range(1, 11)}
    best_floor = max(free_by_floor, key=lambda f: len(free_by_floor[f]))

    result = []
    need = count

    # Step 1: Allocate from best floor
    take = min(need, len(free_by_floor[best_floor]))
    result += free_by_floor[best_floor][:take]
    need -= take

    # Step 2: Spillover to nearest floors
    if need > 0:
        other_floors = sorted(
            [f for f in range(1, 11) if f != best_floor],
            key=lambda f: abs(f - best_floor)
        )

        for f in other_floors:
            if need == 0:
                break

            rooms = free_by_floor[f]
            if rooms:
                take = min(need, len(rooms))
                result += rooms[:take]
                need -= take

    if need > 0:
        return None, "Not enough rooms available"

    bid = get_next_booking_id()
    collection.insert_one({
        "id": bid,
        "rooms": result
    })

    return result, bid


def commit_booking(value: int):
    """
    value >=100 => single room
    1 <= value <= 5 => bulk booking
    """
    if value >= 100:
        if not room_exists(value):
            return None, "Room does not exist"

        if is_occupied(value):
            return None, "Room already occupied"

        return commit_single(value)

    return bulk_allocate(value)


# ==============================
# Other Operations
# ==============================

def vacate_booking(bid: int):
    collection.delete_one({"id": bid})


def reset_hotel():
    collection.delete_many({})


def random_room():
    free = [
        r for f in ALL_ROOMS
        for r in ALL_ROOMS[f]
        if r not in get_occupied()
    ]
    return random.choice(free) if free else None
