import re
import threading
import time

# import requests
import schedule
# from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common import WebDriverException
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


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

    # Function to extract text content of an element using JavaScript

    def execute_task(self, tracked_element):
        print('Grabbing', tracked_element['name'], tracked_element['url'])
        url = tracked_element['url']
        xpath = tracked_element['xpath']
        regex = tracked_element['regex']

        # Pretend being a Human browsing the web
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.3"

        firefox_options = webdriver.FirefoxOptions()
        # firefox_options.add_argument('--headless')
        firefox_options.add_argument(f'user-agent={user_agent}')
        firefox_options.add_argument('--disable-gpu')
        driver = webdriver.Firefox(options=firefox_options)

        try:
            driver.get(url)

            # Wait for the element to be present on the page
            try:
                element = driver.find_element(By.XPATH, xpath)
            except:
                element = driver.find_element(By.CSS_SELECTOR, xpath)

            # element = WebDriverWait(driver, 20).until(
            #     # ec.presence_of_element_located((By.XPATH, xpath))
            #     ec.presence_of_element_located((By.CSS_SELECTOR, xpath))
            #     # ec.presence_of_element_located((By.CLASS_NAME, xpath))
            # )

            # Extract the element text
            if element:
                textContent = element.get_attribute("textContent")
                print("Price found:", tracked_element['name'] + ":", textContent)
                price_str = extract_price(textContent, regex)

                if price_str:
                    try:
                        extracted_price = float(price_str)
                        print(f"Extracted price as float: {extracted_price}")
                        # Now you can save price_float to the database

                    except ValueError:
                        print(f"Could not convert extracted price to float: {price_str}")
                else:
                    print("Could not extract price")

            else:
                print("Element not found")

        except WebDriverException as e:
            print("Selenium WebDriver error")
            # print(f"Selenium WebDriver error: {e}")
        except Exception as ex:
            print("An error occurred")
            # print(f"An error occurred: {ex}")

        finally:
            driver.quit()  # Close the browser session


def extract_price(text, pattern):
    match = re.search(pattern, text)
    if match:
        return match.group().replace(',', '.').replace('€', '')
    return None

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
