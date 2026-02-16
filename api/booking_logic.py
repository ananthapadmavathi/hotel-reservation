# api/booking_logic.py

import random

# Build room model
# Floors 1-9 => 101-110, 201-210, ...
# Floor 10 => 1001-1007 (7 rooms)
ALL_ROOMS = {
    floor: (
        [1000 + i for i in range(1, 8)] if floor == 10
        else [floor * 100 + i for i in range(1, 11)]
    )
    for floor in range(1, 11)
}

state = {
    "next_booking_id": 1,
    "bookings": []
}

MAX_BULK = 5


def floor_of(room: int) -> int:
    if room >= 1000:
        return 10
    return room // 100


def get_occupied():
    occ = []
    for b in state["bookings"]:
        occ += b["rooms"]
    return set(occ)


def available_on_floor(f):
    occ = get_occupied()
    return [r for r in ALL_ROOMS[f] if r not in occ]


def is_occupied(room: int) -> bool:
    return room in get_occupied()


def room_exists(room: int) -> bool:
    return any(room in rooms for rooms in ALL_ROOMS.values())


def commit_single(room: int):
    bid = state["next_booking_id"]
    state["next_booking_id"] += 1
    state["bookings"].append({"id": bid, "rooms": [room]})
    return [room], bid


def bulk_allocate(count: int):
    """
    Bulk logic for <=5 rooms:
    1. Find floor with max free rooms
    2. Allocate as many as possible
    3. Spillover to nearest floors by floor distance
    4. If insufficient -> fail
    """
    if count > MAX_BULK:
        return None, f"Bulk booking limit exceeded (max {MAX_BULK})"

    occ = get_occupied()
    free_by_floor = {f: available_on_floor(f) for f in range(1, 11)}

    # STEP 1: Find best floor by free count (desc)
    best_floor = max(free_by_floor, key=lambda f: len(free_by_floor[f]))

    result = []
    need = count

    # STEP 2: Allocate from best floor first
    take = min(need, len(free_by_floor[best_floor]))
    result += free_by_floor[best_floor][:take]
    need -= take

    # STEP 3: Spillover across nearest floors
    if need > 0:
        # floors sorted by travel distance from best_floor
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
        return None, "Not enough rooms available for bulk booking"

    # STEP 4: Commit booking
    bid = state["next_booking_id"]
    state["next_booking_id"] += 1
    state["bookings"].append({"id": bid, "rooms": result})
    return result, bid


def commit_bulk_from_count(value: int):
    if value < 1:
        return None, "Invalid count"
    if value > MAX_BULK:
        return None, f"Bulk booking limit exceeded (max {MAX_BULK})"
    return bulk_allocate(value)


def commit_booking(value: int):
    """
    Called from API:
    value >=100 => single room
    1 <= value <= 5 => bulk rooms
    """
    if value >= 100:
        if not room_exists(value):
            return None, "Room does not exist"
        if is_occupied(value):
            return None, "Room already occupied"
        return commit_single(value)

    # bulk
    return commit_bulk_from_count(value)


def vacate_booking(bid: int):
    state["bookings"] = [b for b in state["bookings"] if b["id"] != bid]


def reset_hotel():
    state["next_booking_id"] = 1
    state["bookings"] = []


def random_room():
    free = [r for f in ALL_ROOMS for r in ALL_ROOMS[f] if r not in get_occupied()]
    return random.choice(free) if free else None
