import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

load_dotenv()

USERNAME_Clt = os.getenv("USERNAME_Clt")
PASSWORD = os.getenv("PASSWORD")
LOGIN_URL = "https://preprod.kwiks.io/login"

if not USERNAME_Clt or not PASSWORD:
    print("[ERROR] USERNAME_Clt or PASSWORD environment variable is not set. Please check your .env file.")
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

def login(driver):
    """Perform login operation with robust locator fall-backs"""
    try:
        log("Starting login process")
        driver.get(LOGIN_URL)

        # Give the page a second to start rendering
        time.sleep(1)

        # Possible selectors for the email input
        email_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.NAME, "Email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
        ]
        email_elem = None
        for by, value in email_selectors:
            try:
                email_elem = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((by, value))
                )
                log(f"Found email field with selector: {by}={value}")
                email_elem.clear()
                email_elem.send_keys(USERNAME_Clt)
                break
            except TimeoutException:
                continue
        if not email_elem:
            log("Could not find the email input field", "ERROR")
            return False

        # Possible selectors for the password input
        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.NAME, "Password"),
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[placeholder*='Password']"),
        ]
        password_elem = None
        for by, value in password_selectors:
            try:
                password_elem = WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located((by, value))
                )
                log(f"Found password field with selector: {by}={value}")
                password_elem.clear()
                password_elem.send_keys(PASSWORD)
                break
            except TimeoutException:
                continue
        if not password_elem:
            log("Could not find the password input field", "ERROR")
            return False

        # Possible selectors for the login/submit button
        login_button_selectors = [
            (By.CSS_SELECTOR, "button[type='submit']"),
            (By.CSS_SELECTOR, "input[type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'Sign in') or contains(text(), 'Sign In')]")
        ]
        login_button = None
        for by, value in login_button_selectors:
            try:
                login_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((by, value))
                )
                log(f"Found login button with selector: {by}={value}")
                break
            except TimeoutException:
                continue

        # Fallback – press ENTER on password field if button not found
        if login_button:
            if safe_click(driver, login_button):
                log("Login button clicked")
            else:
                log("Failed to click login button", "ERROR")
                return False
        else:
            log("Login button not found, attempting ENTER key on password field")
            password_elem.send_keys(Keys.RETURN)

        # Wait a moment for navigation to happen
        WebDriverWait(driver, 10).until(lambda d: d.current_url != LOGIN_URL)
        log("Login successful (URL changed)")
        return True

    except Exception as e:
        log(f"Login failed: {e}", "ERROR")
        return False

def click_add_new_mission(driver, timeout=15):
    """Click on 'Add New Mission' button after successful login"""
    try:
        log("Looking for 'Add New Mission' button")
        
        # Wait for page to load after login
        time.sleep(2)
        
        # Common selectors for "Add New Mission" button - try multiple approaches
        selectors = [
            "//p[contains(text(), 'Add New Mission')]",  # Added <p> tag selector
            "//p[contains(text(), 'Add New Mission')]/ancestor::*[self::button or @role='button'][1]",  # Clickable ancestor of <p>
            "//*[contains(@class, 'add-mission') or contains(@id, 'add-mission')]",
            "//button[contains(@aria-label, 'Add New Mission')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add new mission')]"
        ]
        
        for selector in selectors:
            try:
                log(f"Trying selector: {selector}")
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                
                if safe_click(driver, element):
                    log("Successfully clicked 'Add New Mission' button")
                    return True
                    
            except TimeoutException:
                log(f"Selector '{selector}' not found or not clickable", "WARNING")
                continue
            except Exception as e:
                log(f"Error with selector '{selector}': {e}", "WARNING")
                continue
        
        # If none of the common selectors work, try to find by partial text match
        try:
            log("Trying to find button by partial text match")
            all_clickable_elements = driver.find_elements(By.XPATH, "//button | //a | //div[@role='button'] | //p")
            
            for element in all_clickable_elements:
                try:
                    element_text = element.text.lower()
                    if "add" in element_text and "mission" in element_text:
                        log(f"Found potential 'Add New Mission' element with text: '{element.text}'")
                        if safe_click(driver, element):
                            log("Successfully clicked 'Add New Mission' button via text search")
                            return True
                except Exception:
                    continue
                    
        except Exception as e:
            log(f"Error during text-based search: {e}", "WARNING")
        
        log("Could not find 'Add New Mission' button", "ERROR")
        return False
        
    except Exception as e:
        log(f"Failed to click 'Add New Mission': {e}", "ERROR")
        return False

