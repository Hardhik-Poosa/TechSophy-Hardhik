# scripts/generate_category_dataset.py
from __future__ import annotations

import csv
import random
from pathlib import Path

OUTPUT_PATH = Path("data/training_categories.csv")

CATEGORIES = {
    "Food": [
        "ZOMATO Order",
        "SWIGGY Order",
        "Dominos Pizza HYD",
        "KFC Food Court",
        "McDonalds Drive Thru",
        "Subway Sandwich",
        "Coffee Cafe HYD",
        "CCD Cafe Coffee Day",
        "Starbucks Jubilee Hills",
        "IRCTC Catering",
        "Hostel Canteen",
    ],
    "Travel": [
        "UBER TRIP HYD",
        "OLA CAB RIDE",
        "Rapido Bike Ride",
        "TSRTC BUS TICKET",
        "Metro Rail Card Reload",
        "IndiGo Flight Booking",
        "IRCTC Train Ticket",
        "Petrol Bunk HP",
        "Fuel IOC Pump",
    ],
    "Shopping": [
        "Amazon purchase",
        "Flipkart Online",
        "Myntra Fashion",
        "Reliance Trends",
        "D Mart Groceries",
        "Big Bazaar Mall",
        "Electronics Store HYD",
        "Croma Retail",
        "Apple Store Online",
        "Local Kirana Store",
    ],
    "Utilities": [
        "Electricity Bill TSSPDCL",
        "Water Bill HMWSSB",
        "Gas Bill HP",
        "Mobile Recharge Jio",
        "Mobile Recharge Airtel",
        "Broadband ACT Fibernet",
        "Internet Bill JioFiber",
        "DTH Recharge TataSky",
    ],
    "Rent": [
        "House Rent Transfer",
        "Hostel Fee Payment",
        "PG Rent Gachibowli",
        "Room Rent UPI",
        "Apartment Maintenance Fee",
    ],
    "Entertainment": [
        "PVR Cinemas Ticket",
        "INOX Multiplex",
        "Netflix Subscription",
        "Spotify Premium",
        "SonyLIV Monthly",
        "Hotstar Annual",
        "Gaming Steam Purchase",
        "Play Store Movies",
    ],
    "Education": [
        "College Tuition Fee",
        "Coursera Course",
        "Udemy Online Course",
        "Byjus Subscription",
        "Exam Registration Fee",
        "Library Fine",
        "Book Store Purchase",
    ],
    "Health": [
        "Apollo Pharmacy",
        "MedPlus Medicine",
        "Diagnostic Center Test",
        "Hospital Bill",
        "Clinic Consultation",
        "Health Insurance Premium",
    ],
}


def synthesize_description(base: str) -> str:
    """Add some noise like transaction id, city, amount, date bits."""
    cities = ["HYD", "BLR", "MUM", "DEL", "PUNE"]
    suffixes = [
        "",
        " TXNID 9" + str(random.randint(1000, 9999)),
        " Ref " + str(random.randint(11111, 99999)),
        " " + random.choice(cities),
    ]
    amounts = [f"{random.randint(100, 5000)} INR", f"Rs {random.randint(50, 3000)}"]
    patterns = [
        base,
        f"{base} {random.choice(amounts)}",
        f"{base} {random.choice(suffixes)}",
        f"{base} {random.choice(amounts)} {random.choice(suffixes)}",
    ]
    return random.choice(patterns)


def generate_rows(num_rows: int = 400) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    all_pairs: list[tuple[str, str]] = []

    for category, bases in CATEGORIES.items():
        for b in bases:
            all_pairs.append((b, category))

    for _ in range(num_rows):
        base, cat = random.choice(all_pairs)
        desc = synthesize_description(base)
        rows.append({"description": desc, "category": cat})

    return rows


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows(num_rows=400)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["description", "category"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"[INFO] Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
