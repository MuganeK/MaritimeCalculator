import pytest
import nautical_calc
import app
from datetime import datetime, timedelta, timezone


def test_validate_coordinate_rejects_out_of_range():
    with pytest.raises(ValueError):
        nautical_calc.validate_coordinate("lat", 91)

    with pytest.raises(ValueError):
        nautical_calc.validate_coordinate("lon", -181)


def test_estimate_fuel_returns_positive_value():
    assert nautical_calc.estimate_fuel(100, 10) == pytest.approx(17500.0)


def test_estimate_fuel_cost_returns_expected_value():
    assert nautical_calc.estimate_fuel_cost(1000) == pytest.approx(218000.0)


def test_build_route_metrics_includes_fuel_and_cost():
    route_metrics = app.build_route_metrics(
        {"lat": 0.0, "lon": 0.0, "tz": "UTC"},
        {"lat": 1.0, "lon": 1.0, "tz": "UTC"},
        10,
    )

    assert route_metrics["fuel_litres"] > 0
    assert route_metrics["fuel_cost_usd"] > 0


def test_build_route_metrics_applies_fuel_reserve_and_departure_time():
    departure = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    route_metrics = app.build_route_metrics(
        {"lat": 0.0, "lon": 0.0, "tz": "UTC"},
        {"lat": 1.0, "lon": 1.0, "tz": "UTC"},
        10,
        consumption_lph=100,
        reserve_percent=20,
        departure_time=departure,
    )

    assert route_metrics["fuel_litres"] == pytest.approx(route_metrics["base_fuel_litres"] * 1.2)
    assert route_metrics["eta"] > departure


def test_generate_watchbill_only_assigns_off_duty_students():
    students = [
        {"MIDN": "Available", "Watch Status": "Off-Duty"},
        {"MIDN": "Busy", "Watch Status": "On-Watch"},
    ]

    watchbill = app.generate_watchbill(students, ["Station A", "Station B"], randomizer=__import__("random"))

    assert watchbill[0]["Assigned Personnel"] == "Available"
    assert watchbill[1]["Assigned Personnel"] == "Unassigned"


def test_somali_and_secondary_ports_are_available():
    for port_name in [
        "Mogadishu",
        "Kismayo",
        "Bosaso",
        "Berbera",
        "Lamu",
        "Tanga",
        "Shimoni",
        "Port Louis",
        "Toamasina",
    ]:
        assert port_name in app.PORT_DATABASE
        assert -90 <= app.PORT_DATABASE[port_name]["lat"] <= 90
        assert -180 <= app.PORT_DATABASE[port_name]["lon"] <= 180

    assert nautical_calc.PORT_DATABASE["toamasina"]["name"] == "Port of Toamasina (Madagascar)"


def test_landlocked_ports_are_not_available():
    assert "Entebbe" not in app.PORT_DATABASE
    assert "entebbe" not in nautical_calc.PORT_DATABASE


def test_build_track_points_includes_both_ports():
    origin = {"lat": 0.0, "lon": 10.0}
    destination = {"lat": 5.0, "lon": 20.0}

    track = app.build_track_points(origin, destination, segments=4)

    assert len(track) == 5
    assert track[0] == {"lat": 0.0, "lon": 10.0}
    assert track[-1] == {"lat": 5.0, "lon": 20.0}


def test_build_voyage_metrics_aggregates_multiple_legs():
    ports = [
        {"name": "Origin", "lat": 0.0, "lon": 0.0, "tz": "UTC"},
        {"name": "Stopover", "lat": 0.0, "lon": 1.0, "tz": "UTC"},
        {"name": "Destination", "lat": 0.0, "lon": 2.0, "tz": "UTC"},
    ]
    departure = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    metrics = app.build_voyage_metrics(ports, 10, departure_time=departure)

    assert len(metrics["legs"]) == 2
    assert metrics["distance_nm"] == pytest.approx(120.08, abs=0.01)
    assert metrics["legs"][0]["eta"] < metrics["eta"]
    assert metrics["legs"][0]["destination"] == "Stopover"
    assert metrics["legs"][1]["destination"] == "Destination"


def test_build_voyage_metrics_includes_stopover_stay_in_eta():
    ports = [
        {"name": "Origin", "lat": 0.0, "lon": 0.0, "tz": "UTC"},
        {"name": "Stopover", "lat": 0.0, "lon": 1.0, "tz": "UTC"},
        {"name": "Destination", "lat": 0.0, "lon": 2.0, "tz": "UTC"},
    ]
    departure = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    without_stay = app.build_voyage_metrics(ports, 10, departure_time=departure)
    with_stay = app.build_voyage_metrics(ports, 10, departure_time=departure, layover_days=[3])

    assert with_stay["eta"] - without_stay["eta"] == timedelta(days=3)
    assert with_stay["legs"][0]["stay_days"] == 3


def test_build_voyage_metrics_supports_return_to_origin():
    ports = [
        {"name": "Mombasa", "lat": -4.0435, "lon": 39.6682, "tz": "Africa/Nairobi"},
        {"name": "Shimoni", "lat": -4.6476, "lon": 39.3817, "tz": "Africa/Nairobi"},
        {"name": "Mombasa", "lat": -4.0435, "lon": 39.6682, "tz": "Africa/Nairobi"},
    ]

    metrics = app.build_voyage_metrics(ports, 10, departure_time=datetime(2026, 1, 1, 8, tzinfo=timezone.utc))

    assert metrics["legs"][-1]["destination"] == "Mombasa"
    assert metrics["distance_nm"] > 0


def test_build_voyage_metrics_supports_independent_stopover_departure():
    ports = [
        {"name": "Origin", "lat": 0.0, "lon": 0.0, "tz": "UTC"},
        {"name": "Stopover", "lat": 0.0, "lon": 1.0, "tz": "Africa/Nairobi"},
        {"name": "Destination", "lat": 0.0, "lon": 2.0, "tz": "UTC"},
    ]
    departure = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    stopover_departure = datetime(2026, 1, 3, 8, 0, tzinfo=timezone.utc)

    metrics = app.build_voyage_metrics(
        ports,
        10,
        departure_time=departure,
        departure_times=[stopover_departure],
    )

    expected_eta = stopover_departure + timedelta(hours=metrics["legs"][1]["duration_hours"])
    assert metrics["legs"][1]["eta"] == expected_eta
    assert metrics["legs"][1]["eta"] > stopover_departure


def test_maritime_timezone_names_use_expected_offsets():
    assert app.get_maritime_timezone("Bravo (UTC+2)").utcoffset(None).total_seconds() == 2 * 3600
    assert app.get_maritime_timezone("Charlie (UTC+3)").utcoffset(None).total_seconds() == 3 * 3600
    assert app.get_maritime_timezone("Zulu (UTC+0)").utcoffset(None).total_seconds() == 0


def test_build_voyage_track_points_joins_stopovers_once():
    ports = [
        {"lat": 0.0, "lon": 0.0},
        {"lat": 0.0, "lon": 1.0},
        {"lat": 1.0, "lon": 1.0},
    ]

    track = app.build_voyage_track_points(ports, segments_per_leg=2)

    assert len(track) == 5
    assert track[0] == {"lat": 0.0, "lon": 0.0}
    assert track[2] == {"lat": 0.0, "lon": 1.0}
    assert track[-1] == {"lat": 1.0, "lon": 1.0}