def safe_send_keys(driver, element, text, clear_first=True):
    """Safely send text to an input/textarea, scrolling into view and optionally clearing first"""
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
        for ch in text:
            element.send_keys(ch)
            time.sleep(0.01)
        log(f"Successfully sent keys (first 30 chars): {text[:30]}")
        return True
    except Exception as e:
        log(f"Failed to send keys: {e}", "ERROR")
        return False

def fill_job_title_and_generate_description(driver, job_title="QA Engineer", timeout=15):
    """Fill the Job Title field and click the Generate Description button"""
    try:
        log("Looking for Job Title input field")
        # Wait for the input to appear
        input_selectors = [
            "//input[@placeholder='Job Title']",
            "//input[contains(@placeholder, 'Job Title')]",
            "//label[contains(text(), 'Job Title')]/following-sibling::input",
            "//label[contains(text(), 'Job Title')]/following::*[self::input or @role='textbox'][1]"
        ]
        title_input = None
        for selector in input_selectors:
            try:
                log(f"Trying Job Title selector: {selector}")
                title_input = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, selector))
                )
                break
            except TimeoutException:
                continue
        if not title_input:
            log("Could not find the Job Title input field", "ERROR")
            return False

        # Scroll into view and type
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", title_input)
        time.sleep(0.3)
        title_input.clear()
        title_input.send_keys(job_title)
        log(f"Entered job title: {job_title}")

        # Locate Generate Description button
        log("Looking for 'Generate Description' button")
        button_selectors = [
            "//button[contains(text(), 'Generate Description')]",
            "//button[@type='button' and contains(., 'Generate Description')]",
            "//span[contains(text(), 'Generate Description')]/ancestor::button"
        ]
        gen_button = None
        for selector in button_selectors:
            try:
                log(f"Trying Generate Description selector: {selector}")
                gen_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except TimeoutException:
                continue
        if not gen_button:
            log("Could not find Generate Description button", "ERROR")
            return False

        if safe_click(driver, gen_button):
            log("Clicked 'Generate Description' button")
            # After clicking Generate Description, fill in the description field and press the final Generate button
            desc_text = (
                "We’re seeking a motivated Junior QA Engineer to help us validate software functionality "
                "and ensure optimal user experience. This role is perfect for someone starting out in tech "
                "and interested in quality assurance.\n\nResponsibilities:\nExecute test plans and report bugs"
            )

            # Locate the description textarea
            textarea_selectors = [
                "//textarea[@placeholder='short description..']",  # explicit placeholder
                "//textarea[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'description')]",  # any description placeholder
                "//textarea",
            ]
            description_elem = None
            for selector in textarea_selectors:
                try:
                    log(f"Trying description textarea selector: {selector}")
                    description_elem = WebDriverWait(driver, timeout).until(
                        EC.visibility_of_element_located((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not description_elem:
                log("Could not find description textarea", "ERROR")
                return False

            if not safe_send_keys(driver, description_elem, desc_text):
                log("Failed to enter description text", "ERROR")
                return False

            log("Description text entered; searching for final 'Generate' button")

            final_generate_selectors = [
                "//button[contains(text(), 'Generate') and not(contains(text(), 'Description'))]",
                "//button[@type='button' and contains(., 'Generate') and not(contains(., 'Description'))]",
                "//span[contains(text(), 'Generate')]/ancestor::button[1]",
            ]

            final_generate_button = None
            for selector in final_generate_selectors:
                try:
                    log(f"Trying final Generate selector: {selector}")
                    final_generate_button = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not final_generate_button:
                log("Could not find final Generate button", "ERROR")
                return False

            if safe_click(driver, final_generate_button):
                log("Clicked final 'Generate' button")
                # Wait 10 seconds before proceeding to the Next Step
                time.sleep(10)

                # After generation, proceed by clicking 'Next Step'
                next_step_selectors = [
                    "//button[contains(text(), 'Next Step')]",
                    "//span[contains(text(), 'Next Step')]/ancestor::button[1]"
                ]
                next_button = None
                for selector in next_step_selectors:
                    try:
                        log(f"Trying Next Step selector: {selector}")
                        next_button = WebDriverWait(driver, timeout).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except TimeoutException:
                        continue

                if next_button and safe_click(driver, next_button):
                    log("Clicked 'Next Step' button, waiting 5 seconds before next actions")
                    time.sleep(3)
                    return True
                else:
                    log("Failed to click 'Next Step' button", "ERROR")
                    return False
            else:
                log("Failed to click final Generate button", "ERROR")
                return False
        else:
            log("Failed to click 'Generate Description' button", "ERROR")
            return False

    except Exception as e:
        log(f"Error in fill_job_title_and_generate_description: {e}", "ERROR")
        return False

def select_dropdown_option(driver, dropdown_label, option_text, timeout=15):
    """Open a react-select style combobox by label text and choose option_text."""
    try:
        label = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//p[text()='{dropdown_label}'] | //label[text()='{dropdown_label}']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
        time.sleep(0.3)
        combobox_input = label.find_element(By.XPATH, "following::*//input[@role='combobox']")
        combobox_input.click()
        time.sleep(0.3)
        combobox_input.send_keys(option_text)

        # Build XPath for option, choosing quote type that doesn't conflict with the value
        if "'" in option_text and '"' not in option_text:
            option_xpath = f'//div[@role="option" and normalize-space()="{option_text}"]'
        else:
            option_xpath = f"//div[@role='option' and normalize-space()='{option_text}']"

        # Wait for option to appear and click it safely
        option = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, option_xpath))
        )
        if not safe_click(driver, option):
            log(f"Safe click failed for option {option_text}", "ERROR")
            return False
        log(f"Selected '{option_text}' for '{dropdown_label}'")
        return True
    except Exception as e:
        log(f"Failed to select '{option_text}' for '{dropdown_label}': {e}", "ERROR")
        return False


