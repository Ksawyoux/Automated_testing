import os
from login import login_with_selenium
from add_qualified_talent import main as add_qualified_talent
from dotenv import load_dotenv
from testing_report import TerminalReportGenerator

load_dotenv()

def run_selenium_tests():
    results = []
    username = os.getenv("USERNAME")
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
    input("Press Enter to close the browser...")
    driver.quit()
    return results

def generate_report_only(test_results):
    agent = TerminalReportGenerator()
    report = agent.generate_report("\n".join(test_results))
    report_path = "test_report.md"
    with open(report_path, "w") as md_file:
        md_file.write(report)
    print("Generated Test Report saved to test_report.md")

if __name__ == "__main__":
    test_results = run_selenium_tests()
    generate_report_only(test_results)