import os
from add_qualified_talent import main as add_qualified_talent
from add_mission import main as add_mission
from dotenv import load_dotenv
from testing_report import TerminalReportGenerator

load_dotenv()

def run_selenium_tests():
    results = []
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
    return results

if __name__ == "__main__":
    test_results = run_selenium_tests()

    # Generate AI report automatically
    try:
        generator = TerminalReportGenerator()
        results_text = "\n".join(test_results)
        report_md = generator.generate_report(results_text)
        
        report_filename = "test_report.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"✅ Test report saved to {report_filename}")
    except Exception as e:
        print(f"⚠️ Could not generate AI report: {e}")
        print("Raw test results:\n", "\n".join(test_results))
    