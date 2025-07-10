# add_mission.py - Complete and improved module with all functions

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains

def log(msg):
    print(f"[LOG] {msg}")

def safe_click(driver, element, max_retries=3):
    for attempt in range(max_retries):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
            time.sleep(0.2)
            element.click()
            log(f"Clicked element on attempt {attempt + 1}")
            return True
        except ElementClickInterceptedException:
            log(f"Click intercepted, trying JS click (attempt {attempt + 1})")
            try:
                driver.execute_script("arguments[0].click();", element)
                log("Clicked element with JS")
                return True
            except Exception as js_error:
                log(f"JS click failed: {js_error}")
        except Exception as e:
            log(f"Click attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    return False

def wait_and_click(driver, selectors, timeout=10):
    wait = WebDriverWait(driver, timeout)
    for by, value in selectors:
        try:
            element = wait.until(EC.element_to_be_clickable((by, value)))
            if safe_click(driver, element):
                return element
        except TimeoutException:
            log(f"Element not found: {by}='{value}'")
    return None

def fill_input(driver, selectors, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    for by, val in selectors:
        try:
            element = wait.until(EC.visibility_of_element_located((by, val)))
            element.clear()
            element.send_keys(value)
            log(f"Filled input: {value}")
            return element
        except TimeoutException:
            log(f"Input not found: {by}='{val}'")
    return None

def select_first_dropdown_option(driver, dropdown_xpath, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        safe_click(driver, dropdown)
        time.sleep(0.5)
        option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option' or @tabindex='0'][1]")))
        safe_click(driver, option)
        log("Selected the first option from dropdown.")
        return True
    except Exception as e:
        log(f"Could not select from dropdown: {e}")
        return False

def select_multiple_skills(driver, dropdown_xpath, n=3, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, dropdown_xpath)))
        safe_click(driver, dropdown)
        time.sleep(0.5)
        skill_options = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='option' or @tabindex='0']")))
        selected = 0
        for skill in skill_options:
            if selected >= n:
                break
            try:
                safe_click(driver, skill)
                selected += 1
                time.sleep(0.2)
            except Exception:
                continue
        safe_click(driver, dropdown)  # Close dropdown
        log(f"Selected {selected} skills.")
        return selected >= n
    except Exception as e:
        log(f"Could not select skills: {e}")
        return False

def report_debug_info(driver, context, label_text=None, option_text=None, search_text=None, extra_message=None):
    log(f"[DEBUG REPORT] Context: {context}")
    if label_text:
        log(f"  - Attempted label: '{label_text}'")
        # Print all elements containing the label text
        labels = driver.find_elements(By.XPATH, f"//*[contains(text(), '{label_text}')]")
        log(f"  - Found {len(labels)} elements containing label text '{label_text}'")
        for idx, label in enumerate(labels):
            try:
                log(f"    Label {idx}: {label.get_attribute('outerHTML')}")
            except Exception:
                continue
    if option_text:
        log(f"  - Attempted option: '{option_text}'")
    if search_text:
        log(f"  - Attempted search text: '{search_text}'")
    if extra_message:
        log(f"  - Extra info: {extra_message}")
    log("  - SUGGESTIONS:")
    log("    1. Check if the label text matches exactly as it appears in the UI.")
    log("    2. Inspect the HTML structure of the dropdown and options.")
    log("    3. Try using a different label or option text if the current one is not found.")
    log("    4. If the dropdown is custom, check for unique attributes (aria-label, placeholder, etc.).")
    log("    5. If options are not visible, try increasing wait times or check for async loading.")