def set_work_model_and_location(driver, work_model="On-Site", country="Morocco", city="Casablanca", timeout=15):
    """Set Work Model radio and choose Country & City in the next step"""
    try:
        # Wait briefly for new step
        time.sleep(2)
        log("Selecting Work Model")
        work_model_selectors = [
            f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{work_model.lower()}')]/ancestor::*[self::label or self::div or self::button][1]",
            f"//*[contains(text(), '{work_model}')]/preceding::span[@class='chakra-radio__control'][1]",
        ]
        work_elem = None
        for selector in work_model_selectors:
            try:
                log(f"Trying Work Model selector: {selector}")
                work_elem = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if safe_click(driver, work_elem):
                    log(f"Selected Work Model: {work_model}")
                    break
            except TimeoutException:
                continue
        if not work_elem:
            log("Could not find Work Model option", "ERROR")
            return False

        # Select Country
        if not select_dropdown_option(driver, "Country", country, timeout):
            return False
        # Select City
        if not select_dropdown_option(driver, "City", city, timeout):
            return False

        log("Work model and location filled, clicking 'Next Step'")

        # Click Next Step and wait 5 seconds
        next_step_selectors = [
            "//button[contains(text(), 'Next Step')]",
            "//span[contains(text(), 'Next Step')]/ancestor::button[1]"
        ]
        next_button = None
        for selector in next_step_selectors:
            try:
                log(f"Trying Next Step selector: {selector}")
                next_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except TimeoutException:
                continue

        if next_button and safe_click(driver, next_button):
            log("Clicked 'Next Step' button after location, waiting 5 seconds")
            time.sleep(5)
            return True
        else:
            log("Failed to click 'Next Step' button after location", "ERROR")
            return False

    except Exception as e:
        log(f"Error in set_work_model_and_location: {e}", "ERROR")
        return False

