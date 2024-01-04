import threading
from dotenv import dotenv_values
import subprocess
import sys
import gui
from crawly import Crawly
from db_handler import DbHandler


def main():
    print("Start")

    subprocess.run([f"{sys.executable}", "crawly.py"])

    db_handler = DbHandler()
    if db_handler.conn is None:
        db_handler.init_db()

    gui.main(db_handler)

    # gui_thread = threading.Thread(target=gui.main(db_handler))
    # gui_thread.daemon = True  # Daemonize the thread to exit when the main thread exits
    # gui_thread.start()
    #
    # # start scheduler
    # scheduler = Crawly(db_handler)
    # scheduler.run()


# Check if the script is being run as the main program
if __name__ == '__main__':
    env_values = dotenv_values('.env')
    # key = env_values.get('KEY')
    main()



