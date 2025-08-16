from typing import List, Tuple, Optional, Dict
import os
import csv

STOPS = "stops.txt"
STOP_TIMES = "stop_times.txt"
TRIPS = "trips.txt"

def get_station_ids(station_name: str) -> List[str]:
    """
    Returns the stop IDs for the given station name.
    """
    stop_ids = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOPS}", "r")  as f:
        reader = csv.reader(f)
        for row in reader:
            stop_id = row[0]
            stop_name = row[2]
            if station_name in stop_name:
                stop_ids.append(stop_id)
    return stop_ids

#print(get_19th_street_station_ids())

def trips_for_stop_ids(station_ids: List[str], trips_dict=None) -> List[Tuple[str, str, Optional[str]]]:
    trips = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOP_TIMES}", "r")  as f:
        reader = csv.reader(f)
        for row in reader:
            # trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type,drop_off_type,shape_distance_traveled
            stop_id = row[3]
            if stop_id in station_ids:
                trip_id = row[0]
                arrival_time = row[1]
                departure_time = row[2]
                stop_sequence = row[4]
                stop_headsign = row[5]
                if trips_dict and not stop_headsign:
                    stop_headsign = trips_dict[trip_id]["trip_headsign"]
                pickup_type = row[6]
                drop_off_type = row[7]
                shape_distance_traveled = row[8]

                if trips_dict:
                    service_id = trips_dict[trip_id]["service_id"]
                else:
                    service_id = None
                
                trips.append((departure_time, stop_headsign, service_id))
    return trips

def trips_dict() -> Dict[str, Dict[str, str]]:
    with open(f"{os.environ["BART_DATA_ROOT"]}/{TRIPS}", "r")  as f:
        reader = csv.reader(f)
        trips = {}
        for row in reader:
            trip_id = row[2]
            service_id = row[1]
            trip_headsign = row[3]
            trips[trip_id] = {
                "service_id": service_id,
                "trip_id": trip_id,
                "trip_headsign": trip_headsign,
            }
        return trips


def first_last_times(trips: List[Tuple[str, str, Optional[str]]]) -> Dict[Tuple[str, str], Tuple[str, str]]:
    first_map = {}
    for time, headsign, service_id in trips:
        key = (service_id, headsign)
        if key not in first_map:
            first_map[key] = time
        else:
            first_map[key] = min(first_map[key], time)

    last_map = {}
    for time, headsign, service_id in trips:
        key = (service_id, headsign)
        if key not in last_map:
            last_map[key] = time
        else:
            last_map[key] = max(last_map[key], time)

    return {key: (first_map[key], last_map[key]) for key in first_map}

def key_replacement(key: Tuple[str, str]) -> str:
    service_id, headsign = key
    service_map = {
        "2025_08_11-SA-MVS-Saturday-000": "Saturday",
        "2025_08_11-SU-MVS-Sunday-000": "Sunday",
        "2025_08_11-DX-MVS-Weekday-003": "Weekday",
    }
    headsign_map = {
        "Richmond": "Red/Orange NB (Richmond)",
        "SF / SFO Airport / Millbrae": "Red SB (Millbrae)",
        "Antioch": "Yellow NB (Antioch)",
        "Pittsburg / Bay Point": "Yellow NB (Pts/BayPt)",
        "San Francisco International Airport": "Yellow SB (SFO)",
        "Millbrae (Caltrain Transfer Platform)": "Yellow SB (Millbrae only)",
        "San Francisco Int'l Airport/Millbrae": "Yellow SB (SFO/Millbrae)",
        "OAK Airport / Berryessa/North San Jose": "Orange SB (Berryessa)",
    }
    service_id = service_map.get(service_id, service_id)
    headsign = headsign_map.get(headsign, headsign)
    
    return f"{service_id} - {headsign}"

def print_first_last_times(trips: List[Tuple[str, str, Optional[str]]]):
    first_last = first_last_times(trips)
    display_map = {key_replacement(key): v for key, v in first_last.items()}

    for key in sorted(display_map):
        # Expect each value in replace_map to be a tuple of (first, last) times
        first, last = display_map[key]
        print(f"{key}: {first} - {last}")

if __name__ == "__main__":
    station_name = "19th Street Oakland"
    print_first_last_times(trips_for_stop_ids(
        station_ids=get_station_ids(station_name),
        trips_dict=trips_dict()))
    #print(trips_dict())