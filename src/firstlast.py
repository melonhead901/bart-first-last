from typing import List, Tuple, Optional, Dict
import os
import csv

STOPS = "stops.txt"
STOP_TIMES = "stop_times.txt"
TRIPS = "trips.txt"

def get_19th_street_station_ids() -> List[str]:
    """
    Returns the stop IDs for the 19th Street stop.
    """
    stop_ids = []
    with open(f"{os.environ["BART_DATA_ROOT"]}/{STOPS}", "r")  as f:
        reader = csv.reader(f)
        for row in reader:
            stop_id = row[0]
            stop_name = row[2]
            if "19th Street Oakland" in stop_name:
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
    if service_id == "2025_08_11-SA-MVS-Saturday-000":
        service_id = "Saturday"
    elif service_id == "2025_08_11-SU-MVS-Sunday-000":
        service_id = "Sunday"
    elif service_id == "2025_08_11-DX-MVS-Weekday-003":
        service_id = "Weekday"

    if headsign == "Richmond":
        headsign = "Red/Orange NB (Richmond)"
    elif headsign == "SF / SFO Airport / Millbrae":
        headsign = "Red SB (Millbrae)"
    elif headsign == "Antioch":
        headsign = "Yellow NB (Antioch)"
    elif headsign == "Pittsburg / Bay Point":
        headsign = "Yellow NB (Pts/BayPt)"
    elif headsign == "San Francisco International Airport":
        headsign = "Yellow SB (SFO)"
    elif headsign == "Millbrae (Caltrain Transfer Platform)":
        headsign = "Yellow SB (Millbrae)"
    elif headsign == "San Francisco Int'l Airport/Millbrae":
        headsign = "Yellow SB (SFO/Millbrae)"
    elif headsign == "OAK Airport / Berryessa/North San Jose":
        headsign = "Orange SB (Berryessa)"
    
    return f"{service_id} - {headsign}"

def print_first_last_times(trips: List[Tuple[str, str, Optional[str]]]):
    first_last = first_last_times(trips)
    replace_map = {key_replacement(key): v for key, v in first_last.items()}
    keys = list(replace_map.keys())
    keys.sort()

    for key in keys:
        # Expect each value in replace_map to be a tuple of (first, last) times
        first, last = replace_map[key]
        print(f"{key}: {first} - {last}")

if __name__ == "__main__":
    print_first_last_times(trips_for_stop_ids(
        station_ids=get_19th_street_station_ids(),
        trips_dict=trips_dict()))
    #print(trips_dict())