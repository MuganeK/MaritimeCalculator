import random
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import pydeck as pdk
import streamlit as st

from nautical_calc import (
    calculate_distance_and_course,
    calculate_eta,
    estimate_fuel,
    estimate_fuel_cost,
)

PORT_DATABASE = {
    "Mombasa": {"lat": -4.0435, "lon": 39.6682, "tz": "Africa/Nairobi", "country": "Kenya"},
    "Dar es Salaam": {"lat": -6.8200, "lon": 39.2796, "tz": "Africa/Nairobi", "country": "Tanzania"},
    "Zanzibar": {"lat": -6.1612, "lon": 39.1864, "tz": "Africa/Nairobi", "country": "Tanzania"},
    "Port Victoria": {"lat": -4.6222, "lon": 55.4514, "tz": "Indian/Mahe", "country": "Seychelles"},
    "Diego Suarez": {"lat": -12.2725, "lon": 49.2892, "tz": "Indian/Antananarivo", "country": "Madagascar"},
    "Toamasina": {"lat": -18.1492, "lon": 49.4023, "tz": "Indian/Antananarivo", "country": "Madagascar"},
    "Mogadishu": {"lat": 2.0469, "lon": 45.3182, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Kismayo": {"lat": -0.3582, "lon": 42.5454, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Bosaso": {"lat": 11.2842, "lon": 49.1816, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Berbera": {"lat": 10.4396, "lon": 45.0143, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Marka (Merca)": {"lat": 1.7159, "lon": 44.7717, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Eyl": {"lat": 7.9803, "lon": 49.8164, "tz": "Africa/Mogadishu", "country": "Somalia"},
    "Lamu": {"lat": -2.2717, "lon": 40.9020, "tz": "Africa/Nairobi", "country": "Kenya"},
    "Malindi": {"lat": -3.2192, "lon": 40.1169, "tz": "Africa/Nairobi", "country": "Kenya"},
    "Tanga": {"lat": -5.0689, "lon": 39.0982, "tz": "Africa/Nairobi", "country": "Tanzania"},
    "Pemba Island": {"lat": -5.2459, "lon": 39.7689, "tz": "Africa/Nairobi", "country": "Tanzania"},
    "Moroni": {"lat": -11.7172, "lon": 43.2473, "tz": "Indian/Comoro", "country": "Comoros"},
    "Shimoni": {"lat": -4.6476, "lon": 39.3817, "tz": "Africa/Nairobi", "country": "Kenya"},
    "Port Louis": {"lat": -20.1609, "lon": 57.5012, "tz": "Indian/Mauritius", "country": "Mauritius"},
}

DEFAULT_STUDENTS = [
    {"MIDN": "Alex Smith", "Watch Status": "Off-Duty", "Helm Tasks": "Complete", "Nav Tasks": "Pending"},
    {"MIDN": "Jordan Taylor", "Watch Status": "Off-Duty", "Helm Tasks": "Pending", "Nav Tasks": "Complete"},
    {"MIDN": "Morgan Brown", "Watch Status": "Off-Duty", "Helm Tasks": "Pending", "Nav Tasks": "Pending"},
    {"MIDN": "Casey Wilson", "Watch Status": "Off-Duty", "Helm Tasks": "Complete", "Nav Tasks": "Complete"},
    {"MIDN": "Jamie Davis", "Watch Status": "Off-Duty", "Helm Tasks": "Pending", "Nav Tasks": "Pending"},
]
WATCH_STATIONS = [
    "Bridge Watch Officer (Instructor)",
    "Helmsman (Student)",
    "Lee Helm (Student)",
    "Lookout Port (Student)",
]
MARITIME_TIME_ZONES = {
    "Zulu (UTC+0)": 0,
    "Alpha (UTC+1)": 1,
    "Bravo (UTC+2)": 2,
    "Charlie (UTC+3)": 3,
    "Delta (UTC+4)": 4,
    "Echo (UTC+5)": 5,
    "Foxtrot (UTC+6)": 6,
    "Golf (UTC+7)": 7,
    "Hotel (UTC+8)": 8,
    "India (UTC+9)": 9,
    "Kilo (UTC+10)": 10,
    "Lima (UTC+11)": 11,
    "Mike (UTC+12)": 12,
    "November (UTC-1)": -1,
    "Oscar (UTC-2)": -2,
    "Papa (UTC-3)": -3,
    "Quebec (UTC-4)": -4,
    "Romeo (UTC-5)": -5,
    "Sierra (UTC-6)": -6,
    "Tango (UTC-7)": -7,
    "Uniform (UTC-8)": -8,
    "Victor (UTC-9)": -9,
    "Whiskey (UTC-10)": -10,
    "X-ray (UTC-11)": -11,
    "Yankee (UTC-12)": -12,
}


def get_maritime_timezone(zone_name):
    return timezone(timedelta(hours=MARITIME_TIME_ZONES[zone_name]))


def build_route_metrics(
    origin,
    dest,
    speed,
    fuel_price_per_litre=218.0,
    consumption_lph=1750.0,
    reserve_percent=10.0,
    departure_time=None,
):
    distance_nm, course = calculate_distance_and_course(
        origin["lat"], origin["lon"], dest["lat"], dest["lon"]
    )
    duration_hours, eta_time = calculate_eta(distance_nm, speed, dest["tz"], departure_time)
    base_fuel_litres = estimate_fuel(distance_nm, speed, consumption_lph)
    reserve_litres = round(base_fuel_litres * reserve_percent / 100, 2)
    total_fuel_litres = round(base_fuel_litres + reserve_litres, 2)

    days_v = int(duration_hours // 24)
    hours_v = int(duration_hours % 24)
    minutes_v = int((duration_hours * 60) % 60)

    return {
        "distance_nm": distance_nm,
        "course": course,
        "duration_hours": duration_hours,
        "eta": eta_time,
        "transit_duration": f"{days_v}d {hours_v}h {minutes_v}m",
        "base_fuel_litres": base_fuel_litres,
        "reserve_litres": reserve_litres,
        "fuel_litres": total_fuel_litres,
        "fuel_cost_kes": estimate_fuel_cost(total_fuel_litres, fuel_price_per_litre),
        "fuel_cost_usd": estimate_fuel_cost(total_fuel_litres, fuel_price_per_litre),
    }


def build_navigation_leg_metrics(
    origin,
    destination,
    waypoints,
    speed,
    fuel_price_per_litre,
    consumption_lph,
    reserve_percent,
    departure_time,
):
    points = [origin, *waypoints, destination]
    segment_metrics = []
    segment_departure = departure_time
    for segment_origin, segment_destination in zip(points, points[1:]):
        segment = build_route_metrics(
            segment_origin,
            {**segment_destination, "tz": destination["tz"]},
            speed,
            fuel_price_per_litre,
            consumption_lph,
            reserve_percent,
            segment_departure,
        )
        segment_metrics.append(segment)
        segment_departure = segment["eta"]

    duration_hours = sum(segment["duration_hours"] for segment in segment_metrics)
    distance_nm = round(sum(segment["distance_nm"] for segment in segment_metrics), 2)
    base_fuel = round(sum(segment["base_fuel_litres"] for segment in segment_metrics), 2)
    reserve_fuel = round(sum(segment["reserve_litres"] for segment in segment_metrics), 2)
    total_fuel = round(base_fuel + reserve_fuel, 2)
    days_v = int(duration_hours // 24)
    hours_v = int(duration_hours % 24)
    minutes_v = int((duration_hours * 60) % 60)

    return {
        "distance_nm": distance_nm,
        "course": segment_metrics[0]["course"],
        "duration_hours": duration_hours,
        "eta": segment_metrics[-1]["eta"],
        "transit_duration": f"{days_v}d {hours_v}h {minutes_v}m",
        "base_fuel_litres": base_fuel,
        "reserve_litres": reserve_fuel,
        "fuel_litres": total_fuel,
        "fuel_cost_kes": estimate_fuel_cost(total_fuel, fuel_price_per_litre),
        "fuel_cost_usd": estimate_fuel_cost(total_fuel, fuel_price_per_litre),
        "waypoints": waypoints,
    }


def build_voyage_metrics(
    ports,
    speed,
    fuel_price_per_litre=218.0,
    consumption_lph=1750.0,
    reserve_percent=10.0,
    departure_time=None,
    layover_days=None,
    departure_times=None,
    waypoints_by_leg=None,
):
    if len(ports) < 2:
        raise ValueError("A voyage requires an origin and destination port")

    legs = []
    current_departure = departure_time
    layover_days = layover_days or [0] * max(len(ports) - 2, 0)
    if len(layover_days) != len(ports) - 2:
        raise ValueError("Provide one stay duration for each stopover")
    departure_times = departure_times or [None] * max(len(ports) - 2, 0)
    if len(departure_times) != len(ports) - 2:
        raise ValueError("Provide one departure time for each stopover")
    waypoints_by_leg = waypoints_by_leg or [[] for _ in range(len(ports) - 1)]
    if len(waypoints_by_leg) != len(ports) - 1:
        raise ValueError("Provide navigation waypoints for each voyage leg")

    for leg_number, (origin, destination) in enumerate(zip(ports, ports[1:]), start=1):
        if leg_number > 1 and departure_times[leg_number - 2] is not None:
            current_departure = departure_times[leg_number - 2]
        leg = build_navigation_leg_metrics(
            origin,
            destination,
            waypoints_by_leg[leg_number - 1],
            speed,
            fuel_price_per_litre,
            consumption_lph,
            reserve_percent,
            current_departure,
        )
        leg["leg_number"] = leg_number
        leg["origin"] = origin.get("name", "Origin")
        leg["destination"] = destination.get("name", "Destination")
        leg["stay_days"] = layover_days[leg_number - 1] if leg_number <= len(layover_days) else 0
        legs.append(leg)
        if leg_number <= len(layover_days):
            current_departure = leg["eta"] + timedelta(days=leg["stay_days"])

    total_duration = sum(leg["duration_hours"] for leg in legs) + sum(layover_days) * 24
    total_distance = round(sum(leg["distance_nm"] for leg in legs), 2)
    total_base_fuel = round(sum(leg["base_fuel_litres"] for leg in legs), 2)
    total_reserve = round(sum(leg["reserve_litres"] for leg in legs), 2)
    total_fuel = round(total_base_fuel + total_reserve, 2)
    first_leg_course = legs[0]["course"] if len(legs) == 1 else None

    days_v = int(total_duration // 24)
    hours_v = int(total_duration % 24)
    minutes_v = int((total_duration * 60) % 60)

    return {
        "distance_nm": total_distance,
        "course": first_leg_course,
        "duration_hours": total_duration,
        "eta": legs[-1]["eta"],
        "transit_duration": f"{days_v}d {hours_v}h {minutes_v}m",
        "base_fuel_litres": total_base_fuel,
        "reserve_litres": total_reserve,
        "fuel_litres": total_fuel,
        "fuel_cost_kes": estimate_fuel_cost(total_fuel, fuel_price_per_litre),
        "fuel_cost_usd": estimate_fuel_cost(total_fuel, fuel_price_per_litre),
        "legs": legs,
    }


def generate_watchbill(students, station_names=WATCH_STATIONS, randomizer=None):
    assigned_students = [student["MIDN"] for student in students if student["Watch Status"] == "Off-Duty"]
    (randomizer or random).shuffle(assigned_students)
    return [
        {
            "Watch Station": station,
            "Assigned Personnel": assigned_students[index] if index < len(assigned_students) else "Unassigned",
        }
        for index, station in enumerate(station_names)
    ]


def build_track_points(origin, destination, segments=24):
    return [
        {
            "lon": origin["lon"] + (destination["lon"] - origin["lon"]) * index / segments,
            "lat": origin["lat"] + (destination["lat"] - origin["lat"]) * index / segments,
        }
        for index in range(segments + 1)
    ]


def build_voyage_track_points(ports, segments_per_leg=24, waypoints_by_leg=None):
    track = []
    waypoints_by_leg = waypoints_by_leg or [[] for _ in range(len(ports) - 1)]
    for leg_index, (origin, destination) in enumerate(zip(ports, ports[1:])):
        leg_points = [origin, *waypoints_by_leg[leg_index], destination]
        leg_track = []
        for segment_origin, segment_destination in zip(leg_points, leg_points[1:]):
            segment_track = build_track_points(segment_origin, segment_destination, segments_per_leg)
            leg_track.extend(segment_track if not leg_track else segment_track[1:])
        track.extend(leg_track if not track else leg_track[1:])
    return track


def render_route_planner():
    st.subheader("Route, Fuel & Cost Planner")
    input_col1, input_col2, input_col3 = st.columns(3)
    with input_col1:
        origin_name = st.selectbox("Origin Port", list(PORT_DATABASE.keys()), index=0)
    with input_col2:
        stopover_count = st.number_input(
            "Number of Stopovers",
            min_value=0,
            max_value=5,
            value=1,
            step=1,
            help="Add ports of call between the origin and final destination.",
        )
    with input_col3:
        speed = st.number_input("Cruising Speed (knots)", min_value=0.1, max_value=60.0, value=14.0, step=0.5)

    selected_stopovers = []
    stopover_stay_days = []
    available_stopovers = [name for name in PORT_DATABASE if name != origin_name]
    if stopover_count:
        st.markdown("#### Route Sequence")
        stopover_columns = st.columns(min(int(stopover_count), 3))
        for index in range(int(stopover_count)):
            options = [name for name in available_stopovers if name not in selected_stopovers]
            with stopover_columns[index % len(stopover_columns)]:
                stopover_name = st.selectbox(
                    f"Port of Call {index + 1}",
                    options,
                    key=f"stopover_{index}",
                )
            selected_stopovers.append(stopover_name)

        stay_columns = st.columns(min(int(stopover_count), 3))
        for index, stopover_name in enumerate(selected_stopovers):
            with stay_columns[index % len(stay_columns)]:
                stay_days = st.number_input(
                    f"Stay at {stopover_name} (days)",
                    min_value=0,
                    max_value=365,
                    value=0,
                    step=1,
                    key=f"stay_days_{index}",
                )
            stopover_stay_days.append(int(stay_days))

    destination_options = list(PORT_DATABASE)
    dest_name = st.selectbox(
        "Final Destination Port",
        destination_options,
        help="Any port may be selected, including the origin for a return voyage.",
    )

    settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)
    with settings_col1:
        consumption_lph = st.number_input("Consumption (L/hour)", min_value=0.1, value=1750.0, step=50.0)
    with settings_col2:
        fuel_price = st.number_input("Fuel Price (KES/L)", min_value=0.0, value=218.0, step=1.0)
    with settings_col3:
        reserve_percent = st.number_input("Fuel Reserve (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
    with settings_col4:
        departure_date = st.date_input("Departure Date", value=datetime.now().date())
        departure_clock = st.time_input("Departure Time", value=time(8, 0))
        departure_zone = st.selectbox(
            "ETD Time Zone",
            list(MARITIME_TIME_ZONES),
            index=0,
            help="Maritime time zones use NATO names such as Bravo (UTC+2) and Charlie (UTC+3).",
        )

    departure_time = datetime.combine(
        departure_date,
        departure_clock,
        tzinfo=get_maritime_timezone(departure_zone),
    )
    route_names = [origin_name, *selected_stopovers, dest_name]
    route_ports = [{**PORT_DATABASE[name], "name": name} for name in route_names]

    waypoints_by_leg = [[] for _ in range(len(route_ports) - 1)]
    waypoint_count = st.number_input(
        "Navigation Waypoints on Final Leg",
        min_value=0,
        max_value=4,
        value=0,
        step=1,
        help="Add course-change points to route around hazards or land. Verify every point against official nautical charts.",
    )
    if waypoint_count:
        st.warning("Manual waypoints change the planned course. This is not a certified collision-avoidance or navigational-chart system.")
        waypoint_columns = st.columns(min(int(waypoint_count), 2))
        final_leg_waypoints = []
        for index in range(int(waypoint_count)):
            with waypoint_columns[index % len(waypoint_columns)]:
                waypoint_lat = st.number_input(
                    f"Waypoint {index + 1} latitude",
                    min_value=-90.0,
                    max_value=90.0,
                    value=float(route_ports[-2]["lat"]),
                    step=0.1,
                    key=f"waypoint_lat_{index}",
                )
                waypoint_lon = st.number_input(
                    f"Waypoint {index + 1} longitude",
                    min_value=-180.0,
                    max_value=180.0,
                    value=float(route_ports[-2]["lon"]),
                    step=0.1,
                    key=f"waypoint_lon_{index}",
                )
            final_leg_waypoints.append(
                {
                    "name": f"Navigation waypoint {index + 1}",
                    "lat": waypoint_lat,
                    "lon": waypoint_lon,
                    "tz": route_ports[-1]["tz"],
                }
            )
        waypoints_by_leg[-1] = final_leg_waypoints

    independent_departures = []
    if selected_stopovers:
        st.markdown("#### Independent Stopover Departures")
        st.caption("Enter each departure in the local time zone of that port, or use the stay-days setting above.")
        departure_columns = st.columns(min(len(selected_stopovers), 3))
        for index, stopover_name in enumerate(selected_stopovers):
            with departure_columns[index % len(departure_columns)]:
                use_independent_departure = st.checkbox(
                    f"Set departure from {stopover_name}",
                    key=f"independent_departure_{index}",
                )
                if use_independent_departure:
                    stopover_date = st.date_input(
                        f"Departure date from {stopover_name}",
                        value=departure_date,
                        key=f"departure_date_{index}",
                    )
                    stopover_clock = st.time_input(
                        f"Departure time from {stopover_name}",
                        value=time(8, 0),
                        key=f"departure_time_{index}",
                    )
                    stopover_zone_options = [
                        f"Port local ({PORT_DATABASE[stopover_name]['tz']})",
                        *MARITIME_TIME_ZONES,
                    ]
                    stopover_zone = st.selectbox(
                        f"Time zone from {stopover_name}",
                        stopover_zone_options,
                        key=f"departure_zone_{index}",
                    )
                    selected_timezone = (
                        ZoneInfo(PORT_DATABASE[stopover_name]["tz"])
                        if stopover_zone.startswith("Port local")
                        else get_maritime_timezone(stopover_zone)
                    )
                    independent_departures.append(
                        datetime.combine(
                            stopover_date,
                            stopover_clock,
                            tzinfo=selected_timezone,
                        )
                    )
                else:
                    independent_departures.append(None)

    schedule_mode = st.radio(
        "ETA Planning",
        ["Calculate ETA from speed", "Plan by target ETA"],
        horizontal=True,
    )
    planned_eta = None
    if schedule_mode == "Plan by target ETA":
        eta_mode = st.radio(
            "Target ETA input",
            ["Specific date and time", "Whole voyage days"],
            horizontal=True,
        )
        if eta_mode == "Specific date and time":
            eta_date = st.date_input(
                "Target ETA Date (destination local time)",
                value=departure_date + timedelta(days=1),
            )
            eta_clock = st.time_input("Target ETA Time (destination local time)", value=time(8, 0))
            planned_eta = datetime.combine(
                eta_date,
                eta_clock,
                tzinfo=ZoneInfo(route_ports[-1]["tz"]),
            )
        else:
            whole_days = st.number_input(
                "Whole Voyage Days",
                min_value=1,
                max_value=365,
                value=1,
                step=1,
            )
            planned_eta = departure_time + timedelta(days=int(whole_days))

        if planned_eta <= departure_time.astimezone(planned_eta.tzinfo):
            st.error("Target ETA must be after the ETD.")
            return

        planned_duration_hours = (planned_eta - departure_time.astimezone(planned_eta.tzinfo)).total_seconds() / 3600
        planned_distance = sum(
            calculate_distance_and_course(
                segment_origin["lat"],
                segment_origin["lon"],
                segment_destination["lat"],
                segment_destination["lon"],
            )[0]
            for leg_index, (origin_port, destination_port) in enumerate(zip(route_ports, route_ports[1:]))
            for segment_origin, segment_destination in zip(
                [origin_port, *waypoints_by_leg[leg_index], destination_port],
                [*waypoints_by_leg[leg_index], destination_port],
            )
        )
        speed = round(planned_distance / planned_duration_hours, 2)
        st.info(f"Required average speed for this schedule: {speed:.2f} knots")

    metrics = build_voyage_metrics(
        route_ports,
        speed,
        fuel_price,
        consumption_lph,
        reserve_percent,
        departure_time,
        stopover_stay_days,
        independent_departures,
        waypoints_by_leg,
    )

    metric_row_one = st.columns(3)
    metric_row_one[0].metric("Distance", f"{metrics['distance_nm']} NM")
    course_value = f"{metrics['course']}° True" if metrics["course"] is not None else "Multi-leg"
    metric_row_one[1].metric("Course", course_value)
    metric_row_one[2].metric("Transit", metrics["transit_duration"])

    metric_row_two = st.columns(3)
    metric_row_two[0].metric(
        "ETA",
        metrics["eta"].strftime("%b %d, %H:%M"),
        f"Zone: {metrics['eta'].tzname()}",
    )
    metric_row_two[1].metric("Fuel incl. reserve", f"{metrics['fuel_litres']:,.0f} L")
    metric_row_two[2].metric("Fuel cost", f"${metrics['fuel_cost_usd']:,.2f}")

    st.subheader("Voyage Legs")
    leg_summary = pd.DataFrame([
        {
            "Leg": f"Leg {leg['leg_number']}",
            "Route": f"{leg['origin']} -> {leg['destination']}",
            "Distance": f"{leg['distance_nm']:,.2f} NM",
            "Course": f"{leg['course']}° True",
            "Transit": leg["transit_duration"],
            "Stay before next leg": f"{leg['stay_days']} days" if leg["stay_days"] else "-",
            "Arrival": leg["eta"].strftime("%b %d, %H:%M %Z"),
        }
        for leg in metrics["legs"]
    ])
    st.dataframe(leg_summary, use_container_width=True, hide_index=True)

    st.subheader("Fuel and Cost Totals")
    fuel_summary = pd.DataFrame([
        {"Item": "Base voyage fuel", "Amount": f"{metrics['base_fuel_litres']:,.2f} L"},
        {"Item": f"Fuel reserve ({reserve_percent:.0f}%)", "Amount": f"{metrics['reserve_litres']:,.2f} L"},
        {"Item": "Total fuel required", "Amount": f"{metrics['fuel_litres']:,.2f} L"},
        {"Item": "Fuel price", "Amount": f"${fuel_price:,.2f} / L"},
        {"Item": "Total estimated fuel cost", "Amount": f"${metrics['fuel_cost_usd']:,.2f}"},
    ])
    st.table(fuel_summary)

    st.subheader("Visualized Transit Track")
    map_style_name = st.selectbox(
        "Map background",
        ["Nautical light", "Nautical dark", "Voyager"],
        help="Use a high-contrast basemap to make the route and port markers easier to read.",
    )
    map_styles = {
        "Nautical light": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        "Nautical dark": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
    }
    track_points = build_voyage_track_points(route_ports, waypoints_by_leg=waypoints_by_leg)
    port_points = [
        {"position": [port["lon"], port["lat"]], "name": name}
        for name, port in zip(route_names, route_ports)
    ]
    waypoint_points = [
        {"position": [waypoint["lon"], waypoint["lat"]], "name": waypoint["name"]}
        for leg_waypoints in waypoints_by_leg
        for waypoint in leg_waypoints
    ]
    route_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": [[point["lon"], point["lat"]] for point in track_points]}],
        get_path="path",
        get_color=[0, 121, 255],
        width_min_pixels=6,
    )
    port_layer = pdk.Layer(
        "ScatterplotLayer",
        data=port_points,
        get_position="position",
        get_fill_color=[220, 50, 47],
        get_radius=4500,
        radius_min_pixels=5,
        radius_max_pixels=9,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        pickable=True,
    )
    waypoint_layer = pdk.Layer(
        "ScatterplotLayer",
        data=waypoint_points,
        get_position="position",
        get_fill_color=[255, 165, 0],
        get_radius=4500,
        radius_min_pixels=6,
        radius_max_pixels=10,
        stroked=True,
        get_line_color=[50, 35, 0],
        line_width_min_pixels=2,
        pickable=True,
    )
    label_layer = pdk.Layer(
        "TextLayer",
        data=port_points,
        get_position="position",
        get_text="name",
        get_size=16,
        get_color=[20, 35, 55],
        get_text_anchor="middle",
        get_alignment_baseline="bottom",
        get_pixel_offset=[0, -18],
        pickable=False,
    )
    waypoint_label_layer = pdk.Layer(
        "TextLayer",
        data=waypoint_points,
        get_position="position",
        get_text="name",
        get_size=14,
        get_color=[180, 95, 0],
        get_text_anchor="middle",
        get_alignment_baseline="bottom",
        get_pixel_offset=[0, -20],
        pickable=False,
    )
    latitude_span = max(port["lat"] for port in route_ports) - min(port["lat"] for port in route_ports)
    longitude_span = max(port["lon"] for port in route_ports) - min(port["lon"] for port in route_ports)
    route_span = max(latitude_span, longitude_span, 1)
    map_zoom = max(2, min(7, 5 - route_span / 35))
    view_state = pdk.ViewState(
        latitude=sum(port["lat"] for port in route_ports) / len(route_ports),
        longitude=sum(port["lon"] for port in route_ports) / len(route_ports),
        zoom=map_zoom,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[route_layer, port_layer, waypoint_layer, label_layer, waypoint_label_layer],
            initial_view_state=view_state,
            map_style=map_styles[map_style_name],
            tooltip={"text": "{name}"},
        ),
        use_container_width=True,
    )


def render_watchbill():
    st.subheader("Training Roster & Watchbill")
    if "students" not in st.session_state:
        st.session_state.students = [student.copy() for student in DEFAULT_STUDENTS]
    if "watchbill" not in st.session_state:
        st.session_state.watchbill = []

    st.dataframe(pd.DataFrame(st.session_state.students), use_container_width=True, hide_index=True)
    student_names = [student["MIDN"] for student in st.session_state.students]
    with st.form("qualification_update"):
        target_student = st.selectbox("Student", student_names)
        target_task = st.selectbox("Task", ["Helm Tasks", "Nav Tasks"])
        target_status = st.selectbox("Status", ["Pending", "Complete"])
        submitted = st.form_submit_button("Update Qualification")
    if submitted:
        for student in st.session_state.students:
            if student["MIDN"] == target_student:
                student[target_task] = target_status
        st.rerun()

    if st.button("Generate 4-Hour Watchbill"):
        st.session_state.watchbill = generate_watchbill(st.session_state.students)
    if st.session_state.watchbill:
        st.dataframe(pd.DataFrame(st.session_state.watchbill), use_container_width=True, hide_index=True)
        st.download_button(
            "Download Watchbill CSV",
            pd.DataFrame(st.session_state.watchbill).to_csv(index=False),
            "watchbill.csv",
            "text/csv",
        )


def main():
    st.set_page_config(page_title="Maritime Cruise Planner", page_icon="⚓", layout="wide")
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] {
            font-size: clamp(0.95rem, 1.8vw, 1.55rem);
            line-height: 1.2;
            white-space: nowrap;
            overflow: visible;
        }
        [data-testid="stMetricLabel"] {
            font-size: clamp(0.72rem, 1.2vw, 0.95rem);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("⚓ Maritime Cruise Planner")
    page = st.sidebar.radio("Planner section", ["Route Planner", "Training Watchbill"])
    if page == "Route Planner":
        render_route_planner()
    else:
        render_watchbill()


if __name__ == "__main__":
    main()
