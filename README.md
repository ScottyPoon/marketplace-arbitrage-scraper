## Basic Overview
This is a public version of a Python program scrapes sales data from a marketplace website and calculates liquidity for each item using a custom algorithm. It is designed for arbitrage purposes and helps identify profitable items.

The program fetches a JSON containing the name of the item and SKU of the item stored in a private repository and iterates through each item, accessing the marketplace website using the corresponding SKU. Utlising Selenium to scrape the HTML content from the marketplace for price and volume data. 

## Liquidity Algorithm
The liquidity algorithm is used as a filter for the profitability ratio for arbitrage purposes. 

Using 3 data arrays each containing sales history data of a single item and using the data calculates financial indicators such as selling frequency, volitility, stability and average volume per day as weights to calculate and return a liquidity index score. 

The algorithm filters data within a 90-day timeframe to provide a more accurate representation of the current state of liquidity for each item. 

The ```statistics.stdev()``` function is used to calculate the standard deviation of the median_prices_90_days data. This value represents the measure of price volatility within the selected time range. A higher standard deviation indicates greater price fluctuations, while a lower value suggests more stability.

The ```z_scores``` are calculated to identify outliers within the ```median_prices_90_days``` data. A z-score measures how many standard deviations an individual data point is away from the mean. In this case, each median price in ```median_prices_90_days``` is transformed into a z-score by subtracting the mean and dividing by the price volatility. This normalization allows for comparison and identification of outliers which are filtered.

The ```price_stability_score``` is calculated by subtracting the standard deviation (```median_prices_std```) from the mean (```median_prices_mean```) of the ```median_prices_90_days```, and then dividing it by the sum of the mean and standard deviation.

Finally the ```liquidity_score``` is calculated using the financial indicators of selling frequency, average volume, and price stability score as weights, the weights are adjusted in terms of importance in the calculation. The resulting ```liquidity_score``` is constrained to be between 0 and 100.


```python
from datetime import datetime, timedelta
import statistics


def calculate_liquidity(date_strings, median_prices, volumes):
    # Get today's date and the date 90 days ago
    today = datetime.today()
    ninety_days_ago = today - timedelta(days=90)

    # Initialize variables for calculating liquidity score
    total_volume = 0
    median_prices_90_days = []

    # Loop through each data point and calculate total volume and median prices for the last 90 days
    for i, date_string in enumerate(date_strings):
        # Convert date string to datetime object
        date = datetime.strptime(date_string, '%b %d, %Y')
        if ninety_days_ago <= date <= today:  # if the date is within the last 90 days
            total_volume += int(volumes[i])  # add to the total volume
            median_prices_90_days.append(float(median_prices[i]))  # add to the list of median prices

    # Identify outliers in median_prices_90_days
    if len(median_prices_90_days) <= 1:
        return 0
    price_volatility = statistics.stdev(median_prices_90_days)
    if price_volatility == 0:
        price_volatility = 0.01
    z_scores = [(x - statistics.mean(median_prices_90_days)) / price_volatility for x in median_prices_90_days]
    outliers = [x for x, z in zip(median_prices_90_days, z_scores) if abs(z) > 3]

    # Remove outliers from median_prices_90_days
    median_prices_90_days = [x for x in median_prices_90_days if x not in outliers]

    selling_frequency = len(
        median_prices_90_days)  # calculate selling frequency (number of data points within last 90 days)

    # If there are less than 20 data points within the last 90 days, set average_volume and price_stability_score to 0
    if selling_frequency < 20:
        average_volume = 0
        price_stability_score = 0
    else:
        # Calculate average volume for the last 90 days
        average_volume = total_volume / len(median_prices_90_days)
        # Normalize average volume by 20
        average_volume = min(1, average_volume / 20)
        # Calculate standard deviation and mean of median prices for the last 90 days
        median_prices_std = statistics.stdev(median_prices_90_days)
        median_prices_mean = statistics.mean(median_prices_90_days)
        # Calculate price stability score
        price_stability_score = (median_prices_mean - median_prices_std) / (median_prices_mean + median_prices_std)
        price_stability_score = min(1, max(0,
                                           price_stability_score))  # ensure that price stability score is between 0 and 1

    # Calculate liquidity score using selling frequency, average volume, and price stability score
    liquidity_score = (66 * selling_frequency / 89) + 26 * average_volume + 8 * price_stability_score
    return round(max(0, min(100, liquidity_score)),
                 1)  # return liquidity score, rounded to 1 decimal point and between 0 and 100
```

## How to install

To build and run this application locally, you'll need latest versions of Git installed on your computer. From your command line:

```bash
# Clone this repository
$ git clone https://github.com/ScottyPoon/marketplace-arbitrage-scraper

# Install dependencies
$ pip3 install -r requirements.txt

# Run the app
$ python main.py
```

## Configuration

Before running the script, you need to configure the following environment variables:

**CHROMEDRIVER_PATH**: Set this variable to the path where you have installed ChromeDriver.

**COOKIE**: Set this variable to the value of the mptf cookie from the marketplace website. This cookie is used for authentication. The price and volume data will only load if you're authenticated.

**HUB_TOKEN**: Set this variable to your GitHub personal access token. The token should have the necessary permissions to update files in a repository.

**DOMAIN**: Set this variable to the domain of the marketplace website being scraped.

**REPO_NAME_RETRIEVE**: Set this variable to your repository name containing the TF2 item name, SKU pair. 

**REPO_NAME_OUTPUT**: Set this variable to your repository name where you want to output the scraped data as a JSON to.


## Heroku Deployment
The program can be deployed locally or via Heroku, using Heroku you can setup a scheduler to scrape at a desired time interval.

To use Selenium on Heroku the following buildpacks need to be installed by going to your-app > Settings > Buildpacks:
* https://github.com/heroku/heroku-buildpack-google-chrome - downloads and installs headless Google Chrome.
* https://github.com/heroku/heroku-buildpack-chromedriver - installs the chromedriver in a Heroku slug.

Next, to use Selenium you need to set the config vars on Heroku by going to your-app > Settings > Config Vars:
* KEY ```CHROMEDRIVER_PATH``` VALUE ```/app/.chromedriver/bin/chromedriver```
* KEY ```GOOGLE_CHROME_BIN``` VALUE ```/app/.apt/usr/bin/google-chrome```

Set the environmental variables mentioned in the Configuration section:
* KEY ```COOKIE``` VALUE ```your authentication cookie``` This can be found by going into the Browser's Developer Console (F12) > Cookies > corresponding value
* KEY ```HUB_TOKEN``` VALUE ```your GitHub personal access token```
* KEY ```DOMAIN``` VALUE ```marketplace domain name```
* KEY ```REPO_NAME_RETRIEVE``` VALUE ```your GitHub repository name containing the JSON data```
* KEY ```REPO_NAME_OUTPUT``` VALUE ```your GitHub repository name where you want the scraped data to be output to```

Create a Procfile:
* inside the Procfile write ```worker: python script.py```

Running the app:
* Run the app by writing ```python main.py``` inside of the Heroku console.

Automatic running at certain times:
* Install the Heroku Scheduler add-on to run the ```python main.py``` command to your desired time interval.

## Authors

* **Scotty Poon** - *Initial work* - [ScottyPoon](https://github.com/ScottyPoon)
