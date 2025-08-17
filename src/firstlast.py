from collections import namedtuple
from typing import List, Tuple, Optional, Dict
import os
import csv

STOPS_FILE_NAME = "stops.txt"
STOP_TIMES_FILE_NAME = "stop_times.txt"
TRIPS_FILE_NAME = "trips.txt"

HEADSIGN_MAP = {
    # Red Line
    "SF / SFO Airport / Millbrae": "Red SB (Millbrae)",
    "SF / SFO Airport / Millbrae": "Red SB (Millbrae)",
    "SF / SFO Airport / Millbrae": "Red SB (Millbrae)",
    "SFO Airport / Millbrae": "Red SB (Millbrae)",
    "SFO / SF / Richmond": "Red NB (Richmond)",

    # Orange Line
    "Berryessa": "Orange SB (Berryessa)",
    # Appears to not be in stop_times.txt but is listed in trips.txt
    "Berryessa/North San Jose": "Orange SB (Berryessa)",
    "OAK Airport / Berryessa/North San Jose": "Orange SB (Berryessa)",
    "OAK Airport / Richmond": "Orange NB (Richmond)",

    # Yellow Line
    "Antioch": "Yellow NB (Antioch)",
    "SFO / SF / Antioch": "Yellow NB (Antioch)",
    "San Francisco / Antioch": "Yellow NB (Antioch)",
    "Pittsburg / Bay Point": "Yellow NB (Pts/BayPt)",
    "SFO / SF / Pittsburg/Bay Point": "Yellow NB (Pts/BayPt)",
    "SF / Pittsburg/Bay Point": "Yellow NB (Pts/BayPt)",
    "San Francisco International Airport": "Yellow SB (SFO)",
    "Millbrae (Caltrain Transfer Platform)": "Yellow SB (Millbrae, No SFO)",
    "San Francisco Int'l Airport/Millbrae": "Yellow SB (Millbrae)",

    # Blue Line
    "Dublin/Pleasanton": "Blue EB (Dublin/Plsntn)",
    "SF / OAK Airport / Dublin/Pleasanton": "Blue EB (Dublin/Plsntn)",
    "OAK Airport / SF / Daly City": "Blue WB (Daly City)",
    # Appears to not be in stop_times.txt but is listed in trips.txt
    "Bay Fair": "Blue WB (Bay Fair only)",

    # Green Line
    "SF / OAK Airport / Berryessa": "Green EB (Berryessa)",

    # Grey Line
    "Coliseum": "Grey OB (Coliseum)",
    "Oakland Airport": "Grey IB (OAK)",

    # Mixed trips not in trips.txt but present in stop_times.txt
    "SF / Daly City": "Blue/Green WB (Daly City)",
    "Richmond": "Red/Orange NB (Richmond)",

    # Other headsigns only in stop_times.txt
    "OAK Airport / Dublin/Pleasanton": "Blue EB (Dublin/Plsntn)",
    "San Francisco / BayPoint": "Yellow NB (Pts/BayPt)",
    "San Francisco / Pittsburg/Bay Point": "Yellow NB (Pts/BayPt)",
    "San Francisco / Richmond": "Red NB (Richmond)",
    "OAK Airport / Berryessa": "Green EB (Berryessa)",
}

def get_station_ids(station_name: str) -> List[str]:
    """
    Returns the stop IDs for the given station name.
    """
    stop_ids = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOPS_FILE_NAME}", "r")  as f:
        reader = csv.reader(f)
        next(reader) # Skip header row
        for row in reader:
            stop_id = row[0]
            stop_name = row[2]
            if station_name in stop_name:
                stop_ids.append(stop_id)
    return stop_ids

TripInfo = namedtuple("TripInfo", ["service_id", "trip_id", "trip_headsign"])


def trips_dict() -> Dict[str, TripInfo]:
    with open(f"{os.environ['BART_DATA_ROOT']}/{TRIPS_FILE_NAME}", "r") as f:
        reader = csv.reader(f)
        next(reader) # Skip header row
        trips = {}
        for row in reader:
            trip_id = row[2]
            service_id = row[1]
            trip_headsign = row[3]
            trips[trip_id] = TripInfo(
                service_id=service_id,
                trip_id=trip_id,
                trip_headsign=trip_headsign,
            )
        return trips

StopTimeInfo = namedtuple(
    "TripForStopInfo", ["departure_time", "stop_headsign", "service_id"])


def get_stop_times(
        station_ids: Optional[List[str]],
        trips_dict: Optional[Dict[str, TripInfo]] = None) -> List[StopTimeInfo]:
    trips = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOP_TIMES_FILE_NAME}", "r")  as f:
        reader = csv.reader(f)
        next(reader) # Skip header row
        for row in reader:
            # trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_distance_traveled
            stop_id = row[3]
            if station_ids is None or stop_id in station_ids:
                trip_id = row[0]
                departure_time = row[2]
                stop_headsign = row[5]
                if trips_dict and not stop_headsign:
                    stop_headsign = trips_dict[trip_id].trip_headsign

                if trips_dict:
                    service_id = trips_dict[trip_id].service_id
                else:
                    service_id = None

                trips.append(StopTimeInfo(departure_time, stop_headsign, service_id))

    return trips

FirstLastKey = namedtuple("FirstLastKey", ["service_id", "stop_headsign"])

FirstLastTimes = namedtuple("FirstLastTimes", ["first", "last"])


def first_last_times(trips: List[StopTimeInfo]) -> Dict[FirstLastKey, FirstLastTimes]:
    first_map = {}
    last_map = {}
    for stop_time_info in trips:
        key = FirstLastKey(stop_time_info.service_id, stop_time_info.stop_headsign)
        time = stop_time_info.departure_time
        if time < first_map.get(key, "99:99:99"):
            first_map[key] = time
        if time > last_map.get(key, "00:00:00"):
            last_map[key] = time

    return {key: FirstLastTimes(first_map[key], last_map[key]) for key in first_map}

