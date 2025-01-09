import time
import threading
import telebot
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

# Dictionary to store the time of last message for each user
last_message_time = {}

# Time to wait (in seconds) before allowing the user to send a message again
cooldown_time = 60  # 60 seconds = 1 minute

# Set up Telegram bot (use your bot token)
API_TOKEN = '7517971279:AAF-sY3Nu1q3RO7xcI66EjoV9NGnCiLDWtU'
bot = telebot.TeleBot(API_TOKEN)

# Semaphore to limit concurrent requests to 3
max_concurrent_requests = 3
semaphore = threading.Semaphore(max_concurrent_requests)

# Function to scrape information from the website
def scrape_lot(lot_number):
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run Chrome in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Ensure ChromeDriver is already installed and in PATH
    driver = webdriver.Chrome(options=chrome_options)

    # Build the URL using the lot number
    # Build the URL using the lot number
    url = f"https://www.copart.com/lot/{lot_number}"
    driver.get(url)
    time.sleep(15)  # Wait for page to load completely

    lot_info = {}

    try:
        lot_number_element = driver.find_element(By.XPATH, '//*[@id="LotNumber"]')
        lot_info['Lot Number'] = lot_number_element.text
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[2]/div/div/div[1]/div[1]/div[1]/vehicle-information-component/div[2]/div[2]/span')
            lot_info['Lot Number'] = name_element.text
        except NoSuchElementException:
            lot_info['Lot Number'] = "Not Found"
    ################################################
    ################################################
    try:
        name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[1]/div/div/div/div/div/div/h1')
        lot_info['Model'] = name_element.text
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[1]/div/lot-details-header-component/div/div[1]/div/h1')
            lot_info['Model'] = name_element.text
        except NoSuchElementException:
            lot_info['Model'] = "Not Found"
    ################################################
    ################################################
    try:
        meter_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[2]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div/div[2]/div/div[1]/div[5]/div/span/span/span')
        lot_info['Meter'] = meter_element.text
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[2]/div/div/div[1]/div[1]/div[1]/vehicle-information-component/div[2]/div[5]/span')
            lot_info['Meter'] = name_element.text
        except NoSuchElementException:
            lot_info['Meter'] = "Not Found"
    ################################################
    ################################################
    try:
        vin_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[2]/div/div/div[1]/div[1]/div[1]/div[2]/div[1]/div/div[2]/div/div[1]/div[2]/div/div/div/span/span')
        lot_info['VIN'] = vin_element.text
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[2]/div/div/div[1]/div[1]/div[1]/vehicle-information-component/div[2]/div[3]/span')
            lot_info['VIN'] = name_element.text
        except NoSuchElementException:
            lot_info['VIN'] = "Not Found"
    ################################################
    ################################################
    try:
        img_element = driver.find_element(By.XPATH, '//*[@id="media-container-box"]/div[1]/img')
        img_url = img_element.get_attribute("src")
        lot_info['Image URL'] = f"[Click here to view the image]({img_url})"
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[1]/div/lot-details-header-component/div/div[1]/div/h1')
            lot_info['Image URL'] = name_element.text
        except NoSuchElementException:
            lot_info['Image URL'] = "Not Found"   
    ################################################
    ################################################
    try:
        address_element = driver.find_element(By.XPATH, '//*[@id="sale-information-block"]/div[2]/div[2]/span/a')
        lot_info['Address'] = address_element.text
    except NoSuchElementException:
        try:
            name_element = driver.find_element(By.XPATH, '//*[@id="lot-details"]/div/div[1]/div/lot-details-header-component/div/div[1]/div/div/div/div[1]/span[5]/span[2]')
            lot_info['Address'] = name_element.text
        except NoSuchElementException:
            lot_info['Address'] = "Not Found"
    ################################################
    ################################################
    # Check if the address contains "MA"
    if "MA" in lot_info.get('Address', ''):
        lot_info['Price Estimate'] = "$2000"
    else:
        lot_info['Price Estimate'] = "Not Found"

    # Close the browser after processing
    driver.quit()

    return lot_info

# Function to handle each request in a separate thread
def handle_lot_request(message, lot_number):
    user_id = message.chat.id

    current_time = time.time()

    # Check if the user has sent a message in the last cooldown_time seconds
    if user_id in last_message_time and current_time - last_message_time[user_id] < cooldown_time:
        remaining_time = int(cooldown_time - (current_time - last_message_time[user_id]))
        bot.reply_to(message, f"Please wait {remaining_time} seconds before sending another message.")
        return

    # Update the last message time
    last_message_time[user_id] = current_time
    # Acquire semaphore to ensure no more than 3 concurrent threads
    semaphore.acquire()

    try:
        # Send a "waiting" message before scraping starts
        waiting_message = bot.reply_to(message, "Please wait, I'm fetching the information for you...")

        # Scrape the lot data
        lot_info = scrape_lot(lot_number)

        # Format and send the scraped information back to the user
        response = "\n".join([f"{key}: {value}" for key, value in lot_info.items()])
        bot.edit_message_text("Here is the lot information:\n" + response, chat_id=message.chat.id, message_id=waiting_message.message_id, parse_mode='Markdown')

    finally:
        # Release the semaphore to allow another thread to run
        semaphore.release()

# Handle commands from Telegram
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me a lot number in the format '/lot <lot_number>'.")

# Handle /lot command strictly with the format '/lot <lot_number>'
@bot.message_handler(func=lambda message: re.match(r'^/lot \d+$', message.text))
def handle_lot_command(message):
    lot_number = message.text.split()[1]  # Extract the lot number
    handle_lot_request(message, lot_number)

# Reject any message that does not match the /lot <lot_number> format
@bot.message_handler(func=lambda message: not re.match(r'^/lot \d+$', message.text))
def reject_invalid_format(message):
    bot.reply_to(message, "Please use the correct format: '/lot <lot_number>'. Example: '/lot 1234567'.")

# Polling to listen for messages
def run_polling():
    bot.polling()

# Run the polling in a separate thread to allow continuous operation
polling_thread = threading.Thread(target=run_polling)
polling_thread.start()
