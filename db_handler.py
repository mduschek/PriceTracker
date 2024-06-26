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
                            update_interval INTEGER NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            regex TEXT NOT NULL
                        )''')

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
                                  (name, url, xpath, update_interval, is_active, regex) 
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                               (row['name'], row['url'], row['xpath'], row['update_interval'],
                                row['is_active'], row['regex']))
            self.conn.commit()
            return cursor.lastrowid  # return new id
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    def update_tracked_element(self, id_, df):
        cursor = self.conn.cursor()
        try:
            for index, row in df.iterrows():
                cursor.execute('''UPDATE tracked_elements 
                                  SET name=?, url=?, xpath=?, update_interval=?, 
                                     is_active=?, regex=? 
                                  WHERE id=?''',
                               (row['name'], row['url'], row['xpath'], row['update_interval'],
                                row['is_active'], row.get('regex', ''), int(id_)))
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
            return True
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            return False

    def retrieve_tracked_elements(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM tracked_elements''')
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'name', 'url', 'xpath', 'update_interval',
                                                 'is_active', 'regex'])
                return df
            else:
                return pd.DataFrame()  # return empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving tracked elements: {e}")
            return pd.DataFrame()  # return empty DataFrame in case of error

    def retrieve_tracked_element_by_id(self, element_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM tracked_elements WHERE id = ?''', (element_id,))
            row = cursor.fetchone()
            if row:
                tracked_element = {
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'xpath': row[3],
                    'update_interval': row[4],
                    'is_active': row[5],
                    'regex': row[6]
                }
                return tracked_element
            else:
                return {}  # return empty dictionary if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving tracked element: {e}")
            return {}  # return empty dictionary in case of an error

    def retrieve_price_history(self, element_ids):
        try:
            cursor = self.conn.cursor()
            # use the IN clause to fetch data for all specified element_ids
            cursor.execute('''SELECT * FROM price_history WHERE tracked_elements_id IN ({})'''.format(
                ','.join(['?'] * len(element_ids))), element_ids)
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'tracked_elements_id', 'current_price', 'timestamp'])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            else:
                return pd.DataFrame()  # return empty DataFrame if no data found
        except sqlite3.Error as e:
            print(f"Error retrieving data: {e}")
            return pd.DataFrame()  # return empty DataFrame in case of an error

    def delete_tracked_element_by_id(self, ids_to_delete):
        cursor = self.conn.cursor()
        try:
            for id_to_delete in ids_to_delete:
                # delete price history associated with the element
                cursor.execute('''DELETE FROM price_history WHERE tracked_elements_id = ?''', (id_to_delete,))
                print(f"Deleted {cursor.rowcount} price history records.")

                # delete the element
                cursor.execute('''DELETE FROM tracked_elements WHERE id = ?''', (id_to_delete,))
                if cursor.rowcount == 0:
                    print("No tracked element found with the given ID.")

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            # roll back in case of error
            self.conn.rollback()
            print(f"Error deleting data: {e}")
            return False

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
