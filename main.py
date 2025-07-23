import os
from login import login_with_selenium
from add_qualified_talent import main as add_qualified_talent
from add_mission import main as add_mission
from dotenv import load_dotenv
from testing_report import TerminalReportGenerator

load_dotenv()

def run_selenium_tests():
    results = []
    username = os.getenv("USERNAME_FR")
    password = os.getenv("PASSWORD")
    if not username or not password:
        raise Exception("Please set KWIKS_USERNAME and KWIKS_PASSWORD environment variables.")
    try:
        driver = login_with_selenium(username, password)
        results.append("Test: Login - PASSED")
    except Exception as e:
        results.append(f"Test: Login - FAILED ({e})")
        return results
    try:
        add_qualified_talent()
        results.append("Test: Add Qualified Talent - PASSED")
    except Exception as e:
        results.append(f"Test: Add Qualified Talent - FAILED ({e})")

    try:
        add_mission()
        results.append("Test: Add Mission - PASSED")
    except Exception as e:
        results.append(f"Test: Add Mission - FAILED ({e})")
    input("Press Enter to close the browser...")
    driver.quit()
    return results

if __name__ == "__main__":
    test_results = run_selenium_tests()
    