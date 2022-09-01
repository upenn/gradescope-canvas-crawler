# Gradescope to iCalendar Converter

Project forked from [apozharski/gradescope-api](https://github.com/apozharski/gradescope-api) because I didn't feel like writing a webcrawler.

## Usage

```bash
python -m venv venv # Create a virtual environment
chmod +x venv/bin/activate # Make the activate script executable
source venv/bin/activate # Activate the virtual environment
pip install -r requirements.txt # Install dependencies
python main.py # Run the script
```

You'll be prompted for your Gradescope username and password. After the script runs, there should be a file called `gradescope.ics` in the current directory.
