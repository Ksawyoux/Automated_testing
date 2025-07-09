import os
import sys
import datetime
import google.generativeai as genai
from dotenv import load_dotenv

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
        self.model = genai.GenerativeModel("models/gemini-2.5-flash")
    
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
            
            prompt = f"""
You are a professional QA engineer. Generate a comprehensive test report in Markdown format based on the following test results.

Test Results:
{test_results}

Requirements for the report:
1. Use proper Markdown formatting
2. Include a clear executive summary
3. Categorize results into: PASSED, FAILED, SKIPPED, ERROR
4. Provide detailed analysis of failures
5. Include actionable recommendations
6. Add test metrics and statistics
7. Use professional language and structure

Structure the report with these sections:
- Executive Summary
- Test Overview
- Test Results Summary
- Detailed Results
- Failed Tests Analysis
- Recommendations
- Next Steps

Generate timestamp: {timestamp}
"""
            
            print("🤖 Generating report with Gemini AI...")
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Error generating report with Gemini: {e}")
            return self.generate_fallback_report(test_results, str(e))
    
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

## Manual Analysis Required
Please manually review the test results above and create a proper analysis.

## Recommendations
1. Check the AI service connectivity
2. Verify API key configuration
3. Review test result format
4. Consider manual report generation
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