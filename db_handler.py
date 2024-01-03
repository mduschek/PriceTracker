import sqlite3
import json
import pandas as pd


class DbHandler:

    def __init__(self):
        self.conn = None

    def init_db(self):
        self.conn = sqlite3.connect('pricetracker.db')
        cursor = self.conn.cursor()

        # Create a table
        cursor.execute('''CREATE TABLE IF NOT EXISTS tracked_elements (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            domain_name VARCHAR(255) NOT NULL,
                            url VARCHAR(2048) NOT NULL,
                            xpath TEXT NOT NULL,
                            update_interval INTEGER NOT NULL,
                            min_price_threshold DOUBLE,
                            max_price_threshold DOUBLE,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            notify BOOLEAN NOT NULL DEFAULT TRUE
                        )''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
                            id INTEGER PRIMARY KEY,
                            current_price DOUBLE NOT NULL,
                            timestamp TIMESTAMP NOT NULL,
                            tracked_elements_id INTEGER NOT NULL,
                            FOREIGN KEY (tracked_elements_id) REFERENCES tracked_elements (id)
                        )''')

        self.conn.commit()

    def insert_tracked_element(self, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''INSERT INTO tracked_elements 
                                  (name, domain_name, url, xpath, update_interval, min_price_threshold, 
                                  max_price_threshold, is_active, notify) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (row['name'], row['domain_name'], row['url'], row['xpath'], row['update_interval'],
                                row['min_price_threshold'], row['max_price_threshold'], row['is_active'],
                                row['notify']))
            self.conn.commit()
            print("Data inserted successfully!")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def insert_price_history(self, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''INSERT INTO price_history 
                                  (tracked_elements_id, current_price, timestamp) 
                                  VALUES (?, ?, ?)''',
                                  (row['tracked_elements_id'], row['current_price'], row['timestamp']))
            self.conn.commit()
            print("Data inserted successfully!")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def retrieve_tracked_elements(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM tracked_elements''')
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'name', 'domain_name', 'url', 'xpath', 'update_interval',
                                                 'min_price_threshold', 'max_price_threshold', 'is_active', 'notify'])
                print("Tracked elements retrieved successfully!")
                return df
            else:
                print("No tracked elements found in the database")
                return pd.DataFrame()  # Return an empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving tracked elements: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

    def retrieve_price_history(self, element_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM price_history WHERE tracked_elements_id = ?''', (element_id,))
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'tracked_elements_id', 'current_price', 'timestamp'])
                print("Data retrieved successfully!")
                return df
            else:
                print("No data found for the given element_id")
                return pd.DataFrame()  # Return an empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving data: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error


    # Function to retrieve a row by IP from the SQLite database
    # def retrieve_all_geolocations(self):
    #     cursor = self.conn.cursor()
    #
    #     # Retrieve row by IP address
    #     cursor.execute("SELECT * FROM ip_geolocation")  # Get column names
    #     columns = [description[0] for description in cursor.description]
    #     rows = cursor.fetchall()
    #     if not rows:
    #         return None
    #
    #     df = pd.DataFrame(rows, columns=columns)
    #
    #     return df

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
