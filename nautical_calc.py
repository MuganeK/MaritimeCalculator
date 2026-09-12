import math
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# The expanded database of regional port coordinates and their local time zones
PORT_DATABASE = {
    "mombasa": {
        "name": "Port of Mombasa (Kenya)",
        "lat": -4.0435,
        "lon": 39.6682,
        "tz": "Africa/Nairobi",
    },
    "dar es salaam": {
        "name": "Port of Dar es Salaam (Tanzania)",
        "lat": -6.8200,
        "lon": 39.2796,
        "tz": "Africa/Nairobi",
    },
    "zanzibar": {
        "name": "Port of Zanzibar (Tanzania)",
        "lat": -6.1612,
        "lon": 39.1864,
        "tz": "Africa/Nairobi",
    },
    "port victoria": {
        "name": "Port Victoria (Seychelles)",
        "lat": -4.6222,
        "lon": 55.4514,
        "tz": "Indian/Mahe",
    },
    "diego suarez": {
        "name": "Port of Diego Suarez / Antsiranana (Madagascar)",
        "lat": -12.2725,
        "lon": 49.2892,
        "tz": "Indian/Antananarivo",
    },
    "mogadishu": {
        "name": "Port of Mogadishu (Somalia)",
        "lat": 2.0469,
        "lon": 45.3182,
        "tz": "Africa/Mogadishu",
    },
    "kismayo": {
        "name": "Port of Kismayo (Somalia)",
        "lat": -0.3582,
        "lon": 42.5454,
        "tz": "Africa/Mogadishu",
    },
    "bosaso": {
        "name": "Port of Bosaso (Somalia)",
        "lat": 11.2842,
        "lon": 49.1816,
        "tz": "Africa/Mogadishu",
    },
    "berbera": {
        "name": "Port of Berbera (Somalia)",
        "lat": 10.4396,
        "lon": 45.0143,
        "tz": "Africa/Mogadishu",
    },
    "marka (merca)": {
        "name": "Port of Marka / Merca (Somalia)",
        "lat": 1.7159,
        "lon": 44.7717,
        "tz": "Africa/Mogadishu",
    },
    "eyl": {
        "name": "Port of Eyl (Somalia)",
        "lat": 7.9803,
        "lon": 49.8164,
        "tz": "Africa/Mogadishu",
    },
    "lamu": {
        "name": "Lamu Port (Kenya)",
        "lat": -2.2717,
        "lon": 40.9020,
        "tz": "Africa/Nairobi",
    },
    "malindi": {
        "name": "Malindi Port (Kenya)",
        "lat": -3.2192,
        "lon": 40.1169,
        "tz": "Africa/Nairobi",
    },
    "tanga": {
        "name": "Port of Tanga (Tanzania)",
        "lat": -5.0689,
        "lon": 39.0982,
        "tz": "Africa/Nairobi",
    },
    "pemba island": {
        "name": "Pemba Island Port (Tanzania)",
        "lat": -5.2459,
        "lon": 39.7689,
        "tz": "Africa/Nairobi",
    },
    "moroni": {
        "name": "Port of Moroni (Comoros)",
        "lat": -11.7172,
        "lon": 43.2473,
        "tz": "Indian/Comoro",
    },
    "shimoni": {
        "name": "Port of Shimoni (Kenya)",
        "lat": -4.6476,
        "lon": 39.3817,
        "tz": "Africa/Nairobi",
    },
    "port louis": {
        "name": "Port Louis (Mauritius)",
        "lat": -20.1609,
        "lon": 57.5012,
        "tz": "Indian/Mauritius",
    },
}


def validate_coordinate(name, value):
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")

    if name == "lat" and not -90 <= value <= 90:
        raise ValueError("Latitude must be between -90 and 90")
    if name == "lon" and not -180 <= value <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    return float(value)


def validate_speed(speed):
    if speed <= 0:
        raise ValueError("Speed must be greater than zero")
    return float(speed)


