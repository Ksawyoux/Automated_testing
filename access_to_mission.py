import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from dotenv import load_dotenv
import time

load_dotenv()

def create_driver():
    """Create and configure Chrome driver."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def login_with_selenium(username: str, password: str):
    """Login to the Kwiks platform."""
    driver = create_driver()
    
    try:
        driver.get("https://preprod.kwiks.io/login")
        wait = WebDriverWait(driver, 10)
        
        # Find and fill email
        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name*='email' i]"),
            (By.ID, "email"),
            (By.NAME, "email"),
        ]
        
        email_elem = None
        for by, value in email_selectors:
            try:
                email_elem = wait.until(EC.presence_of_element_located((by, value)))
                email_elem.clear()
                email_elem.send_keys(username)
                break
            except TimeoutException:
                continue
        
        if not email_elem:
            raise Exception("Could not find email field")
        
        # Find and fill password
        password_selectors = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.ID, "password"),
            (By.NAME, "password"),
        ]
        
        password_elem = None
        for by, value in password_selectors:
            try:
                password_elem = wait.until(EC.presence_of_element_located((by, value)))
                password_elem.clear()
                password_elem.send_keys(password)
                break
            except TimeoutException:
                continue
        
        if not password_elem:
            raise Exception("Could not find password field")
        
        # Find and click login button
        login_button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login') or contains(text(), 'Sign in')]"),
            (By.CSS_SELECTOR, "button"),
        ]
        
        login_clicked = False
        for by, value in login_button_selectors:
            try:
                login_button = wait.until(EC.element_to_be_clickable((by, value)))
                login_button.click()
                login_clicked = True
                break
            except TimeoutException:
                continue
        
        if not login_clicked:
            # Fallback: press Enter on password field
            password_elem.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        time.sleep(3)
        return driver
        
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        raise

def go_to_first_mission(driver):
    """Navigate to the first mission after login."""
    wait = WebDriverWait(driver, 10)
    
    try:
        # Find the <p> with text "My Missions"
        p_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//p[text()='My Missions']")))
        parent_div = p_elem.find_element(By.XPATH, "./..")
        driver.execute_script("arguments[0].scrollIntoView();", parent_div)
        parent_div.click()
        print("Clicked 'My Missions' tab via parent div.")
        
        # Wait for the missions page to load
        time.sleep(2)
        
    except Exception as e:
        print(f"Could not find or click the 'My Missions' tab: {e}")
        # Don't raise here, maybe we're already on the right page
    
    # Try several selectors for the first mission row
    mission_selectors = [
        (By.XPATH, "//table//tbody//tr[1]"),  
        (By.XPATH, "//table//tr[not(th)][1]"),  
        (By.CSS_SELECTOR, "tbody tr:first-child"),
        (By.CSS_SELECTOR, "table tr:not(:first-child)"),  
        (By.CSS_SELECTOR, "tr[role='row']:not([class*='header'])"),
        (By.CSS_SELECTOR, "div.mission-card"),
        (By.CSS_SELECTOR, ".mission-list-item"),
        (By.CSS_SELECTOR, ".mission-row"),
        (By.CSS_SELECTOR, "a[href*='mission']"),
        (By.XPATH, "(//div[contains(@class, 'mission') or contains(@class, 'row')])[1]"),
        (By.XPATH, "(//a[contains(@href, 'mission')])[1]"),
    ]
    
    mission_elem = None
    for by, value in mission_selectors:
        try:
            mission_elem = wait.until(EC.element_to_be_clickable((by, value)))
            print(f"Found first mission with selector: {by}={value}")
            driver.execute_script("arguments[0].scrollIntoView();", mission_elem)
            time.sleep(0.5)  # Small delay after scrolling
            mission_elem.click()
            return driver
        except TimeoutException:
            continue
    
    if not mission_elem:
        print("Could not find the first mission element. Available table structure:")
        try:
            # Better debugging - show table structure
            table = driver.find_element(By.XPATH, "//table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            print(f"Found {len(rows)} table rows:")
            for i, row in enumerate(rows[:3]):  # Show first 3 rows
                cells = row.find_elements(By.TAG_NAME, "td")
                if cells:
                    print(f"Row {i}: {len(cells)} cells - {cells[0].text if cells else 'No text'}")
        except Exception as debug_e:
            print(f"Error during debugging: {debug_e}")
        
        raise Exception("Could not find the first mission element. Please check the selector.")
    
    return driver



def main():
    """Main function to run the automation."""
    username = os.getenv("KWIKS_USERNAME")
    password = os.getenv("KWIKS_PASSWORD")
    
    if not username or not password:
        raise Exception("Please set KWIKS_USERNAME and KWIKS_PASSWORD environment variables.")
    
    driver = None
    try:
        driver = login_with_selenium(username, password)
        go_to_first_mission(driver)
        input("Press Enter to close the browser...")
    except Exception as e:
        print(f"Script failed: {e}")
    finally:
        if driver:
            driver.quit()
