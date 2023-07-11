from datetime import datetime, timedelta
import statistics


def calculate_liquidity(date_strings, median_prices, volumes):
    """
    Calculates the liquidity score based on date strings, median prices, and volumes.

    :param date_strings: List of date strings.
    :param median_prices: List of median prices.
    :param volumes: List of volumes.
    :return: The calculated liquidity score.
    """
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
