import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv
import os
import json

# --- CONFIGURATION ---
load_dotenv()
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = "https://preprod.kwiks.io/login"
CV_FILE_PATH = os.getenv("CV_FILE_PATH", "/path/to/your/cv.pdf")  # Add this to your .env

if not USERNAME or not PASSWORD:
    print("[ERROR] USERNAME or PASSWORD environment variable is not set. Please check your .env file.")
    exit(1)

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log(msg, level="INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if level == "ERROR":
        logger.error(f"[{timestamp}] {msg}")
    elif level == "WARNING":
        logger.warning(f"[{timestamp}] {msg}")
    else:
        logger.info(f"[{timestamp}] {msg}")

def safe_click(driver, element, max_retries=3):
    for attempt in range(max_retries):
        try:
            if not element.is_displayed():
                log(f"Element not displayed on attempt {attempt + 1}", "WARNING")
                time.sleep(0.5)
                continue
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
            element.click()
            log(f"Successfully clicked element on attempt {attempt + 1}")
            return True
        except ElementClickInterceptedException:
            log(f"Click intercepted, trying ActionChains (attempt {attempt + 1})", "WARNING")
            try:
                ActionChains(driver).move_to_element(element).click().perform()
                log("Clicked element with ActionChains")
                return True
            except Exception:
                log("ActionChains click failed, trying JS click", "WARNING")
                try:
                    driver.execute_script("arguments[0].click();", element)
                    log("Clicked element with JavaScript")
                    return True
                except Exception as js_error:
                    log(f"JavaScript click failed: {js_error}", "ERROR")
        except Exception as e:
            log(f"Click attempt {attempt + 1} failed: {e}", "WARNING")
            if attempt < max_retries - 1:
                time.sleep(1)
    log("All click attempts failed", "ERROR")
    return False

def safe_send_keys(driver, element, text, clear_first=True):
    try:
        if not element.is_displayed():
            log("Element not visible for text input", "WARNING")
            return False
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
        time.sleep(0.2)
        if clear_first:
            element.clear()
            time.sleep(0.1)
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            time.sleep(0.1)
        for char in text:
            element.send_keys(char)
            time.sleep(0.02)
        log(f"Successfully sent keys: {text}")
        return True
    except Exception as e:
        log(f"Failed to send keys '{text}': {e}", "ERROR")
        return False



def find_salary_fields(driver):
    """Find salary fields using more robust selectors"""
    current_salary_field = None
    desired_salary_field = None
    
    # Try multiple selectors for current salary
    current_selectors = [
        "//input[contains(@placeholder, 'Current') and contains(@placeholder, 'salary')]",
        "//input[contains(@id, 'current')]",
        "//label[contains(text(), 'Current')]/following-sibling::input",
        "//label[contains(text(), 'Current')]/following-sibling::*/input"
    ]
    
    for selector in current_selectors:
        try:
            current_salary_field = driver.find_element(By.XPATH, selector)
            log(f"Found current salary field")
            break
        except NoSuchElementException:
            continue
    
    # Try multiple selectors for desired salary
    desired_selectors = [
        "//input[contains(@placeholder, 'Desired') and contains(@placeholder, 'salary')]",
        "//input[contains(@id, 'desired')]",
        "//label[contains(text(), 'Desired')]/following-sibling::input",
        "//label[contains(text(), 'Desired')]/following-sibling::*/input"
    ]
    
    for selector in desired_selectors:
        try:
            desired_salary_field = driver.find_element(By.XPATH, selector)
            log(f"Found desired salary field")
            break
        except NoSuchElementException:
            continue
    
    return current_salary_field, desired_salary_field

def select_dropdown_option(driver, dropdown_label, option_text):
    """Select an option from a dropdown with better error handling"""
    try:
        # Find the dropdown by label
        label = driver.find_element(By.XPATH, f"//p[text()='{dropdown_label}'] | //label[text()='{dropdown_label}']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(0.5)
        
        # Find the combobox input near the label
        combobox_input = driver.find_element(By.XPATH, f"//p[text()='{dropdown_label}']/following-sibling::*//input[@role='combobox'] | //label[text()='{dropdown_label}']/following-sibling::*//input[@role='combobox']")
        
        # Click to open dropdown
        combobox_input.click()
        log(f"Clicked {dropdown_label} dropdown")
        time.sleep(1)
        
        # Select the option
        option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//div[@role='option' and text()='{option_text}']"))
        )
        option.click()
        log(f"Selected '{option_text}' for '{dropdown_label}'")
        return True
        
    except Exception as e:
        log(f"Failed to select '{option_text}' for '{dropdown_label}': {e}", "ERROR")
        return False

def fill_form_step(driver, logger, wait, step_number):
    """Fill form fields for a specific step"""
    log(f"Filling form for step {step_number}")
    
    # Fill salary fields
    current_salary_field, desired_salary_field = find_salary_fields(driver)
    
    if current_salary_field:
        if safe_send_keys(driver, current_salary_field, "10000"):
            logger.log_step(f"Step {step_number}: Entered current salary")
        else:
            logger.log_problem(f"Step {step_number}: Failed to enter current salary")
    
    if desired_salary_field:
        if safe_send_keys(driver, desired_salary_field, "12000"):
            logger.log_step(f"Step {step_number}: Entered desired salary")
        else:
            logger.log_problem(f"Step {step_number}: Failed to enter desired salary")
    
    # Select Business Line
    if select_dropdown_option(driver, "Business Line", "Information Technology & Software"):
        logger.log_step(f"Step {step_number}: Selected Business Line")
    else:
        logger.log_problem(f"Step {step_number}: Failed to select Business Line")
    
    # Select Contract
    if select_dropdown_option(driver, "Contract", "Fixed-Term Contract"):
        logger.log_step(f"Step {step_number}: Selected Contract type")
    else:
        logger.log_problem(f"Step {step_number}: Failed to select Contract type")

def wait_for_next_step(driver, timeout=30):
    """Wait for the next step to load"""
    try:
        # Wait for any loading indicators to disappear
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [class*='load']"))
        )
        
        # Wait for page to be ready
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        time.sleep(2)  # Small buffer
        return True
    except TimeoutException:
        log("Timeout waiting for next step", "WARNING")
        return False

