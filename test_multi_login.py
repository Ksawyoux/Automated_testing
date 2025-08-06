import os
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from webdriver_manager.chrome import ChromeDriverManager

# -------------------- Logging Setup --------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- Load Credentials --------------------
load_dotenv()
ACCOUNT1_EMAIL = os.getenv("USERNAME_FR")
ACCOUNT1_PASSWORD = os.getenv("PASSWORD")
ACCOUNT2_EMAIL = os.getenv("USERNAME_OSM")
ACCOUNT2_PASSWORD = os.getenv("PASSWORD")
ACCOUNT3_EMAIL = os.getenv("USERNAME_Clt")
ACCOUNT3_PASSWORD = os.getenv("PASSWORD")

# -------------------- WebDriver Setup --------------------
def start_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

# -------------------- Utility --------------------
def find_first_visible(wait: WebDriverWait, locators: list[tuple]) -> webdriver.remote.webelement.WebElement | None:
    """Try multiple locator tuples until one element is present and visible."""
    for by, value in locators:
        try:
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            continue
    return None

# -------------------- Login Logic --------------------
def login_to_kwiks(driver: webdriver.Chrome, email: str, password: str, click_barrier: threading.Barrier) -> None:
    url = "https://preprod.kwiks.io/login"
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    # Step 1: Locate and fill the Email Address field
    email_locators = [
        (By.ID, "email"),
        (By.NAME, "email"),
        (By.CSS_SELECTOR, "input[type='email']"),
        (By.XPATH, "//input[contains(@placeholder, 'Email')]"),
        (By.XPATH, "//input[contains(@placeholder, 'email')]"),
    ]

    email_input = find_first_visible(wait, email_locators)
    if not email_input:
        logging.error(f"{email}: Could not locate Email Address input.")
        return

    email_input.clear()
    email_input.send_keys(email)
    logging.info(f"{email}: Filled Email Address.")

    # Step 2: Locate and fill the Password field
    password_locators = [
        (By.ID, "password"),
        (By.NAME, "password"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.XPATH, "//input[contains(@placeholder, 'Password')]"),
        (By.XPATH, "//input[contains(@placeholder, 'password')]"),
    ]

    password_input = find_first_visible(wait, password_locators)
    if not password_input:
        logging.error(f"{email}: Could not locate Password input.")
        return

    password_input.clear()
    password_input.send_keys(password)
    logging.info(f"{email}: Filled Password.")

    # Step 3: Click the Login button after barrier to keep simultaneous behaviour
    try:
        logging.info(f"{email}: Waiting at barrier before clicking Login.")
        click_barrier.wait(timeout=30)
    except threading.BrokenBarrierError:
        logging.warning(f"{email}: Barrier broken — proceeding without sync.")

    button_locators = [
        (By.XPATH, "//button[@type='submit' and contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'login')]"),
        (By.XPATH, "//button[@type='button' and contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'login')]"),
        (By.XPATH, "//button[contains(@class,'button') and contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'login')]"),
        (By.CSS_SELECTOR, "button[type='submit']"),
    ]

    login_button = find_first_visible(wait, button_locators)
    if login_button:
        try:
            wait.until(EC.element_to_be_clickable(login_button))
            login_button.click()
            logging.info(f"{email}: Clicked Login button.")
        except ElementClickInterceptedException:
            logging.warning(f"{email}: Click intercepted — sending RETURN key.")
            password_input.send_keys(Keys.RETURN)
    else:
        logging.warning(f"{email}: Login button not found — sending RETURN key.")
        password_input.send_keys(Keys.RETURN)

    # Step 5: Wait for login success indicator
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//nav//*[contains(text(), 'Dashboard') or contains(text(), 'Logout')]")))
        logging.info(f"{email}: Logged in successfully.")
    except TimeoutException:
        logging.warning(f"{email}: Login might have failed or confirmation element not found.")

