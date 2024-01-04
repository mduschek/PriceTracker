import threading
import time

import requests
import schedule
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from db_handler import DbHandler


class Crawly:
    db_handler = None
    scheduled_tasks = None

    def __init__(self, _db_handler: DbHandler):
        print("Crawly init")
        self.db_handler = _db_handler
        if self.db_handler.conn is None:
            self.db_handler.init_db()

    def run(self):
        df_tracked_elements = self.db_handler.retrieve_tracked_elements()

        # create tasks
        for _, row in df_tracked_elements.iterrows():
            job = schedule.every(row['update_interval']).minutes
            # job.do(lambda te=row: self.run_threaded(self.execute_task(te)))
            job.do(self.run_threaded, row)

        print(schedule.get_jobs())

        # Run the scheduler
        ### THREADED APPROACH ###
        scheduler_thread = threading.Thread(target=self.run_scheduler)
        scheduler_thread.daemon = True  # Daemonize the thread to exit when the main thread exits
        scheduler_thread.start()

    def run_scheduler(self):
        schedule.run_all()
        while True:
            schedule.run_pending()
            time.sleep(1)  # Adjust as needed to control the frequency of checking for scheduled tasks

    def run_threaded(self, row):
        job_thread = threading.Thread(target=self.execute_task, args=[row])
        job_thread.start()

    def execute_task(self, tracked_element):
        print('Grabbing', tracked_element['name'], tracked_element['url'])
        url = tracked_element['url']
        xpath = tracked_element['xpath']

        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument('--headless')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(options=firefox_options)

        try:
            driver.get(url)

            # Wait for the element to be present on the page
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )

            # Extract the element text
            if element:
                print(element.text)
            else:
                print("Element not found")

        except WebDriverException as e:
            print(f"Selenium WebDriver error: {e}")
        except Exception as ex:
            print(f"An error occurred: {ex}")

        finally:
            driver.quit()  # Close the browser session


if __name__ == '__main__':
    print("Starting Scheduler...")

    db_handler = DbHandler()
    if db_handler.conn is None:
        db_handler.init_db()

    scheduler = Crawly(db_handler)
    # scheduler.add_task()
    scheduler.run()

    while True:
        time.sleep(1)
