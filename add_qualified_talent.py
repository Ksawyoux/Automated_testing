import time
import os
import logging
import random
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
USERNAME_FR = os.getenv("USERNAME_FR")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = "https://preprod.kwiks.io/auth/login"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not USERNAME_FR or not PASSWORD:
    print("[ERROR] USERNAME_FR or PASSWORD environment variable is not set. Please check your .env file.")
    exit(1)

# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("[WARNING] GEMINI_API_KEY not set. Will use fallback name generation.")

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

def generate_random_name():
    """Generate a random first name using Gemini API or fallback."""
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = "Generate a single realistic first name (only the name, no explanation). Make it sound like a real person's name."
            response = model.generate_content(prompt)
            name = response.text.strip()
            # Clean up the response to get just the name
            if name and len(name) < 50:  # Reasonable name length
                log(f"Generated name using Gemini API: {name}")
                return name
        except Exception as e:
            log(f"Gemini API failed: {e}", "WARNING")
    
    # Fallback names if Gemini API fails or is not configured
    fallback_names = [
        "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Quinn", "Avery", 
        "Blake", "Cameron", "Drew", "Emery", "Finley", "Gray", "Harper", "Indigo",
        "Jamie", "Kendall", "Logan", "Mason", "Noah", "Olivia", "Parker", "Quinn",
        "Rowan", "Sage", "Tyler", "Unity", "Vale", "Winter", "Xander", "Yuki", "Zara"
    ]
    fallback_name = random.choice(fallback_names)
    log(f"Using fallback name: {fallback_name}")
    return fallback_name

