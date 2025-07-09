import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv
import time

load_dotenv()

def login_with_selenium(username: str, password: str):
    options = Options()
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://preprod.kwiks.io/login")
        wait = WebDriverWait(driver, 1)  # Increased wait time
        # Try several selectors for the email field
        email_selectors = [
            (By.NAME, "Email Address"),
            (By.NAME, "Email"),
            (By.NAME, "email"),
            (By.ID, "email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
        ]
        email_elem = None
        for by, value in email_selectors:
            try:
                email_elem = wait.until(EC.presence_of_element_located((by, value)))
                print(f"Found email field with selector: {by}={value}")
                email_elem.clear()
                email_elem.send_keys(username)
                break
            except TimeoutException:
                continue
        if not email_elem:
            raise Exception("Could not find the email input field. Please check the selector.")

        # Try several selectors for the password field
        password_selectors = [
            (By.NAME, "Password"),
            (By.NAME, "password"),
            (By.ID, "password"),
            (By.ID, "Password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
        ]
        password_elem = None
        for by, value in password_selectors:
            try:
                password_elem = wait.until(EC.presence_of_element_located((by, value)))
                print(f"Found password field with selector: {by}={value}")
                password_elem.clear()
                password_elem.send_keys(password)
                break
            except TimeoutException:
                continue
        if not password_elem:
            raise Exception("Could not find the password input field. Please check the selector.")

        # Try multiple selectors for the login button
        login_button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.CSS_SELECTOR, "button[type='Login']"),
            (By.XPATH, "//button[contains(text(), 'Login')]") ,
            (By.XPATH, "//button[contains(text(), 'Sign in')]") ,
            (By.XPATH, "//button[contains(text(), 'Sign In')]") ,
            (By.XPATH, "//input[@value='Login']"),
            (By.CSS_SELECTOR, "button"),
            (By.CSS_SELECTOR, ".login-button"),
            (By.CSS_SELECTOR, "#login-button"),
            (By.CSS_SELECTOR, ".btn-primary"),
            (By.CSS_SELECTOR, ".submit-btn"),
        ]
        login_button = None
        for by, value in login_button_selectors:
            try:
                login_button = wait.until(EC.element_to_be_clickable((by, value)))
                print(f"Found login button with selector: {by}={value}")
                driver.execute_script("arguments[0].scrollIntoView();", login_button)
                time.sleep(0.5)  # Small delay to ensure scrolling is complete
                login_button.click()
                break
            except TimeoutException:
                continue
        if not login_button:
            print("Could not find login button with standard selectors. Trying alternative approach...")
            # Alternative: Try pressing Enter on password field
            try:
                password_elem.send_keys(Keys.RETURN)
                print("Pressed Enter on password field as alternative to clicking login button")
            except Exception as e:
                print(f"Alternative approach failed: {e}")
                raise Exception("Could not find or click the login button. Please check the page structure.")
        # Wait a moment for the login to process
        time.sleep(2)
        return driver
    except Exception as e:
        print(f"An error occurred: {e}")
        driver.quit()
        raise

if __name__ == "__main__":
    username = os.getenv("USERNAME") or "your_username"
    password = os.getenv("PASSWORD") or "your_password"
    
    try:
        driver = login_with_selenium(username, password)
        input("Press Enter to close the browser...")
        driver.quit()
    except Exception as e:
        print(f"Login failed: {e}")