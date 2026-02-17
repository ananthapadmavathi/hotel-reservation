from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import booking_logic as logic

app = FastAPI()

# Enable CORS (allow frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Get Room Status
# ==============================

@app.get("/rooms/status")
def status():
    """
    Returns floors 1-10 with occupied & booking IDs
    Used by frontend grid renderer
    """
    bookings = logic.get_all_bookings()

    occ = {}
    for b in bookings:
        for r in b["rooms"]:
            occ[r] = b["id"]

    result = {}
    for floor in range(1, 11):
        result[floor] = [
            {
                "room": r,
                "occupied": r in occ,
                "booking_id": occ.get(r)
            }
            for r in logic.ALL_ROOMS[floor]
        ]

    return result


# ==============================
# Book Room(s)
# ==============================

@app.post("/book")
def book(value: int):
    """
    Booking interpretation handled in frontend:
      - >=100 => single room
      - 1-5   => bulk
    """
    rooms, bid_or_err = logic.commit_booking(value)

    if rooms is None:
        raise HTTPException(status_code=400, detail=bid_or_err)

    return {
        "status": "booked",
        "booking_id": bid_or_err,
        "rooms": rooms
    }


# ==============================
# Vacate Booking
# ==============================

@app.post("/vacate")
def vacate(bid: int):
    logic.vacate_booking(bid)
    return {"status": "vacated", "booking_id": bid}


# ==============================
# Reset Hotel
# ==============================

@app.post("/reset")
def reset():
    logic.reset_hotel()
    return {"status": "reset"}


# ==============================
# Random Room Booking
# ==============================

@app.post("/random")
def random():
    rm = logic.random_room()

    if rm is None:
        raise HTTPException(status_code=400, detail="No rooms available")

    rooms, bid = logic.commit_single(rm)

    return {
        "status": "booked",
        "booking_id": bid,
        "rooms": rooms
    }


# ==============================
# Get All Bookings
# ==============================

@app.get("/bookings")
def bookings():
    return logic.get_all_bookings()
