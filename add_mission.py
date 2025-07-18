# add_mission.py - Enhanced and improved module with all functions
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log(msg, level="INFO"):
    """Enhanced logging with different levels"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    if level == "ERROR":
        logger.error(f"[{timestamp}] {msg}")
    elif level == "WARNING":
        logger.warning(f"[{timestamp}] {msg}")
    else:
        logger.info(f"[{timestamp}] {msg}")
    print(f"[{timestamp}] {msg}")

def safe_click(driver, element, max_retries=3):
    """
    Safely click an element with multiple retry strategies
    """
    for attempt in range(max_retries):
        try:
            # Check if element is still attached to DOM
            if not element.is_displayed():
                log(f"Element not displayed on attempt {attempt + 1}", "WARNING")
                time.sleep(0.5)
                continue
                
            # Scroll element into view with better positioning
            driver.execute_script("""
                arguments[0].scrollIntoView({
                    block: 'center', 
                    inline: 'center',
                    behavior: 'smooth'
                });
            """, element)
            time.sleep(0.5)
            
            # Wait for element to be clickable
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
            
            # Try normal click
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

def wait_and_click(driver, selectors, timeout=10):
    """
    Wait for element(s) and click the first available one
    Enhanced with better error handling
    """
    wait = WebDriverWait(driver, timeout)
    
    # If single selector passed, convert to list
    if isinstance(selectors, tuple):
        selectors = [selectors]
    
    for by, value in selectors:
        try:
            log(f"Trying selector: {by}={value}")
            element = wait.until(EC.element_to_be_clickable((by, value)))
            if safe_click(driver, element):
                log(f"Successfully clicked element: {value}")
                return element
        except TimeoutException:
            log(f"Timeout waiting for element: {value}", "WARNING")
            continue
        except Exception as e:
            log(f"Error with element {value}: {e}", "ERROR")
            continue
    
    log("No clickable elements found", "ERROR")
    return None

def safe_send_keys(driver, element, text, clear_first=True):
    """
    Safely send keys to an element with enhanced error handling
    """
    try:
        # Ensure element is visible and interactable
        if not element.is_displayed():
            log("Element not visible for text input", "WARNING")
            return False
            
        # Scroll to element
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        
        # Focus on element
        element.click()
        time.sleep(0.2)
        
        if clear_first:
            # Clear using multiple methods
            element.clear()
            time.sleep(0.1)
            # Additional clear using select all + delete
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            time.sleep(0.1)
        
        # Send text character by character for better reliability
        for char in text:
            element.send_keys(char)
            time.sleep(0.02)  # Small delay between characters
            
        log(f"Successfully sent keys: {text}")
        return True
        
    except Exception as e:
        log(f"Failed to send keys '{text}': {e}", "ERROR")
        return False

def wait_for_element(driver, by, value, timeout=10, condition=EC.presence_of_element_located):
    """
    Wait for an element with customizable condition
    """
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(condition((by, value)))
        log(f"Found element: {value}")
        return element
    except TimeoutException:
        log(f"Timeout waiting for element: {value}", "WARNING")
        return None
    except Exception as e:
        log(f"Error waiting for element {value}: {e}", "ERROR")
        return None

def fill_contenteditable_field(driver, element, text):
    """
    Specialized function for filling contenteditable fields (like TipTap editor)
    """
    try:
        # Focus on the element
        element.click()
        time.sleep(0.3)
        
        # Clear existing content
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        element.send_keys(Keys.DELETE)
        time.sleep(0.1)
        
        # For rich text editors, we might need to use innerHTML
        driver.execute_script("arguments[0].innerHTML = arguments[1];", element, text)
        
        # Trigger input event to ensure the change is registered
        driver.execute_script("""
            var event = new Event('input', { bubbles: true });
            arguments[0].dispatchEvent(event);
        """, element)
        
        log(f"Filled contenteditable field with: {text}")
        return True
        
    except Exception as e:
        log(f"Failed to fill contenteditable field: {e}", "ERROR")
        return False

def select_dropdown_option(driver, dropdown_element, option_text):
    """
    Enhanced dropdown selection with multiple strategies
    """
    try:
        # Strategy 1: Standard Select dropdown
        try:
            select = Select(dropdown_element)
            select.select_by_visible_text(option_text)
            log(f"Selected option via Select: {option_text}")
            return True
        except Exception:
            pass
        
        # Strategy 2: Custom dropdown (click to open, then select)
        try:
            dropdown_element.click()
            time.sleep(0.5)
            
            # Look for option in dropdown
            option_selectors = [
                (By.XPATH, f"//option[contains(text(), '{option_text}')]"),
                (By.XPATH, f"//*[contains(text(), '{option_text}')]"),
                (By.CSS_SELECTOR, f"[data-value='{option_text}']"),
            ]
            
            for by, selector in option_selectors:
                try:
                    option = wait_for_element(driver, by, selector, timeout=5)
                    if option and safe_click(driver, option):
                        log(f"Selected custom dropdown option: {option_text}")
                        return True
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        # Strategy 3: React Select or similar
        try:
            dropdown_element.click()
            dropdown_element.send_keys(option_text)
            time.sleep(0.5)
            dropdown_element.send_keys(Keys.ENTER)
            log(f"Selected via text input: {option_text}")
            return True
        except Exception:
            pass
        
        log(f"Failed to select option: {option_text}", "ERROR")
        return False
        
    except Exception as e:
        log(f"Error selecting dropdown option {option_text}: {e}", "ERROR")
        return False

def add_mission(driver, mission_data):
    """
    Enhanced main function to add a mission with better error handling
    """
    try:
        log("Starting mission addition process")
        
        # Enhanced selectors for add mission button
        add_button_selectors = [
            (By.XPATH, "//button[contains(text(), 'Add New Mission')]"),
            (By.XPATH, "//button[contains(text(), 'Add Mission')]"),
            (By.XPATH, "//button[contains(text(), 'New Mission')]"),
            (By.XPATH, "//button[contains(text(), '+')]"),
            (By.CSS_SELECTOR, "button.chakra-button.mui-1ynj8wc"),
            (By.XPATH, "//button[.//p[text()='Add New Mission']]"),
            (By.CSS_SELECTOR, "button[class*='mui-1ynj8wc']"),
            (By.CSS_SELECTOR, "[data-testid='add-mission-button']"),
        ]
        
        # Click add mission button
        if not wait_and_click(driver, add_button_selectors, timeout=15):
            log("Failed to find add mission button", "ERROR")
            return False
        
        # Wait for form to load
        time.sleep(3)
        
        # Fill Job Title
        if not fill_job_title(driver, mission_data.get('title', '')):
            return False
        
        # Fill Job Description
        if not fill_job_description(driver, mission_data.get('description', '')):
            return False
        
        # Click Next button
        if not click_next_button(driver, "after job description"):
            return False
        
        # Select Work Model (On-Site)
        if not select_work_model(driver, 'On-Site'):
            return False
        
        # Select Country
        if not select_country(driver, mission_data.get('country', 'Morocco')):
            return False
        
        # Select City
        if not select_city(driver, mission_data.get('city', 'Ifrane')):
            return False
        
        # Click Next button
        if not click_next_button(driver, "after location selection"):
            return False
        
        log("Mission addition process completed successfully")
        return True
        
    except Exception as e:
        log(f"Error in add_mission: {e}", "ERROR")
        return False

def fill_job_title(driver, job_title):
    """Specialized function for filling job title"""
    if not job_title:
        log("No job title provided", "WARNING")
        return True
    
    log(f"Filling job title: {job_title}")
    
    title_selectors = [
        (By.XPATH, "//label[contains(text(), 'Job Title')]/following-sibling::input"),
        (By.XPATH, "//input[@placeholder='Job Title']"),
        (By.XPATH, "//input[contains(@aria-label, 'Job Title')]"),
        (By.CSS_SELECTOR, "input[placeholder*='Job Title' i]"),
        (By.CSS_SELECTOR, "input[name*='title' i]"),
        (By.CSS_SELECTOR, "input[type='text']:first-of-type"),
        (By.CSS_SELECTOR, "[data-testid='job-title-input']"),
    ]
    
    for by, selector in title_selectors:
        try:
            element = wait_for_element(driver, by, selector, timeout=5)
            if element and element.is_displayed():
                if safe_send_keys(driver, element, job_title):
                    log(f"Successfully filled job title: {job_title}")
                    return True
        except Exception as e:
            log(f"Failed with selector {selector}: {e}", "WARNING")
            continue
    
    log("Failed to find or fill job title field", "ERROR")
    return False

def fill_job_description(driver, job_description):
    """Specialized function for filling job description"""
    if not job_description:
        log("No job description provided", "WARNING")
        return True
    
    log(f"Filling job description: {job_description}")
    
    desc_selectors = [
        (By.CSS_SELECTOR, "div[contenteditable='true'].tiptap.ProseMirror"),
        (By.CSS_SELECTOR, "div[contenteditable='true']"),
        (By.CSS_SELECTOR, "textarea[placeholder*='description' i]"),
        (By.CSS_SELECTOR, "textarea"),
        (By.CSS_SELECTOR, "[data-testid='job-description-input']"),
    ]
    
    for by, selector in desc_selectors:
        try:
            element = wait_for_element(driver, by, selector, timeout=5)
            if element and element.is_displayed():
                # Check if it's a contenteditable field
                if element.get_attribute('contenteditable') == 'true':
                    if fill_contenteditable_field(driver, element, job_description):
                        log(f"Successfully filled job description: {job_description}")
                        return True
                else:
                    if safe_send_keys(driver, element, job_description):
                        log(f"Successfully filled job description: {job_description}")
                        return True
        except Exception as e:
            log(f"Failed with selector {selector}: {e}", "WARNING")
            continue
    
    log("Failed to find or fill job description field", "ERROR")
    return False

def click_next_button(driver, context=""):
    """Specialized function for clicking Next button"""
    log(f"Clicking Next button {context}")
    
    next_selectors = [
        (By.XPATH, "//button[contains(text(), 'Next') and not(@disabled)]"),
        (By.XPATH, "//button[text()='Next']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "button.chakra-button:not([disabled])"),
        (By.CSS_SELECTOR, "[data-testid='next-button']"),
    ]
    
    if wait_and_click(driver, next_selectors, timeout=10):
        log(f"Successfully clicked Next button {context}")
        time.sleep(2)
        return True
    
    log(f"Failed to click Next button {context}", "ERROR")
    return False

def select_work_model(driver, work_model):
    """Specialized function for selecting work model"""
    log(f"Selecting work model: {work_model}")
    
    # Scroll to top to ensure we can see the work model section
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    work_model_selectors = [
        (By.XPATH, f"//span[contains(text(), '{work_model}')]"),
        (By.XPATH, f"//label[contains(text(), '{work_model}')]"),
        (By.XPATH, f"//div[contains(text(), '{work_model}')]"),
        (By.XPATH, f"//*[contains(text(), '{work_model}')]"),
        (By.CSS_SELECTOR, f"[data-testid='work-model-{work_model.lower()}']"),
    ]
    
    for by, selector in work_model_selectors:
        try:
            element = wait_for_element(driver, by, selector, timeout=5)
            if element and element.is_displayed():
                # Try to find radio button control
                try:
                    radio_control = element.find_element(By.XPATH, "ancestor::label//span[contains(@class, 'chakra-radio__control')]")
                    if safe_click(driver, radio_control):
                        log(f"Selected work model: {work_model}")
                        return True
                except Exception:
                    pass
                
                # Try clicking the element itself
                if safe_click(driver, element):
                    log(f"Selected work model: {work_model}")
                    return True
        except Exception as e:
            log(f"Failed with work model selector {selector}: {e}", "WARNING")
            continue
    
    log(f"Failed to select work model: {work_model}", "ERROR")
    return False

def select_country(driver, country):
    """Specialized function for selecting country"""
    log(f"Selecting country: {country}")
    
    try:
        country_input = wait_for_element(
            driver, 
            By.XPATH, 
            "//input[@role='combobox' and contains(@id, 'react-select') and @type='text']",
            timeout=10
        )
        
        if country_input:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", country_input)
            time.sleep(0.5)
            
            if safe_send_keys(driver, country_input, country, clear_first=True):
                time.sleep(0.5)
                country_input.send_keys(Keys.ENTER)
                log(f"Selected country: {country}")
                return True
        
        log(f"Failed to select country: {country}", "ERROR")
        return False
        
    except Exception as e:
        log(f"Error selecting country {country}: {e}", "ERROR")
        return False

<<<<<<< HEAD
def select_city(driver, city):
    """Specialized function for selecting city"""
    log(f"Selecting city: {city}")
    
    try:
        # Wait a moment for the city dropdown to become available
        time.sleep(1)
        
        city_input = wait_for_element(
            driver,
            By.XPATH,
            "//input[@role='combobox' and contains(@id, 'react-select') and @type='text']",
            timeout=10
        )
        
        if city_input:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_input)
            time.sleep(0.5)
            
            if safe_send_keys(driver, city_input, city, clear_first=True):
                time.sleep(0.5)
                city_input.send_keys(Keys.ENTER)
                log(f"Selected city: {city}")
                return True
        
        log(f"Failed to select city: {city}", "ERROR")
        return False
        
    except Exception as e:
        log(f"Error selecting city {city}: {e}", "ERROR")
        return False

def wait_for_page_load(driver, timeout=30):
    """Wait for page to fully load with enhanced checks"""
    try:
        # Wait for document ready state
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Wait for jQuery if present
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return typeof jQuery !== 'undefined' && jQuery.active == 0")
            )
        except TimeoutException:
            pass  # jQuery might not be present
        
        # Wait for any loading spinners to disappear
        try:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [data-testid='loading']"))
            )
        except TimeoutException:
            pass  # No loading elements found
        
        log("Page loaded successfully")
        return True
        
    except TimeoutException:
        log("Page load timeout", "WARNING")
        return False
    except Exception as e:
        log(f"Error waiting for page load: {e}", "ERROR")
        return False
=======
    # Step 7: City
    if not select_labeled_dropdown_option(driver, "City", "Ifrane", search_text="Ifrane"):
        log("Failed to select City")
        return False

    # Step 8: Next Step
    if not wait_and_click(driver, next_step_selectors):
        log("Failed to click Next Step again")
        return False

    # Step 9: Business Line
    if not select_labeled_dropdown_option(driver, "Business Line", select_first=True):
        log("Failed to select Business Line")
        return False

>>>>>>> dcb5d6ae5d306ca5e4e9343ab16c8fdbed6fe37e

def handle_popup(driver):
    """Handle any popup dialogs that might appear"""
    try:
        # Check for JavaScript alert
        alert = driver.switch_to.alert
        alert_text = alert.text
        log(f"Alert found: {alert_text}")
        alert.accept()
        return True
    except Exception:
        pass
    
    # Check for modal dialogs
    modal_selectors = [
        (By.CSS_SELECTOR, ".modal"),
        (By.CSS_SELECTOR, ".chakra-modal"),
        (By.CSS_SELECTOR, "[role='dialog']"),
        (By.CSS_SELECTOR, "[data-testid='modal']"),
    ]
    
    for by, selector in modal_selectors:
        try:
            modal = driver.find_element(by, selector)
            if modal.is_displayed():
                log("Modal dialog found")
                # Try to close it
                close_selectors = [
                    (By.CSS_SELECTOR, ".close"),
                    (By.CSS_SELECTOR, "[aria-label='Close']"),
                    (By.CSS_SELECTOR, ".modal-close"),
                    (By.XPATH, "//button[contains(text(), 'Close')]"),
                ]
                
                for close_by, close_selector in close_selectors:
                    try:
                        close_btn = modal.find_element(close_by, close_selector)
                        if safe_click(driver, close_btn):
                            log("Closed modal dialog")
                            return True
                    except Exception:
                        continue
        except Exception:
            continue
    
    return False

# Example usage and testing
def test_mission_data():
    """Example mission data structure"""
    return {
        'title': 'Software Engineer',
        'description': 'Develop and maintain web applications using modern technologies.',
        'country': 'Morocco',
        'city': 'Ifrane',
        'work_model': 'On-Site',
        'priority': 'High',
        'deadline': '2024-12-31'
    }

if __name__ == "__main__":
    log("Enhanced add_mission.py module loaded successfully")
    print("\nAvailable functions:")
    print("- add_mission(driver, mission_data)")
    print("- fill_job_title(driver, job_title)")
    print("- fill_job_description(driver, job_description)")
    print("- select_work_model(driver, work_model)")
    print("- select_country(driver, country)")
    print("- select_city(driver, city)")
    print("- wait_and_click(driver, selectors)")
    print("- safe_click(driver, element)")
    print("- safe_send_keys(driver, element, text)")
    print("- wait_for_page_load(driver)")
    print("- handle_popup(driver)")
    print("\nExample usage:")
    print("mission_data = test_mission_data()")
    print("result = add_mission(driver, mission_data)")