def select_labeled_dropdown_option(driver, label_text, option_text=None, search_text=None, timeout=10, select_first=False):
    wait = WebDriverWait(driver, timeout)
    label_xpath = f"//*[contains(text(), '{label_text}')]"
    try:
        label_elem = wait.until(EC.visibility_of_element_located((By.XPATH, label_xpath)))
        log(f"Found label for '{label_text}': {label_elem.get_attribute('outerHTML')}")
        dropdown_xpath = (
            ".//following-sibling::*[self::div or self::button][1]"
            " | "
            "./ancestor::*[self::div or self::label]/following-sibling::*[self::div or self::label or self::button][1]"
        )
        try:
            dropdown_elem = label_elem.find_element(By.XPATH, dropdown_xpath)
        except Exception:
            try:
                dropdown_elem = driver.find_element(By.XPATH, f"//*[contains(text(), '{label_text}')]/following::div[contains(@role, 'button') or @tabindex='0'][1]")
            except Exception:
                report_debug_info(driver, "Dropdown not found after label", label_text=label_text)
                return False
        log(f"Found dropdown for '{label_text}': {dropdown_elem.get_attribute('outerHTML')}")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_elem)
        ActionChains(driver).move_to_element(dropdown_elem).click().perform()

        panel_xpath = "//div[contains(@role, 'listbox') or contains(@class, 'dropdown')][not(contains(@style, 'display: none'))]"
        try:
            panel = wait.until(EC.visibility_of_element_located((By.XPATH, panel_xpath)))
        except Exception:
            report_debug_info(driver, "Dropdown panel not found or not visible", label_text=label_text)
            return False
        log(f"Dropdown panel for '{label_text}': {panel.get_attribute('outerHTML')[:1000]}")

        if search_text:
            try:
                search_input = panel.find_element(By.XPATH, ".//input[@type='text' or @role='searchbox']")
                search_input.clear()
                search_input.send_keys(search_text)
                time.sleep(0.5)
                log(f"Typed '{search_text}' in search input for '{label_text}'")
            except Exception as e:
                log(f"No search input in dropdown: {e}")
                report_debug_info(driver, "Search input not found in dropdown panel", label_text=label_text, search_text=search_text, extra_message=str(e))
                return False

        if option_text:
            option_xpaths = [
                f".//div[contains(@role, 'option') and contains(., '{option_text}')]",
                f".//li[contains(@role, 'option') and contains(., '{option_text}')]",
                f".//span[contains(., '{option_text}')]",
                f".//*[contains(text(), '{option_text}')]"
            ]
            option = None
            for ox in option_xpaths:
                try:
                    option = WebDriverWait(panel, timeout).until(lambda d: panel.find_element(By.XPATH, ox))
                    if option.is_displayed():
                        break
                except Exception:
                    continue
            if not option:
                report_debug_info(driver, "Option not found in dropdown panel", label_text=label_text, option_text=option_text)
                return False
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", option)
            if not safe_click(driver, option):
                report_debug_info(driver, "Failed to click option in dropdown", label_text=label_text, option_text=option_text)
                return False
            log(f"Selected '{option_text}' from dropdown labeled '{label_text}'.")
        elif select_first:
            try:
                first_option = panel.find_element(By.XPATH, ".//div[@role='option' or @tabindex='0'][1] | .//li[@role='option'][1]")
                if not safe_click(driver, first_option):
                    report_debug_info(driver, "Failed to click first option in dropdown", label_text=label_text)
                    return False
                log(f"Selected first option from dropdown labeled '{label_text}'.")
            except Exception as e:
                report_debug_info(driver, "First option not found or not clickable", label_text=label_text, extra_message=str(e))
                return False
        else:
            log(f"Labeled dropdown '{label_text}' opened.")
        time.sleep(0.5)
        return True
    except Exception as e:
        report_debug_info(driver, "General error in select_labeled_dropdown_option", label_text=label_text, option_text=option_text, search_text=search_text, extra_message=str(e))
        return False

def add_new_mission(driver, job_title="TEST11", job_description="This is an Automated test mission"):
    log("Starting mission creation process...")

    # Step 1: Click 'Add New Mission'
    add_btn_selectors = [
        (By.XPATH, "//button[contains(., 'Add New Mission')]"),
        (By.XPATH, "//span[contains(text(), 'Add New Mission')]/ancestor::button"),
    ]
    if not wait_and_click(driver, add_btn_selectors):
        log("Failed to click 'Add New Mission'")
        return False

    # Step 2: Fill Job Title
    job_title_selectors = [
        (By.XPATH, "//input[@placeholder='Job Title']"),
        (By.XPATH, "//input[contains(@placeholder, 'Title')]"),
    ]
    if not fill_input(driver, job_title_selectors, job_title):
        log("Failed to fill Job Title")
        return False

    # Step 3: Fill Job Description
    desc_selectors = [(By.CSS_SELECTOR, "div[contenteditable='true']")]
    if not fill_input(driver, desc_selectors, job_description):
        log("Failed to fill Job Description")
        return False

    # Step 4: Click Next Step
    next_step_selectors = [
        (By.XPATH, "//button[contains(., 'Next Step')]"),
        (By.XPATH, "//span[contains(text(), 'Next Step')]/ancestor::button"),
    ]
    if not wait_and_click(driver, next_step_selectors):
        log("Failed to click Next Step")
        return False

    # Step 5: Work Model
    log("Selecting Work Model: On-site...")
    try:
        options = [
            "//label[contains(., 'On-site')]",
            "//span[contains(text(), 'On-site')]/ancestor::*[self::label or self::div or self::button]",
            "//div[contains(@class, 'work-model')]//*[contains(text(), 'On-site')]"
        ]
        work_model_element = None
        wait = WebDriverWait(driver, 10)
        for xpath in options:
            try:
                work_model_element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                if work_model_element:
                    break
            except Exception:
                continue
        if work_model_element:
            safe_click(driver, work_model_element)
            log("Selected 'On-site' work model.")
        else:
            log("Could not find 'On-site' work model.")
    except Exception as e:
        log(f"Error selecting work model: {e}")

    # Step 6: Country
    if not select_labeled_dropdown_option(driver, "Country", "Morocco", search_text="Morocco"):
        log("Failed to select Country")
        return False

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


    log("Mission creation completed successfully!")
    return True
