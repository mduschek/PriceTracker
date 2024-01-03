import bs4 as bs
import requests
import streamlit as st
import plotly.express as px
import pandas as pd
import threading
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import dotenv_values


# def main():
#     select_field()

def open_browser():
    # global browser
    # Configure Firefox options
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument('--start-maximized')  # Maximize the browser window on startup

    # Initialize Firefox browser
    browser_ = webdriver.Firefox(options=firefox_options)
    # Open a website
    website_url = 'https://duckduckgo.com'  # Replace with the URL you want to open
    browser_.get(website_url)
    return browser_


def select_field(browser_):
    # Function to select a DOM element

    print(browser_.current_url)
    # element = browser_.find_element_by_xpath('https://www.amazon.de/feela-%C2%AE-Orthop%C3%A4disches-Sitzkissen-B%C3%BCrostuhl-inkl/dp/B07VHBZ69N/?_encoding=UTF8&ref_=dlx_gate_sd_dcl_tlt_ecd6e123_dt_pd_gw_unk&pd_rd_w=m1Kze&content-id=amzn1.sym.5b3ed663-dc9b-42d6-9b59-8397a19b7356&pf_rd_p=5b3ed663-dc9b-42d6-9b59-8397a19b7356&pf_rd_r=GBZ4JQECD45ECM5EY5FH&pd_rd_wg=KMAp2&pd_rd_r=2e3c928f-c517-4fbd-beb5-7a226a468324&th=1')  # Replace with your XPath
    # actions = ActionChains(browser_)
    # actions.move_to_element(element).click().perform()

# /html/body/div[2]/div/div[7]/div[4]/div[4]/div[13]/div/div/div[1]/div/div[3]/div[1]/span[2]

# Check if the script is being run as the main program
if __name__ == '__main__':
    env_values = dotenv_values('.env')
    # key = env_values.get('KEY')

    # main()

    # Create GUI
    root = tk.Tk()
    root.title("New Field")

    browser = open_browser()
    # Button to open browser
    # open_button = tk.Button(root, text="Open Browser", command=open_browser)
    # open_button.pack()

    # Button to select DOM element
    select_element_button = tk.Button(root, text="Select Element", command=lambda: select_field(browser))
    select_element_button.pack()

    root.mainloop()

    # Close the browser
    browser.quit()


