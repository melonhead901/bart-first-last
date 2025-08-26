from collections import namedtuple
from typing import List, Tuple, Optional, Dict, Set, Callable, Iterable
import os
import csv

from bartdb import BartDb

STOPS_FILE_NAME = "stops.txt"
STOP_TIMES_FILE_NAME = "stop_times.txt"
TRIPS_FILE_NAME = "trips.txt"

DALY_CITY_AMBIGUOUS = "1"
AMBIGUOUS = set([DALY_CITY_AMBIGUOUS])

HEADSIGN_MAP = {
    # Red Line
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
    "San Francisco Int'l Airport/Millbrae": "Yellow SB (SFO/Millbrae)",

    # Blue Line
    "Dublin/Pleasanton": "Blue EB (Dublin/Plsntn)",
    "SF / OAK Airport / Dublin/Pleasanton": "Blue EB (Dublin/Plsntn)",
    "Bay Fair": "Blue WB (Bay Fair only)",

    # Ambiguous
    "OAK Airport / SF / Daly City": DALY_CITY_AMBIGUOUS,

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

def get_station_name_for_id() -> Dict[str, str]:
    """
    Returns a dictionary mapping station IDs to their names.
    """
    station_id_name_map = {}
    with open(f"{os.environ['BART_DATA_ROOT']}/{STOPS_FILE_NAME}", "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            stop_id = row[0]
            stop_name = row[2]
            station_id_name_map[stop_id] = stop_name
    return station_id_name_map

def get_ids_for_station_name() -> Dict[str, List[str]]:
    """
    Returns a dictionary mapping station names to their IDs.
    """
    station_name_ids_map: Dict[str, List[str]] = {}
    with open(f"{os.environ['BART_DATA_ROOT']}/{STOPS_FILE_NAME}", "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        for row in reader:
            stop_id = row[0]
            stop_name = row[2]
            if stop_name not in station_name_ids_map:
                station_name_ids_map[stop_name] = []
            station_name_ids_map[stop_name].append(stop_id)
    #for station_name, stop_ids in station_name_ids_map.items():
    #    print(f"Station: {station_name}, IDs: {', '.join(stop_ids)}")
    return station_name_ids_map

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


TripId = str

def trips_dict(filter_func: Optional[Callable]=None) -> Dict[TripId, TripInfo]:
    with open(f"{os.environ['BART_DATA_ROOT']}/{TRIPS_FILE_NAME}", "r") as f:
        reader = csv.reader(f)
        next(reader) # Skip header row
        trips: Dict[TripId, TripInfo] = {}
        for row in reader:
            trip_id: TripId = row[2]
            service_id = row[1]
            trip_headsign = row[3]
            if filter_func is None or filter_func(trip_id, service_id, trip_headsign):
                trips[trip_id] = TripInfo(
                    service_id=service_id,
                    trip_id=trip_id,
                    trip_headsign=trip_headsign,
            )
        return trips

StopTimeInfo = namedtuple(
    "StopTimeInfo", ["departure_time", "stop_headsign", "trip_id", "service_id", "stop_id"])


def get_stop_times(
        target_station_ids: Optional[List[str]],
        trips_dict: Optional[Dict[TripId, TripInfo]] = None) -> List[StopTimeInfo]:
    trips: List[StopTimeInfo] = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOP_TIMES_FILE_NAME}", "r")  as f:
        reader = csv.reader(f)
        next(reader) # Skip header row
        for row in reader:
            # trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_distance_traveled
            stop_id = row[3]
            if target_station_ids is None or stop_id in target_station_ids:
                trip_id = row[0]
                departure_time = row[2]
                stop_id = row[3]
                stop_headsign = row[5]
                if trips_dict and not stop_headsign:
                    stop_headsign = trips_dict[trip_id].trip_headsign

                if trips_dict:
                    service_id = trips_dict[trip_id].service_id
                else:
                    service_id = None

                trips.append(StopTimeInfo(departure_time, stop_headsign, trip_id, service_id, stop_id))

    return trips

ServiceIdHeadsign = namedtuple("ServiceIdHeadsign", ["service_id", "stop_headsign"])

FirstLastTimes = namedtuple("FirstLastTimes", ["first", "last"])


def first_last_times(trips: List[StopTimeInfo]) -> Dict[ServiceIdHeadsign, FirstLastTimes]:
    first_map: Dict[ServiceIdHeadsign, str] = {}
    last_map: Dict[ServiceIdHeadsign, str] = {}
    for stop_time_info in trips:
        key = ServiceIdHeadsign(stop_time_info.service_id, stop_time_info.stop_headsign)
        time = stop_time_info.departure_time
        if time < first_map.get(key, "99:99:99"):
            first_map[key] = time
        if time > last_map.get(key, "00:00:00"):
            last_map[key] = time

    return {key: FirstLastTimes(first_map[key], last_map[key]) for key in first_map}

def get_label_for_service_id(service_id: str) -> str:
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

    return service_map.get(service_id, service_id)

def get_line_for_headsign(headsign: str, station_name: Optional[str] = None) -> str:
    # If headsign is not in the map, center it with asterisks so it stands out.
    if headsign not in HEADSIGN_MAP.keys():
        headsign = headsign.center(50, '*')
    headsign = HEADSIGN_MAP.get(headsign, headsign)
    if headsign in AMBIGUOUS:
        if headsign == DALY_CITY_AMBIGUOUS:
            if station_name in ["Hayward", "South Hayward", "Union City", "Fremont", "Warm Springs/South Fremont", "Milpitas", "Berryessa/North San Jose"]:
                headsign = "Green WB (Daly City)"
            elif station_name in ["Castro Valley", "West Dublin/Pleasanton", "Dublin/Pleasanton"]:
                headsign = "Blue WB (Daly City)"
            else:
                headsign = "Blue/Green WB (Daly City)"
    # headsign = replaced_headsign_destination_only(headsign)
    return headsign


def map_service_id_to_label(service_id, headsign=None) -> str:

    return f"{get_label_for_service_id(service_id)} - {get_line_for_headsign(headsign)}"

def replaced_headsign_destination_only(replaced_headsign: str) -> str:
    # Yellow NB (Pts/BayPt) -> Pts/BayPt
    start = replaced_headsign.find('(')
    end = replaced_headsign.find(')')
    return replaced_headsign[start + 1:end].strip() if start != -1 and end != -1 else replaced_headsign

def print_first_last_times(trips: List[StopTimeInfo]) -> None:
    first_last = first_last_times(trips)
    service_label_time_map = {map_service_id_to_label(key): v for key, v in first_last.items()}
    max_key_length = max(len(key) for key in service_label_time_map.keys())

    for key in sorted(service_label_time_map):
        # Expect each value in replace_map to be a tuple of (first, last) times.
        print(f"{key.ljust(max_key_length)}: {service_label_time_map[key].first} - {service_label_time_map[key].last}")

def print_system_first_last_times() -> None:
    all_trips = trips_dict()
    stop_times = get_stop_times(None, all_trips)
    first_stop = min(stop_times, key=lambda x: x.departure_time)
    last_stop = max(stop_times, key=lambda x: x.departure_time)
    station_names_for_id = get_station_name_for_id()

    def format_stop_time_info(stop_time_info: StopTimeInfo) -> str:
        return (
            f"Time: {stop_time_info.departure_time}\n"
            f"Stop Name: {station_names_for_id.get(stop_time_info.stop_id)}\n"
            f"Line: {get_line_for_headsign(stop_time_info.stop_headsign, None)}\n"
            f"Headsign: {stop_time_info.stop_headsign}\n"
        )

    print(f"System First Stop:\n{format_stop_time_info(first_stop)}")
    print(f"System Last Stop:\n{format_stop_time_info(last_stop)}")

    pass

def print_first_last_times_db(bartdb: BartDb, station_name: str) -> None:
    stop_ids = get_station_ids(station_name)
    first_stops = bartdb.first_stop_time(stop_ids)

    for i, row in enumerate(first_stops):
        departure_time, service_id, headsign, route_short_name = row
        service_id = get_label_for_service_id(service_id)
        route_short_name = map_route_short_name(route_short_name)
        first_stops[i] = (departure_time, service_id, headsign, route_short_name)
    service_order = ["Saturday", "Sunday", "Weekday"]
    route_order = ["Red", "Orange", "Yellow", "Green", "Blue", "Grey"]

    def sort_key(row):
        departure_time, service_id, headsign, route_short_name = row
        service_index = service_order.index(service_id)
        portion_before_dash = route_short_name.split("-")[0]
        route_index = route_order.index(portion_before_dash)
        return (service_index, route_index, departure_time)
    first_stops.sort(key=sort_key)

    for row in first_stops:
        departure_time, service_id, headsign, route_short_name = row
        str = " ".join([
            departure_time,
            service_id.ljust(10),
            route_short_name.ljust(10),
            headsign.ljust(30)])
        print(str)

def map_route_short_name(route_short_name):
    route_short_name_map = {
            "Green-S": "Green-W",
            "Green-N": "Green-E",
            "Blue-S": "Blue-W",
            "Blue-N": "Blue-E",
            "Grey-N": "Grey-I",
            "Grey-S": "Grey-O"
        }
    route_short_name = route_short_name_map.get(route_short_name, route_short_name)
    return route_short_name

def print_first_last_train_per_station(bart_db: BartDb, station_name: str) -> None:
    first_last_trains = bart_db.first_last_trains_per_station_headsign(
        station_ids=get_station_ids(station_name),
        service_id_pattern="%Weekday%"
    )
    for train in first_last_trains:
        print(train)

def print_first_last_times_table(trips: List[StopTimeInfo], station_name: Optional[str] = None) -> None:
    first_last = first_last_times(trips)
    display_map = {f"{get_label_for_service_id(service_id)} - {get_line_for_headsign(headsign, station_name)}":
                   v for (service_id, headsign), v in first_last.items()}
    destinations = set(map(lambda key: key.split(' - ')[1], display_map.keys()))
    services = set(map(lambda key: key.split(' - ')[0], display_map.keys()))

    print_first_or_last((
        "First Trains", lambda x: x.first, "opened before", min), display_map, destinations, services)
    print()
    print_first_or_last((
        "Last Trains", lambda x: x.last, "closed after", max), display_map, destinations, services)

def print_first_or_last(
        print_specs: Tuple[str,  Callable[[FirstLastTimes], str], str, Callable[[Iterable[str]], str]],
        display_map: Dict[str, FirstLastTimes] ,
        destinations: Set[str],
        services:  Set[str]) -> None:
    first_col_len = max(len(dest) for dest in destinations)
    time_len = 8  # Length of time strings (HH:MM:SS)
    header_str = "| " + "Destinations".ljust(first_col_len) + " | "
    service_order = ["Weekday", "Saturday", "Sunday"]
    sorted_services = sorted(services, key=lambda x: service_order.index(x) if x in service_order else len(service_order))
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
        "Millbrae, No SFO", "Millbrae", "SFO/Millbrae", "SFO",
        "Daly City",
    ]
    for destination in sorted(destinations, key=lambda x: destination_order.index(x) if x in destination_order else x):
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
    unique_headsigns: Set[Tuple[str, str]] = set()
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


def print_first_last_for_station(station_name: str) -> None:
    stop_times = get_stop_times(get_station_ids(station_name), trips_dict())
    print_first_last_times_table(stop_times, station_name)

TEST_HEADSIGNS = True


def assertEqual(actual: object, expected: object) -> None:
    assert actual == expected, f"Assertion failed: actual '{actual}' but expected '{expected}'"

def test_daly_city_service() -> None:
    station_name: str = "Hayward"
    line_name: str = "Green WB (Daly City)"
    headsign: str = "OAK Airport / SF / Daly City"
    assertEqual(get_line_for_headsign(headsign, station_name), line_name)

    station_name = "Castro Valley"
    line_name = "Blue WB (Daly City)"
    headsign = "OAK Airport / SF / Daly City"
    assertEqual(get_line_for_headsign(headsign, station_name), line_name)

    station_name = "Bay Fair"
    line_name = "Blue/Green WB (Daly City)"
    headsign = "OAK Airport / SF / Daly City"
    assertEqual(get_line_for_headsign(headsign, station_name), line_name)

def all_stops_for(station_name: str) -> List[StopTimeInfo]:
    weekday_trips = trips_dict()
    stop_times = get_stop_times(get_station_ids(station_name), weekday_trips)
    def print_stop_time_info(stop_time_info: StopTimeInfo) -> str:
        return (
            f"Time: {stop_time_info.departure_time}, "
            f"Trip ID: {stop_time_info.trip_id}, "
            f"Service ID: {stop_time_info.service_id}, "
            f"Headsign: {stop_time_info.stop_headsign}"
        )
    return map(print_stop_time_info, stop_times)

if __name__ == "__main__":
    if TEST_HEADSIGNS:
        success = test_headsign_names()
        if not success:
            print("Some headsigns are missing mappings in HEADSIGN_MAP.")
            exit(1)
    test_daly_city_service()
    # print_system_first_last_times()
    #print_first_last_for_station("Daly City")


    #for stop_time_info in all_stops_for(station_name="Hayward"):
        #print(stop_time_info)

    #bartdb = BartDb()
    #bartdb.connect()
    #print_first_last_train_per_station(bartdb, "19th")
    trips_dict = trips_dict()
    station_name = "Bay Fair"
    stop_times = get_stop_times(get_station_ids(station_name), trips_dict)
    print_first_last_times_table(stop_times, station_name)
    #bartdb.disconnect()
    #test_daly_city_service()
    #print(trips_dict())
