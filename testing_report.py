import os
import sys
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()



class TerminalReportGenerator:
    """Terminal-based test report generator using Gemini AI."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("models/gemini-1.5-flash")
    
    def get_test_results_input(self):
        """Get test results from command line arguments or stdin."""
        if len(sys.argv) > 1:
            # Test results provided as command line arguments
            return ' '.join(sys.argv[1:])
        else:
            # Read from stdin
            print("📝 Enter your test results (end with Ctrl+D on Unix/Mac or Ctrl+Z on Windows):")
            try:
                return sys.stdin.read()
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user.")
                sys.exit(0)
    
    def generate_report(self, test_results):
        """Generate a test report using Gemini AI."""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Parse test results to map terminal output lines to their corresponding test files
            file_steps_map = self.parse_test_results(test_results)
            parsed_steps_md = self._format_parsed_steps_md(file_steps_map)
            
            prompt = f"""
You are a professional QA engineer. Generate a comprehensive test report in Markdown format based on the following test results.

Test Results:
{test_results}

Parsed Test Steps by File:
{parsed_steps_md}

Requirements for the report:
1. Use proper Markdown formatting
2. Include a clear executive summary
3. Categorize results into: PASSED, FAILED, SKIPPED, ERROR
4. Provide detailed analysis of failures
5. Add test metrics and statistics
6. Use professional language and structure

Structure the report with these sections:
- Executive Summary
- Test Overview
- Test Results Summary
- Detailed Results and steps taken
- Failed Tests Analysis


Generate timestamp: {timestamp}
"""
            
            print("🤖 Generating report with Gemini AI...")
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Error generating report with Gemini: {e}")
            return self.generate_fallback_report(test_results, str(e))

    # ----------------------- NEW METHODS -----------------------
    def parse_test_results(self, test_results: str):
        """Parse raw terminal results and group lines by the test file they reference.

        A very generic approach is used: if a line contains a path ending with `.py`, that
        path is considered the *test file* for that line. Otherwise, it falls back to the
        key "unknown" so no data is lost. This should work for typical pytest/unittest
        outputs like:

            tests/test_api.py::TestAPI::test_get PASSED

        or other CLI tools that echo file names.
        """
        file_steps: dict[str, list[str]] = {}
        for raw_line in test_results.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = re.search(r"([\\w./\\-]+\\.py)", line)
            file_key = match.group(1) if match else "unknown"
            file_steps.setdefault(file_key, []).append(line)
        return file_steps

    def _format_parsed_steps_md(self, file_steps_map: dict):
        """Convert parsed steps into a Markdown-friendly string."""
        md_lines: list[str] = []
        for file, steps in file_steps_map.items():
            md_lines.append(f"### {file}")
            for s_idx, step_line in enumerate(steps, 1):
                md_lines.append(f"{s_idx}. {step_line}")
            md_lines.append("")  # blank line for spacing
        if not md_lines:
            md_lines.append("*(No test steps detected)*")
        return "\n".join(md_lines)
    
    def generate_fallback_report(self, test_results, error_msg):
        """Generate a basic fallback report if AI generation fails."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""# Test Report
**Generated:** {timestamp}

## ⚠️ Note
This is a fallback report. AI generation failed with error: {error_msg}

## Raw Test Results
```
{test_results}
```
"""

    def save_report(self, report):
        """Save the report to a file with user confirmation."""
        try:
            filename = input("\n💾 Enter filename to save report (or press Enter for 'test_report.md'): ").strip()
            if not filename:
                filename = "test_report.md"

            # Ensure .md extension
            if not filename.endswith('.md'):
                filename += '.md'

            # Check if file exists
            if os.path.exists(filename):
                overwrite = input(f"📄 File '{filename}' already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    print("❌ Report not saved.")
                    return False

            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            print(f"✅ Report saved to '{filename}'")
            return True

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return False

    def display_report(self, report):
        """Display the report in the terminal with formatting."""
        print("\n" + "="*60)
        print("📊 GENERATED TEST REPORT")
        print("="*60)
        print(report)
        print("="*60)

    def run(self):
        """Main execution method."""
        print("🚀 Terminal Test Report Generator")
        print("-" * 40)

        # Get test results
        test_results = self.get_test_results_input()

        if not test_results.strip():
            print("❌ No test results provided. Exiting.")
            return

        print(f"📊 Processing {len(test_results)} characters of test data...")

        # Generate report
        report = self.generate_report(test_results)

        # Display report
        self.display_report(report)

        # Ask to save the report
        save_choice = input("\n💾 Save report to file? (y/n): ").strip().lower()
        if save_choice == 'y':
            self.save_report(report)

        # Ask to copy to clipboard (if available)
        try:
            import pyperclip
            copy_choice = input("\n📋 Copy report to clipboard? (y/n): ").strip().lower()
            if copy_choice == 'y':
                pyperclip.copy(report)
                print("✅ Report copied to clipboard!")
        except ImportError:
            print("\n💡 Tip: Install 'pyperclip' package to enable clipboard functionality")

        print("\n✅ Report generation complete!")


def main():
    """Entry point for the script."""
    try:
        generator = TerminalReportGenerator()
        generator.run()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()