def find_and_fill_first_name(driver, logger):
    """Find the first name field and fill it with a random name."""
    first_name = generate_random_name()
    first_name_selectors = [
        "//input[@placeholder='First Name']",
        "//input[contains(@placeholder, 'First Name')]",
        "//input[@data-ddg-inputtype='identities.firstName']",
        "//input[contains(@class, 'chakra-input') and contains(@placeholder, 'First Name')]",
        "//input[contains(@placeholder, 'First')]",
        "//input[contains(@placeholder, 'first')]",
        "//input[contains(@id, 'first')]",
        "//input[contains(@name, 'first')]",
        "//label[contains(text(), 'First Name')]/following-sibling::input",
        "//label[contains(text(), 'first')]/following-sibling::input",
        "//label[contains(text(), 'First Name')]/following-sibling::*/input",
        "//label[contains(text(), 'first')]/following-sibling::*/input"
    ]
    
    for selector in first_name_selectors:
        try:
            first_name_field = driver.find_element(By.XPATH, selector)
            if first_name_field.is_displayed():
                if safe_send_keys(driver, first_name_field, first_name):
                    logger.log_step(f"Successfully filled first name field with: {first_name}")
                    return True
                else:
                    logger.log_problem("Failed to fill first name field")
                    return False
        except NoSuchElementException:
            continue
        except Exception as e:
            continue
    
    logger.log_problem("Could not find first name field with any selector")
    return False


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
            log(f"Successfully clicked element on attempt {attempt + 1}")
            element.click()
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
    current_salary_field = None
    desired_salary_field = None
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
    try:
        label = driver.find_element(By.XPATH, f"//p[text()='{dropdown_label}'] | //label[text()='{dropdown_label}']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(0.5)
        combobox_input = driver.find_element(By.XPATH, f"//p[text()='{dropdown_label}']/following-sibling::*//input[@role='combobox'] | //label[text()='{dropdown_label}']/following-sibling::*//input[@role='combobox']")
        combobox_input.click()
        log(f"Clicked {dropdown_label} dropdown")
        time.sleep(1)
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
    log(f"Filling form for step {step_number}")
    current_salary_field, desired_salary_field = find_salary_fields(driver)
    if current_salary_field:
        if safe_send_keys(driver, current_salary_field, "10000"):
            logger.log_step(f"Step {step_number}: Entered current salary")
        else:
            logger.log_problem(f"Step {step_number}: Failed to enter current salary")
    else:
        logger.log_problem(f"Step {step_number}: Could not find current salary field")
    if desired_salary_field:
        if safe_send_keys(driver, desired_salary_field, "12000"):
            logger.log_step(f"Step {step_number}: Entered desired salary")
        else:
            logger.log_problem(f"Step {step_number}: Failed to enter desired salary")
    else:
        logger.log_problem(f"Step {step_number}: Could not find desired salary field")
    if select_dropdown_option(driver, "Business Line", "Information Technology & Software"):
        logger.log_step(f"Step {step_number}: Selected Business Line")
    else:
        logger.log_problem(f"Step {step_number}: Failed to select Business Line")
    if select_dropdown_option(driver, "Contract", "Fixed-Term Contract"):
        logger.log_step(f"Step {step_number}: Selected Contract type")
    else:
        logger.log_problem(f"Step {step_number}: Failed to select Contract type")

def wait_for_next_step(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [class*='load']"))
        )
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)
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
        # Print step information immediately with a running count for real-time visibility
        print(f"[STEP {len(self.steps)}] {description}")
    def log_problem(self, description):
        self.problems.append(description)
        # Print problems immediately so they are visible while the automation runs
        print(f"[PROBLEM] {description}")
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
        print("Launching Chrome and navigating to login page...")
        logger.log_step("Launched Chrome and navigated to login page")
        driver.get(LOGIN_URL)

        wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input = driver.find_element(By.ID, "email")
        password_input = driver.find_element(By.ID, "password")

        safe_send_keys(driver, email_input, USERNAME_FR)
        safe_send_keys(driver, password_input, PASSWORD)
        password_input.send_keys(Keys.RETURN)
        logger.log_step("Logged in successfully")

        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Add qualified talents')]")))
        add_talent_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Add qualified talents')]")
        if safe_click(driver, add_talent_button):
            logger.log_step("Clicked 'Add qualified talents'")
        else:
            logger.log_problem("'Add qualified talents' button did not work or did not get to next step!")

        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Browse Files')]")))
        browse_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Browse Files')]")
        if safe_click(driver, browse_button):
            logger.log_step("Clicked 'Browse Files' button.")
            try:
                wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".MuiLinearProgress-root, .progress-bar, .uploading")))
                logger.log_step("Waited for file upload to complete (progress bar disappeared).")
            except Exception:
                time.sleep(2)
                logger.log_step("Waited 2 seconds after file upload (no progress bar detected).")
        else:
            logger.log_problem("Failed to click 'Browse Files' button.")

        logger.log_step("Waiting 30 seconds before clicking 'Next Step' after uploading CV.")
        time.sleep(30)

        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
        next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
        if safe_click(driver, next_button):
            logger.log_step("Clicked first Next Step after upload")
        else:
            logger.log_problem("First 'Next Step' button did not work or did not get to next step!")

        # Wait for the page to load after first Next Step
        time.sleep(15)
        wait_for_next_step(driver)
        
        # Look for and fill first name field
        logger.log_step("Looking for first name field after first Next Step")
        find_and_fill_first_name(driver, logger)

        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
            next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
            if safe_click(driver, next_button):
                logger.log_step("Clicked second Next Step before filling form fields")
            else:
                logger.log_problem("Second 'Next Step' button did not work or did not get to next step!")
        except Exception as e:
            logger.log_problem(f"Failed to click second Next Step before filling form fields: {e}")

        time.sleep(4)
        wait_for_next_step(driver)
        fill_form_step(driver, logger, wait, 1)

        for step in range(1, 8):
            try:
                # Fill note field only on step 6 (where it appears)
                if step == 6:
                    logger.log_step(f"Step {step}: Looking for Head Hunter's Note field")
                    note_field = None
                    possible_selectors = [
                        "//textarea",
                    ]
                    
                    for i, selector in enumerate(possible_selectors):
                        try:
                            logger.log_step(f"Step {step}: Trying selector {i+1}: {selector}")
                            note_field = WebDriverWait(driver, 5).until(
                                EC.visibility_of_element_located((By.XPATH, selector))
                            )
                            if note_field and note_field.is_displayed():
                                logger.log_step(f"Step {step}: Found textarea with selector {i+1}")
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", note_field)
                                time.sleep(1)
                                break
                        except Exception as e:
                            logger.log_problem(f"Step {step}: Selector {i+1} failed: {e}")
                            continue
                    
                    if note_field:
                        note_text = "a business analyst and good AI knowledgeable in general, a perfect candidate"
                        logger.log_step(f"Step {step}: Attempting to fill note field with: {note_text}")
                        if safe_send_keys(driver, note_field, note_text):
                            logger.log_step(f"Step {step}: Successfully filled 'Head Hunter's Note' field with candidate description.")
                        else:
                            logger.log_problem(f"Step {step}: Failed to fill 'Head Hunter's Note' field!")
                    else:
                        logger.log_problem(f"Step {step}: Could not find any textarea field for Head Hunter's Note!")
                if step == 7:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save Talent')]")))
                    save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Save Talent')]")
                    if safe_click(driver, save_button):
                        logger.log_step("Clicked Save Talent (final step)")
                    else:
                        logger.log_problem("'Save Talent' button did not work or did not get to next step!")
                else:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Step')]")))
                    next_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Next Step')]")
                    if safe_click(driver, next_button):
                        logger.log_step(f"Clicked Next Step {step}")
                    else:
                        logger.log_problem(f"Next Step {step} button did not work or did not get to next step!")
                if step < 7:
                    if step == 1 or step == 2:  # First and Second Next Steps
                        time.sleep(15)
                    elif step == 3:  # Third Next Step
                        time.sleep(15)
                    else:  # Steps 4, 5, 6
                        time.sleep(4)
            except Exception as e:
                logger.log_problem(f"Step {step}: Exception - {e}")
                break

        logger.log_step("Automation completed successfully")
    except Exception as e:
        log(f"Automation failed: {e}", "ERROR")
        logger.log_problem(f"Automation failed: {e}")
    finally:
        logger.save()
        input("\nPress Enter to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main()