def calculate_distance_and_course(lat1, lon1, lat2, lon2):
    lat1 = validate_coordinate("lat", lat1)
    lon1 = validate_coordinate("lon", lon1)
    lat2 = validate_coordinate("lat", lat2)
    lon2 = validate_coordinate("lon", lon2)

    rad_lat1, rad_lon1 = math.radians(lat1), math.radians(lon1)
    rad_lat2, rad_lon2 = math.radians(lat2), math.radians(lon2)

    dlat = rad_lat2 - rad_lat1
    dlon = rad_lon2 - rad_lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(rad_lat1) * math.cos(rad_lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    earth_radius_nm = 3440.06
    distance_nm = earth_radius_nm * c

    x = math.sin(dlon) * math.cos(rad_lat2)
    y = (
        math.cos(rad_lat1) * math.sin(rad_lat2)
        - math.sin(rad_lat1) * math.cos(rad_lat2) * math.cos(dlon)
    )

    initial_bearing = math.atan2(x, y)
    compass_course = (math.degrees(initial_bearing) + 360) % 360

    return round(distance_nm, 2), round(compass_course, 1)


def calculate_eta(distance_nm, speed_knots, destination_tz, departure_time=None):
    speed_knots = validate_speed(speed_knots)
    if distance_nm < 0:
        raise ValueError("Distance must not be negative")

    duration_hours = distance_nm / speed_knots
    current_time = departure_time or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    eta_time = current_time + timedelta(hours=duration_hours)
    localized_eta = eta_time.astimezone(ZoneInfo(destination_tz))

    return duration_hours, localized_eta


def estimate_fuel(distance_nm, speed_knots, consumption_lph=1750):
    if distance_nm < 0:
        raise ValueError("Distance must not be negative")

    speed_knots = validate_speed(speed_knots)
    if consumption_lph < 0:
        raise ValueError("Fuel consumption must not be negative")
    hours = distance_nm / speed_knots
    return round(hours * consumption_lph, 2)


def estimate_fuel_cost(litres, price_per_litre=218):
    if litres < 0:
        raise ValueError("Fuel litres must not be negative")
    if price_per_litre < 0:
        raise ValueError("Fuel price must not be negative")
    return round(litres * price_per_litre, 2)


def prompt_port_selection():
    ports_list = list(PORT_DATABASE.keys())
    for index, port_key in enumerate(ports_list, start=1):
        print(f"[{index}] {PORT_DATABASE[port_key]['name']}")

    origin_choice = int(input("\nSelect Origin Port number: ")) - 1
    dest_choice = int(input("Select Destination Port number: ")) - 1

    if not 0 <= origin_choice < len(ports_list) or not 0 <= dest_choice < len(ports_list):
        raise IndexError("Port selection out of range")

    return PORT_DATABASE[ports_list[origin_choice]], PORT_DATABASE[ports_list[dest_choice]]


def prompt_manual_coordinates():
    origin_lat = validate_coordinate("lat", float(input("Enter origin latitude: ")))
    origin_lon = validate_coordinate("lon", float(input("Enter origin longitude: ")))
    dest_lat = validate_coordinate("lat", float(input("Enter destination latitude: ")))
    dest_lon = validate_coordinate("lon", float(input("Enter destination longitude: ")))
    destination_tz = input("Enter destination timezone (e.g. UTC or Africa/Nairobi): ").strip() or "UTC"

    return {
        "name": "Manual origin",
        "lat": origin_lat,
        "lon": origin_lon,
        "tz": "UTC",
    }, {
        "name": "Manual destination",
        "lat": dest_lat,
        "lon": dest_lon,
        "tz": destination_tz,
    }


def print_route_summary(origin_port, dest_port, distance, course, speed, hours, eta, fuel_estimate):
    days_v = int(hours // 24)
    hours_v = int(hours % 24)
    minutes_v = int((hours * 60) % 60)

    print("\n" + "═" * 45)
    print("         OPERATIONAL ROUTE BRIEF         ")
    print("═" * 45)
    print(f" ROUTE        : {origin_port['name']} -> {dest_port['name']}")
    print(f" TOTAL DIST.  : {distance} Nautical Miles")
    print(f" TRUE COURSE  : {course}° True")
    print(f" STEER SPEED  : {speed} knots")
    print(f" TRANSIT TIME : {days_v}d {hours_v}h {minutes_v}m")
    print(f" EST. ETA     : {eta.strftime('%Y-%m-%d %H:%M')} ({eta.tzname()})")
    print(f" EST. FUEL    : {fuel_estimate} litres")
    fuel_cost = estimate_fuel_cost(fuel_estimate)
    print(f" FUEL COST    : {fuel_cost:.2f} USD")
    print("═" * 45 + "\n")


def run_cli():
    print("\n⚓ NAUTICAL DISTANCE & ETA CALCULATOR CLI ⚓")
    print("===========================================")
    print("[1] Use built-in port database")
    print("[2] Enter coordinates manually")

    try:
        mode = input("\nChoose input mode: ").strip()
        speed = validate_speed(float(input("Enter target cruising speed (knots): ")))

        if mode == "1":
            origin_port, dest_port = prompt_port_selection()
        elif mode == "2":
            origin_port, dest_port = prompt_manual_coordinates()
        else:
            raise ValueError("Please choose 1 or 2")

        distance, course = calculate_distance_and_course(
            origin_port["lat"], origin_port["lon"], dest_port["lat"], dest_port["lon"]
        )
        hours, eta = calculate_eta(distance, speed, dest_port["tz"])
        fuel_estimate = estimate_fuel(distance, speed)
        print_route_summary(origin_port, dest_port, distance, course, speed, hours, eta, fuel_estimate)

    except (ValueError, IndexError, KeyError) as exc:
        print(f"\n❌ Error: {exc}")
        print("Please restart and enter valid values.")


if __name__ == "__main__":
    run_cli()