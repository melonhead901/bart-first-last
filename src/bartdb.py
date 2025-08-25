import sqlite3
import csv
import os

class BartDb:
    DB_PATH = f'{os.environ["BART_DATA_ROOT"]}/bartdb.db'
    def __init__(self):
        self.conn = None
        self.cursor = None
        pass

    def connect(self):
        if not self.conn:
            self.conn = sqlite3.connect(self.DB_PATH)
            self.cursor = self.conn.cursor()
        else :
            raise Exception("Already connected to the database.")

    def load_stop_times(self):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''DROP TABLE IF EXISTS stop_times;''')

        self.cursor.execute('''
            CREATE TABLE stop_times (
                trip_id TEXT,
                arrival_time TEXT,
                departure_time TEXT,
                stop_id TEXT,
                stop_sequence INTEGER,
                stop_headsign TEXT,
                PRIMARY KEY (trip_id, stop_sequence)
            )
        ''')
        self.conn.commit()

        with open(f'{os.environ["BART_DATA_ROOT"]}/stop_times.txt', 'r') as f:
            reader = csv.DictReader(f)
            stop_times = [(row['trip_id'], row['arrival_time'], row['departure_time'], row['stop_id'], row['stop_sequence'], row['stop_headsign'] or None) for row in reader]

        self.cursor.executemany('INSERT INTO stop_times (trip_id, arrival_time, departure_time, stop_id, stop_sequence, stop_headsign) VALUES (?, ?, ?, ?, ?, ?)', stop_times)
        self.conn.commit()

    def load_trips(self):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''DROP TABLE IF EXISTS trips;''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                trip_id TEXT PRIMARY KEY,
                service_id TEXT,
                route_id TEXT,
                trip_headsign TEXT
            )
        ''')
        self.conn.commit()

        with open(f'{os.environ["BART_DATA_ROOT"]}/trips.txt', 'r') as f:
            reader = csv.DictReader(f)
            trips = [(row['trip_id'], row['service_id'],row['route_id'], row['trip_headsign']) for row in reader]

        self.cursor.executemany('INSERT INTO trips (trip_id, service_id, route_id, trip_headsign) VALUES (?, ?, ?, ?)', trips)
        self.conn.commit()

    def load_stops(self):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stops (
                stop_id TEXT PRIMARY KEY,
                stop_name TEXT,
                stop_lat REAL,
                stop_lon REAL
            )
        ''')
        self.conn.commit()

        with open(f'{os.environ["BART_DATA_ROOT"]}/stops.txt', 'r') as f:
            reader = csv.DictReader(f)
            stops = [(row['stop_id'], row['stop_name'], row['stop_lat'], row['stop_lon']) for row in reader]

        self.cursor.executemany('INSERT INTO stops (stop_id, stop_name, stop_lat, stop_lon) VALUES (?, ?, ?, ?)', stops)
        self.conn.commit()


    def load_routes(self):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''DROP TABLE IF EXISTS routes;''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE routes (
                route_id TEXT PRIMARY KEY,
                route_short_name TEXT,
                route_long_name TEXT,
                route_type INTEGER
            )
        ''')
        self.conn.commit()

        with open(f'{os.environ["BART_DATA_ROOT"]}/routes.txt', 'r') as f:
            reader = csv.DictReader(f)
            routes = [(row['route_id'], row['route_short_name'], row['route_long_name'], row['route_type']) for row in reader]

        self.cursor.executemany('INSERT INTO routes (route_id, route_short_name, route_long_name, route_type) VALUES (?, ?, ?, ?)', routes)
        self.conn.commit()

    def check_5_rows(self, table_name):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''DROP TABLE IF EXISTS routes;''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE routes (
                route_id TEXT PRIMARY KEY,
                route_short_name TEXT,
                route_long_name TEXT,
                route_type INTEGER
            )
        ''')
        self.conn.commit()

        with open(f'{os.environ["BART_DATA_ROOT"]}/routes.txt', 'r') as f:
            reader = csv.DictReader(f)
            routes = [(row['route_id'], row['route_short_name'], row['route_long_name'], row['route_type']) for row in reader]

        self.cursor.executemany('INSERT INTO routes (route_id, route_short_name, route_long_name, route_type) VALUES (?, ?, ?, ?)', routes)
        self.conn.commit()

    def check_5_rows(self, table_name):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute(f'SELECT * FROM {table_name} LIMIT 5')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def print_5_joined_trips(self):
        for row in self.joined_stop_times():
            print(row)

    def first_stop_time(self, stop_ids):
        self.cursor.execute(
            f"""SELECT MIN(departure_time), service_id, COALESCE(stop_headsign, trip_headsign) AS headsign, route_short_name
            FROM stop_times
            JOIN stops ON stop_times.stop_id = stops.stop_id
            JOIN trips ON stop_times.trip_id = trips.trip_id
            JOIN routes ON trips.route_id = routes.route_id
            WHERE stops.stop_id IN ({', '.join(repr(x) for x in stop_ids)}) AND departure_time IS NOT NULL
            GROUP BY service_id, headsign, route_short_name
            ORDER BY service_id, departure_time

            """

        )
        rows = self.cursor.fetchall()
        return rows

    def joined_stop_times(self):
        if not self.conn:
            raise Exception("Database not connected. Call connect() first.")

        self.cursor.execute('''
            SELECT stop_name, service_id, departure_time, coalesce(stop_headsign, trip_headsign) AS headsign, route_short_name
            FROM trips
            JOIN stop_times ON trips.trip_id = stop_times.trip_id
            JOIN stops ON stop_times.stop_id = stops.stop_id
            JOIN routes ON trips.route_id = routes.route_id
            LIMIT 5
        ''')
        rows = self.cursor.fetchall()
        return rows

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None


if __name__ == "__main__":
    db = BartDb()
    db.connect()
    #db.load_trips()
    #db.load_stop_times()
    #db.load_stops()
    #db.load_trips()
    #db.load_routes()
    #db.check_5_rows("trips")
    #db.print_5_joined_trips()
    db.disconnect()