def set_business_details(driver, timeout=15):
    """Fill Business Line, Skills, Education, Salary, Contract, click Add and Next Step"""
    try:
        time.sleep(2)
        # Business Line
        if not select_dropdown_option(driver, "Business Line", "Information Technology & Software", timeout):
            return False
        time.sleep(1)
        # Skills
        if not select_dropdown_option(driver, "Skills", "IT", timeout):
            return False
        time.sleep(1)
        # Education
        if not select_dropdown_option(driver, "Education Level", "Bachelor's Degree (e.g., BA, BSc, BEng)", timeout):
            return False
        time.sleep(1)
        # Salary – try to locate a single salary input
        salary_selectors = [
            "//input[contains(@placeholder, 'Salary')]",
        ]
        salary_elem = None
        for sel in salary_selectors:
            try:
                log(f"Trying Salary selector: {sel}")
                salary_elem = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((By.XPATH, sel))
                )
                break
            except TimeoutException:
                continue
        if not salary_elem:
            log("Could not find Salary input", "ERROR")
            return False
        if not safe_send_keys(driver, salary_elem, "10000 dh"):
            return False
        # Contract
        if not select_dropdown_option(driver, "Contract", "Fixed-Term Contract", timeout):
            return False
        # Click Add button
        add_selectors = [
            "//button[contains(normalize-space(), 'Add') and not(contains(., 'Add New'))]",
            "//button[.//svg and contains(., 'Add')]",
            "//span[contains(normalize-space(), 'Add')]/ancestor::button[1]"
        ]
        add_button = None
        for sel in add_selectors:
            try:
                log(f"Trying Add button selector: {sel}")
                add_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, sel))
                )
                break
            except TimeoutException:
                continue
        if not add_button or not safe_click(driver, add_button):
            log("Failed to click Add button", "ERROR")
            return False
        log("Clicked Add button, searching for Next Step")
        # Next Step
        next_selectors = [
            "//button[contains(text(), 'Next Step')]",
            "//span[contains(text(), 'Next Step')]/ancestor::button[1]"
        ]
        next_button = None
        for sel in next_selectors:
            try:
                next_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, sel))
                )
                break
            except TimeoutException:
                continue
        if not next_button or not safe_click(driver, next_button):
            log("Failed to click final Next Step", "ERROR")
            return False

        log("Clicked final Next Step, waiting 5 seconds")
        time.sleep(5)

        # Now click Publish
        publish_selectors = [
            "//button[contains(text(), 'Publish')]",
            "//span[contains(text(), 'Publish')]/ancestor::button[1]",
            "//button[.//svg and contains(., 'Publish')]"
        ]
        publish_button = None
        for sel in publish_selectors:
            try:
                publish_button = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, sel))
                )
                break
            except TimeoutException:
                continue
        if publish_button and safe_click(driver, publish_button):
            log("Clicked 'Publish' button")
            return True
        else:
            log("Failed to click 'Publish' button", "ERROR")
            return False
    except Exception as e:
        log(f"Error in set_business_details: {e}", "ERROR")
        return False

def main():
    """Main execution function"""
    driver = None
    try:
        # Setup Chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--headless')  # Uncomment for headless mode
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        
        # Perform login
        if login(driver):
            log("Login successful, waiting for page to load")
            time.sleep(3)  # Give page time to fully load
            
            # Click Add New Mission
            if click_add_new_mission(driver):
                log("Successfully navigated to Add New Mission")
                # Fill job title and generate description
                if fill_job_title_and_generate_description(driver):
                    log("Job title filled and description generated")
                    # After description step completed, set work model and location
                    if set_work_model_and_location(driver):
                        log("Work model and location set successfully")
                        if set_business_details(driver):
                            log("Business details filled successfully")
                        else:
                            log("Failed to fill business details", "ERROR")
                    else:
                        log("Failed to set work model or location", "ERROR")
                else:
                    log("Failed to fill job title or generate description", "ERROR")
                time.sleep(5)  # Keep browser open to see result
            else:
                log("Failed to click Add New Mission button", "ERROR")
        else:
            log("Login failed", "ERROR")
            
    except Exception as e:
        log(f"Main execution error: {e}", "ERROR")
    finally:
        if driver:
            input("Press Enter to close the browser...")  # Keep browser open for inspection
            driver.quit()

if __name__ == "__main__":
    main()