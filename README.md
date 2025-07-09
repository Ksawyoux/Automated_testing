# Selenium + CrewAI Automation Project

This project uses [Selenium](https://www.selenium.dev/) for browser automation and [CrewAI](https://github.com/joaomdmoura/crewAI) for agent-based workflows in Python.
This is a general use case of testing a web application using "Selenium" and creating a report using "CrewAI".

## Prerequisites
- Python 3.8+
- Google Chrome or another supported browser

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <your-project-directory>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the .env file**
   Create a `.env` file in the project root with your environment variables. See the example below.
   ```
   export KWIKS_USERNAME="Client Email"
   export KWIKS_PASSWORD="Client Password"
   export GEMINI_API_KEY="Gemini API KEY"
   ```

5. **Download the appropriate WebDriver**
   - If you use Chrome, download [ChromeDriver](https://sites.google.com/chromium.org/driver/) and ensure it is in your PATH, or use `webdriver-manager` for automatic management.

## Running the Automation

Run your main script:

```bash
python main.py
```

## Notes
- Make sure your browser version matches the WebDriver version.
- If you use `webdriver-manager`, you may not need to set `SELENIUM_DRIVER_PATH`.
- For CrewAI usage, refer to the [CrewAI documentation](https://github.com/joaomdmoura/crewAI) for agent setup and orchestration.


---

Feel free to customize this README for your specific workflow or add more details as needed. 