def key_replacement(key: FirstLastKey) -> str:
    service_id, headsign = key.service_id, key.stop_headsign
    service_map = {
        # Mainline
        "2025_08_11-SA-MVS-Saturday-000": "Saturday",
        "2025_08_11-SU-MVS-Sunday-000": "Sunday",
        "2025_08_11-DX-MVS-Weekday-003": "Weekday",

        # OAK Shuttle
        # Yes, it really is 6 separate services for the same route.
        "2025_08_11-DX19-Weekday-001": "Weekday",
        "2025_08_11-DX20-Weekday-001": "Weekday",
        "2025_08_11-SA19-Saturday-001": "Saturday",
        "2025_08_11-SA20-Saturday-001": "Saturday",
        "2025_08_11-SU19-Sunday-001": "Sunday",
        "2025_08_11-SU20-Sunday-001": "Sunday",
    }

    service_id = service_map.get(service_id, service_id)
    # If headsign is not in the map, center it with asterisks so it stands out.
    if headsign not in HEADSIGN_MAP.keys():
        headsign = headsign.center(50, '*')
    headsign = HEADSIGN_MAP.get(headsign, headsign)
    headsign = replaced_headsign_destination_only(headsign)

    return f"{service_id} - {headsign}"

def replaced_headsign_destination_only(replaced_headsign: str) -> str:
    # Yellow NB (Pts/BayPt) -> Pts/BayPt
    start = replaced_headsign.find('(')
    end = replaced_headsign.find(')')
    return replaced_headsign[start + 1:end].strip() if start != -1 and end != -1 else replaced_headsign

def print_first_last_times(trips: List[StopTimeInfo]) -> None:
    first_last = first_last_times(trips)
    display_map = {key_replacement(key): v for key, v in first_last.items()}
    max_key_length = max(len(key) for key in display_map.keys())

    for key in sorted(display_map):
        # Expect each value in replace_map to be a tuple of (first, last) times.
        print(f"{key.ljust(max_key_length)}: {display_map[key].first} - {display_map[key].last}")

def print_first_last_times_table(trips: List[StopTimeInfo]) -> None:
    first_last = first_last_times(trips)
    display_map = {key_replacement(key): v for key, v in first_last.items()}
    destinations = set(map(lambda key: key.split(' - ')[1], display_map.keys()))
    services = set(map(lambda key: key.split(' - ')[0], display_map.keys()))

    print_first_or_last((
        "First Trains", lambda x: x.first, "opened before", min), display_map, destinations, services)
    print()
    print_first_or_last((
        "Last Trains", lambda x: x.last, "closed after", max), display_map, destinations, services)

def print_first_or_last(
        print_specs: Tuple[str, callable],
        display_map: Dict[str, FirstLastTimes] ,
        destinations: List[str],
        services:  List[str]) -> None:
    first_col_len = max(len(dest) for dest in destinations)
    time_len = 8  # Length of time strings (HH:MM:SS)
    header_str = "| " + "Destinations".ljust(first_col_len) + " | "
    service_order = ["Weekday", "Saturday", "Sunday"]
    sorted_services = sorted(services, key=service_order.index)
    for service in sorted_services:
        header_str += service.ljust(time_len)
        header_str += " | "

    title, extraction_func, station_action, agg_func = print_specs
    last = agg_func(map(lambda x: extraction_func(x) , display_map.values()))
    print(
        f"*** {title} *** station {station_action}: {last}"
        .center(len(header_str.strip())))

    def print_dashes():
        print("-" * (len(header_str.strip())))
    print_dashes()
    print(header_str.strip())
    print_dashes()

    destination_order = [
        "Richmond",
        "Pts/BayPt", "Antioch",
        "OAK", "Coliseum", "Bay Fair",
        "Dublin/Plsntn",
        "Berryessa/North San Jose", "Berryessa",
        "Millbrae, No SFO", "Millbrae", "SFO",
        "Daly City",
    ]
    for destination in sorted(destinations, key=destination_order.index):
        print(f"| {destination.ljust(first_col_len)} | ", end='')
        for service in sorted_services:
            # Create a key for the display_map
            key = f"{service} - {destination}"
            if key in display_map:
                print(f"{extraction_func(display_map[key]).ljust(time_len)} | ", end='')
            else:
                print(" " * time_len + " | ", end='')
        print()

    print_dashes()

def test_headsign_names() -> bool:
    """
    Tests that all headsigns in the trips.txt file have a mapping in HEADSIGN_MAP.
    """
    all_trips = trips_dict()
    unique_headsigns = set()
    unique_headsigns.update(
        (trip.trip_headsign, "TRIP") for trip in all_trips.values()
    )
    headsigns_from_stop_times = get_stop_times(None, all_trips)
    unique_headsigns.update(
        (stop_time.stop_headsign, "STOP_TIMES")
        for stop_time in headsigns_from_stop_times
    )

    success = True
    for headsign, source in unique_headsigns:
        if headsign not in HEADSIGN_MAP:
            success = False
            print(f"Missing headsign mapping for: {headsign}, source: {source}")
    return success


TEST_HEADSIGNS = True
if __name__ == "__main__":
    if TEST_HEADSIGNS:
        success = test_headsign_names()
        if not success:
            print("Some headsigns are missing mappings in HEADSIGN_MAP.")
            exit(1)
    station_name = "19th"
    print_first_last_times_table(get_stop_times(
    #print_first_last_times(get_stop_times(
        station_ids=get_station_ids(station_name),
        trips_dict=trips_dict()))
    #print(trips_dict())