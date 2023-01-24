import json
import sys

from explicit import waiter, XPATH
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from datetime import datetime
from pathlib import Path


FOLLOWERS_COUNT_XPATH = "//a/div/span"
FOLLOWERS_CONTAINER_CLASS = "_aano"


def login(driver):
    username = ""  # <username here>
    password = ""  # <password here>

    # Load page
    driver.get("https://www.instagram.com/accounts/login/")

    try_accept_cookies(driver)

    # Login
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    submit = driver.find_element(By.TAG_NAME, 'form')
    submit.submit()

    # Wait for the user dashboard page to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.LINK_TEXT, "Home")))


def try_accept_cookies(driver):
    try:
        sleep(3)
        cookieStatement = driver.find_element(
            By.XPATH, "//button[@class='_a9-- _a9_1']")
        cookieStatement.click()
        sleep(3)
    except Exception as exception:
        print("Could not accept cookies. Exception: {}".format(exception))


def scrape_followers(driver, account):
    # Load account page
    driver.get("https://www.instagram.com/{0}/".format(account))

    # Click the 'Follower(s)' link
    sleep(2)

    followersParentElement = driver.find_element(
        By.PARTIAL_LINK_TEXT, "followers")
    allfoll = int(followersParentElement.find_element(
        By.XPATH, FOLLOWERS_COUNT_XPATH).text)

    print('Followers number for {0}: '.format(account))
    print(allfoll)

    driver.get("https://www.instagram.com/{0}/followers".format(account))

    # Wait for the followers modal to load
    waiter.find_element(driver, "//div[@role='dialog']", by=XPATH, timeout=3)

    sleep(2)

    followers = []
    lastFollower = None
    for follower_index in range(1, allfoll+1):
        follower_xpath = "//div[@class='{0}']/div/div/div[{1}]".format(
                FOLLOWERS_CONTAINER_CLASS, follower_index)
        print("search follower '{0}'".format(follower_xpath))

        followerElement = find_element_with_retries(driver, follower_xpath, retries=4, waitTime=2, lastFollower=lastFollower)
        if(followerElement == None):
            print("Error in finding follower {0}".format(follower_xpath))
            return followers

        lastFollower = followerElement
        follower = get_follower_data_from_driver_element(followerElement)
        followers.append(follower)

        driver.execute_script("arguments[0].scrollIntoView();", lastFollower)

    return followers

def find_element_with_retries(driver, elementXpath, retries, waitTime, lastFollower):
    if (retries == 0):
        return None

    retriesLeft = retries

    while retriesLeft > 0:
        try:
            retriesLeft = retriesLeft - 1
            return driver.find_element(By.XPATH, elementXpath)

        except Exception as exception:
            print("Error: {0}".format(repr(exception)))
            print("Retrying for element: {0}".format(elementXpath))
            sleep(waitTime)
            driver.execute_script("arguments[0].scrollIntoView();", lastFollower)

            if(retriesLeft == 0):
                return None


def get_follower_data_from_driver_element(driverElement):
    imageSrc = driverElement.find_element(
        By.XPATH, ".//div[1]//img").get_attribute("src")
    username = driverElement.find_element(By.XPATH, ".//div[2]//a").text
    print("found user: {0}".format(username))
    return {
        "imageSrc": imageSrc,
        "username": username
    }


if __name__ == "__main__":
    account = sys.argv[1]
    driver = webdriver.Firefox(executable_path="./geckodriver")
    try:
        login(driver)
        followers = scrape_followers(driver, account)
        followers_data_directory_path = "followers/{0}".format(account)
        Path(followers_data_directory_path).mkdir(parents=True, exist_ok=True)
        file_path = "{0}/{1}.json".format(followers_data_directory_path, datetime.now(tz=None))

        with open(file_path, "w") as write:
            json.dump(followers, write)

        print("found '{0} followers".format(len(followers)))
    finally:
        driver.quit()