class AutomationLogger:
    def __init__(self, log_path="automation_log.md"):
        self.log_path = log_path
        self.steps = []
        self.problems = []
    
    def log_step(self, description):
        self.steps.append(description)
        
    def log_problem(self, description):
        self.problems.append(description)
        
    def save(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write("# Automation Log\n\n")
            f.write("## Steps Taken\n")
            for i, step in enumerate(self.steps, 1):
                f.write(f"{i}. {step}\n")
            f.write("\n## Problems Encountered\n")
            if self.problems:
                for p in self.problems:
                    f.write(f"- {p}\n")
            else:
                f.write("- No problems encountered.\n")

def main():
    logger = AutomationLogger()
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)
    
    try:
        # Login
        logger.log_step("Launched Chrome and navigated to login page")
        driver.get(LOGIN_URL)
        
        # Wait for login form
        wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")
        
        # Enter credentials
        safe_send_keys(driver, email_input, USERNAME)
        safe_send_keys(driver, password_input, PASSWORD)
        password_input.send_keys(Keys.RETURN)
        logger.log_step("Logged in successfully")
        
        # Click Add Talent
        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Add qualified talents')]")))
        add_talent_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Add qualified talents')]")
        safe_click(driver, add_talent_button)
        logger.log_step("Clicked 'Add qualified talents'")
        
        # Handle file upload
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Browse Files')]")))
        browse_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Browse Files')]")
        if safe_click(driver, browse_button):
            log("Clicked 'Browse Files' button!")
            logger.log_step("Clicked 'Browse Files' button.")
            try:
                wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiLinearProgress-root, .progress-bar, .uploading")))
                logger.log_step("Waited for file upload to complete (progress bar disappeared).")
            except Exception:
                time.sleep(2)
                logger.log_step("Waited 2 seconds after file upload (no progress bar detected).")
        else:
            logger.log_problem("Failed to click 'Browse Files' button.")
        
        # Wait 40 seconds before clicking first Next Step
        log("Waiting 40 seconds before clicking 'Next Step'...", "INFO")
        logger.log_step("Waiting 40 seconds before clicking 'Next Step' after uploading CV.")
        time.sleep(40)
        
        # First Next Step (after upload)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
        next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
        safe_click(driver, next_button)
        logger.log_step("Clicked first Next Step after upload")

        # Click Next Step again before filling form fields
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
            next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
            safe_click(driver, next_button)
            logger.log_step("Clicked second Next Step before filling form fields")
        except Exception as e:
            logger.log_problem(f"Failed to click second Next Step before filling form fields: {e}")

        # Wait 1 minute before filling form fields
        log("Waiting 1 minute before filling form fields...", "INFO")
        time.sleep(60)
        
        wait_for_next_step(driver)
        fill_form_step(driver, logger, wait, 1)
        
        # Click Next Step multiple times (7 times total)
        for step in range(1, 7):
            try:
                if step == 6:  # Last step - click "Save Talent"
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save Talent')]")))
                    save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Save Talent')]")
                    safe_click(driver, save_button)
                    logger.log_step(f"Clicked Save Talent (final step)")
                else:  # Regular Next Step clicks
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
                    safe_click(driver, next_button)
                    logger.log_step(f"Clicked Next Step {step}")
                
                # Wait 30 seconds before next click (except for the last one)
                if step < 6:
                    log("Waiting 30 seconds before next click...", "INFO")
                    time.sleep(30)
                    
            except Exception as e:
                if step == 6:
                    logger.log_problem(f"Failed to click Save Talent: {e}")
                else:
                    logger.log_problem(f"Failed to click Next Step {step}: {e}")
                break
        
        logger.log_step("Automation completed successfully")
        
    except Exception as e:
        log(f"Automation failed: {e}", "ERROR")
        logger.log_problem(f"Automation failed: {e}")
    
    finally:
        input("\nPress Enter to close the browser...")
        driver.quit()
        print("✅ Automation completed")

if __name__ == "__main__":
    main()