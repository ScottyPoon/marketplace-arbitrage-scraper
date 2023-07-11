import os
import re
import base64
import json
import time
from datetime import datetime, timedelta
import numpy as np
import undetected_chromedriver as uc
from github import Github
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import SessionNotCreatedException
from get_blob import get_blob_content
from calculate_liquidity import calculate_liquidity
from parse_numeric_array import parse_numeric_array


def setup_chrome_driver():
    """
    Sets up and initializes an undetected ChromeDriver.

    :return: The initialized ChromeDriver instance.
    """
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    session = {'name': 'mptf', 'value': os.environ['COOKIE'], 'domain': f".{os.environ['DOMAIN']}", 'secure': True}

    driver = uc.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
    driver.get(f"https://{os.environ['DOMAIN']}/")
    driver.add_cookie(session)

    driver.refresh()
    return driver


def initialize_tf2_items_dict():
    """
    Initializes the TF2 items dictionary by fetching and parsing the items.json file from a GitHub repository.

    :return: The initialized TF2 items dictionary.
    """
    # Initialize the TF2 items dictionary
    token = os.environ['HUB_TOKEN']
    repo_name = os.environ['REPO_NAME_RETRIEVE']
    github = Github(token)
    repository = github.get_user().get_repo(repo_name)

    blob = get_blob_content(repository, "main", "items.json")
    b64 = base64.b64decode(blob.content)
    tf2_items_dict = json.loads(b64.decode())

    return tf2_items_dict


def scrape_marketplace():
    """
    Scrapes data from the marketplace website for TF2 items, calculates liquidity and other statistics and creates a
    json file of scraped data.

    :return: None
    """
    scraped_data = {}

    tf2_items_dict = initialize_tf2_items_dict()

    driver = setup_chrome_driver()
    try:
        for i, (key, sku) in enumerate(tf2_items_dict.items(), 1):

            print(f"Iteration {i}/{len(tf2_items_dict)}")
            if key.startswith('#'):
                continue
            elif ';u' in sku:
                continue
            else:
                url = f"https://{os.environ['DOMAIN']}/items/tf2/{sku}"

                driver.get(url)
                try:
                    # wait 2 seconds for the element to appear
                    wait = WebDriverWait(driver, 2)
                    text = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//script[contains(text(), 'var data = ')]"))).get_attribute('innerHTML')
                except TimeoutException:
                    # handle the case when the element is not found within 2 seconds
                    print("Element not found after waiting for 2 seconds, continuing...")
                    continue

                my_dict = {}

                date_regex = r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{1,2},\s\d{4}\b'
                dates = re.findall(date_regex, text)

                pattern = r'data:\s*\[([^]]*)\]'

                # Find all matches
                matches = re.findall(pattern, text)

                # Print the matches
                price_array = parse_numeric_array(matches[0][:-1])

                volume_array = parse_numeric_array(matches[1][:-1])

                # Calculate Z-scores via price outlier
                z_scores = np.abs((price_array - np.mean(price_array)) / np.std(price_array))

                # Find indices of outliers
                outlier_indices = np.where(z_scores > 3)[0]

                # Remove outliers from all arrays
                dates = np.delete(dates, outlier_indices)
                price_array = np.delete(price_array, outlier_indices)
                volume_array = np.delete(volume_array, outlier_indices)

                liquidity = calculate_liquidity(dates, price_array, volume_array)

                if liquidity > 70:
                    print(f"\033[36mFor item {url} the len dates {len(dates)} liquidity {liquidity}\033[0m")
                elif liquidity > 50:
                    print(f"\033[32mFor item {url} the len dates {len(dates)} liquidity {liquidity}\033[0m")
                else:
                    print(f"For item {url} the len dates {len(dates)} liquidity {liquidity}")

                for x in range(len(dates)):
                    my_dict[dates[x]] = {'price': price_array[x], 'volume': volume_array[x]}

                # Get today's date
                today = datetime.today()

                # Initialize variables for calculating the statistics
                total_price = 0
                total_volume = 0
                days_counted = 0

                # Loop through the dictionary
                for date_str, data in my_dict.items():
                    # Convert the date string to a datetime object
                    date = datetime.strptime(date_str, '%b %d, %Y')

                    # Check if the date is within the past 7 days
                    if today - timedelta(days=7) <= date <= today:
                        # Add the price and volume for this day to the totals
                        total_price += data['price']
                        total_volume += data['volume']
                        days_counted += 1

                if days_counted > 0:
                    # Calculate the average price and volume
                    avg_price = total_price / days_counted
                    avg_volume = total_volume / days_counted
                    avg_sold_per_day = total_volume / 7  # Assumes 7 days counted
                else:
                    avg_price = 0
                    avg_volume = 0
                    avg_sold_per_day = 0

                scraped_data[key] = {
                    "sku": sku,
                    "7D_avg_price": round(avg_price, 2),
                    "7D_avg_volume": round(avg_volume, 2),
                    "7D_vol_per_day": round(avg_sold_per_day, 2),
                    "liquidity": liquidity
                }

                print("New Dict Len", len(scraped_data))

                with open("scraped_data.json", "w") as file:
                    json.dump(scraped_data, file)
    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting...")


def wait_for_input():
    """
    Waits for user input and initiates the scraping process.

    :return: None
    """
    start_time = time.time()
    while True:
        user_input = input("Enter 1 to start the scraping function: ")
        if user_input == "1":
            try:
                scrape_marketplace()
            except SessionNotCreatedException:
                print("Session not created exception caught, restarting program...")
                time.sleep(5)
                wait_for_input()

            token = os.environ['HUB_TOKEN']
            repo_name = os.environ['REPO_NAME_OUTPUT']
            github = Github(token)
            repository = github.get_user().get_repo(repo_name)
            with open("scraped_data.json", 'r') as file:
                data = file.read()
                contents = repository.get_contents("stats")
                repository.update_file(contents.path, "update dictionary", data, contents.sha)
            break

        else:
            print("\033[35mInvalid input. Please enter 1 to start the scraping function.\033[0m")

    end_time = time.time()
    total_time = end_time - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    print(f"Program took {hours} hours, {minutes} minutes, and {seconds} seconds to run.")