# -------------------- Run Each Session --------------------
def run_session(name: str, email: str, password: str, click_barrier: threading.Barrier, headless: bool = False) -> None:
    driver = start_driver(headless=headless)
    try:
        login_to_kwiks(driver, email, password, click_barrier)

        # -------------------- Post-login actions --------------------
        if name == "Account-1":
            try:
                wait = WebDriverWait(driver, 15)
                mission_element = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[self::a or self::button or self::div][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'mission')]",
                        )
                    )
                )
                mission_element.click()
                logging.info(f"{name}: Clicked 'Mission' successfully.")

                # Wait for an element labeled 'Apply' and click it
                try:
                    apply_element = wait.until(
                        EC.element_to_be_clickable(
                            (
                                By.XPATH,
                                "//*[self::a or self::button or self::div][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'apply')]",
                            )
                        )
                    )
                    # Capture mission name from surrounding card/row before clicking Apply
                    try:
                        mission_card = apply_element.find_element(By.XPATH, "ancestor::*[self::tr or contains(@class,'card') or contains(@class,'chakra') or contains(@class,'Mui')]")
                        mission_name_el = mission_card.find_element(By.XPATH, ".//*[self::h1 or self::h2 or self::h3 or self::span or self::p][normalize-space(text())!='']")
                        global mission_name_selected
                        mission_name_selected = mission_name_el.text.strip()
                        logging.info(f"{name}: Selected mission '{mission_name_selected}'.")
                    except Exception:
                        logging.warning(f"{name}: Could not extract mission name; proceeding anyway.")

                    apply_element.click()
                    logging.info(f"{name}: Clicked 'Apply' successfully.")

                    # Signal other threads mission selected
                    mission_selected_event.set()

                except TimeoutException:
                    logging.error(f"{name}: 'Apply' element not found or not clickable.")
                except ElementClickInterceptedException:
                    logging.error(f"{name}: Click intercepted when trying to click 'Apply'.")

            except TimeoutException:
                logging.error(f"{name}: 'Mission' element not found or not clickable.")
            except ElementClickInterceptedException:
                logging.error(f"{name}: Click intercepted when trying to open 'Mission'.")

        elif name == "Account-2":
            # Wait until Account-1 has selected a mission
            logging.info(f"{name}: Waiting for mission selection by Account-1...")
            if mission_selected_event.wait(timeout=60):
                logging.info(f"{name}: Detected mission '{mission_name_selected}' selected by Account-1. Navigating to assign.")

                try:
                    wait = WebDriverWait(driver, 15)
                    # Ensure Mission page open
                    try:
                        mission_tab = wait.until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH,
                                    "//*[self::a or self::button or self::div][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'mission')]",
                                )
                            )
                        )
                        mission_tab.click()
                        logging.info(f"{name}: Opened 'Mission' page.")
                    except TimeoutException:
                        logging.warning(f"{name}: 'Mission' tab not found; assuming already there.")

                    # Find mission row by name
                    mission_row = wait.until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                f"//*[contains(normalize-space(text()), '{mission_name_selected}')]",
                            )
                        )
                    )

                    # Within same row/card, click 'Assign'
                    try:
                        assign_button = mission_row.find_element(
                            By.XPATH,
                            ".//*[self::a or self::button][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'assign')]",
                        )
                        wait.until(EC.element_to_be_clickable(assign_button))
                        assign_button.click()
                        logging.info(f"{name}: Clicked 'Assign' for mission '{mission_name_selected}'.")
                    except Exception:
                        logging.error(f"{name}: Could not click 'Assign' for mission '{mission_name_selected}'.")
                except TimeoutException:
                    logging.error(f"{name}: Mission '{mission_name_selected}' not found.")
            else:
                logging.error(f"{name}: Timed out waiting for mission selection.")

        # Keep session alive to observe actions
        time.sleep(10)
    finally:
        driver.quit()
        logging.info(f"{name}: Session closed.")

# -------------------- Main Entry --------------------
def main() -> None:
    accounts = [
        ("Account-1", ACCOUNT1_EMAIL, ACCOUNT1_PASSWORD),
        ("Account-2", ACCOUNT2_EMAIL, ACCOUNT2_PASSWORD),
        ("Account-3", ACCOUNT3_EMAIL, ACCOUNT3_PASSWORD),
    ]

    # Remove accounts with missing emails/passwords
    accounts = [(name, email, pwd) for name, email, pwd in accounts if email and pwd]

    if len(accounts) < 3:
        logging.error("Please ensure all three account credentials are set in .env (USERNAME_FR, USERNAME_OSM, USERNAME_3 and corresponding PASSWORD/PASSWORD3).")
        return

    click_barrier = threading.Barrier(len(accounts))

    with ThreadPoolExecutor(max_workers=len(accounts)) as executor:
        for name, email, pwd in accounts:
            executor.submit(run_session, name, email, pwd, click_barrier, headless=False)

# -------------------- Run --------------------
if __name__ == "__main__":
    main()
