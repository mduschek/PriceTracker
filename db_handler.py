import sqlite3
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
                            url VARCHAR(2048) NOT NULL,
                            xpath TEXT NOT NULL,
                            regex TEXT NOT NULL,
                            update_interval INTEGER NOT NULL,
                            min_price_threshold DOUBLE,
                            max_price_threshold DOUBLE,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            notify BOOLEAN NOT NULL DEFAULT TRUE
                        )''')

        #cursor.execute('''ALTER TABLE tracked_elements ADD COLUMN regex TEXT''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS price_history (
                            id INTEGER PRIMARY KEY,
                            tracked_elements_id INTEGER NOT NULL,
                            current_price DOUBLE NOT NULL,
                            timestamp TIMESTAMP NOT NULL,
                            FOREIGN KEY (tracked_elements_id) REFERENCES tracked_elements (id)
                        )''')

        self.conn.commit()

    def insert_tracked_element(self, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''INSERT INTO tracked_elements 
                                  (name, url, xpath, update_interval, min_price_threshold, 
                                  max_price_threshold, is_active, notify, regex) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (row['name'], row['url'], row['xpath'], row['update_interval'],
                                row['min_price_threshold'], row['max_price_threshold'], row['is_active'],
                                row['notify'], row['regex']))
            self.conn.commit()
            # print("Data inserted successfully!")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def update_tracked_element(self, id_, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''UPDATE tracked_elements 
                                  SET name=?, url=?, xpath=?, update_interval=?, 
                                      min_price_threshold=?, max_price_threshold=?, 
                                      is_active=?, notify=?, regex=? 
                                  WHERE id=?''',
                               (row['name'], row['url'], row['xpath'], row['update_interval'],
                                row['min_price_threshold'], row['max_price_threshold'], row['is_active'],
                                row['notify'], row.get('regex', ''), int(id_)))
                print(f"Done updating row {index + 1}/{len(df)}. Rows affected: {cursor.rowcount}")
            self.conn.commit()
            print("Data updated successfully!")
        except sqlite3.Error as e:
            print(f"Error updating data: {e}")

    def insert_price_history(self, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''INSERT INTO price_history 
                                  (tracked_elements_id, current_price, timestamp) 
                                  VALUES (?, ?, ?)''',
                                  (row['tracked_elements_id'], row['current_price'], row['timestamp']))
            self.conn.commit()
            # print("Data inserted successfully!")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def retrieve_tracked_elements(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM tracked_elements''')
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'name', 'url', 'xpath', 'update_interval',
                                                 'min_price_threshold', 'max_price_threshold', 'is_active', 'notify', 'regex'])
                # print("Tracked elements retrieved successfully!")
                return df
            else:
                # print("No tracked elements found in the database")
                return pd.DataFrame()  # Return an empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving tracked elements: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

    def retrieve_price_history(self, element_ids):
        try:
            cursor = self.conn.cursor()
            # Use the IN clause to fetch data for all specified element_ids
            cursor.execute('''SELECT * FROM price_history WHERE tracked_elements_id IN ({})'''.format(','.join(['?']*len(element_ids))), element_ids)
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'tracked_elements_id', 'current_price', 'timestamp'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # print("Data retrieved successfully!")
                return df
            else:
                # print("No data found for the given element_ids")
                return pd.DataFrame()  # Return an empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving data: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of an error

    def delete_tracked_element_by_id(self, ids_to_delete):
        cursor = self.conn.cursor()
        try:
            # Start a transaction
            for id_to_delete in ids_to_delete:
                # First, delete the price history associated with the element
                cursor.execute('''DELETE FROM price_history WHERE tracked_elements_id = ?''', (id_to_delete,))
                print(f"Deleted {cursor.rowcount} price history records.")

                # Next, delete the element itself
                cursor.execute('''DELETE FROM tracked_elements WHERE id = ?''', (id_to_delete,))
                if cursor.rowcount == 0:
                    print("No tracked element found with the given ID.")
                # else:
                #     print("Tracked element deleted successfully!")

            # Commit the transaction
            self.conn.commit()

        except sqlite3.Error as e:
            # Roll back the transaction in case of error
            self.conn.rollback()
            print(f"Error deleting data: {e}")

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
