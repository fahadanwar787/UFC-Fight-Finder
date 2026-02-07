# UFC Fight Finder

A web application that allows you to search for UFC fighters, view their fight history (without spoilers), and get direct links to watch fights on Paramount+.

## Features

- 🔍 **Live Search with Autocomplete**: Start typing and see fighter suggestions appear instantly
- 👤 **Full Names Displayed**: See both first and last names of all fighters
- 📋 **Spoiler-Free History**: View all previous fights without any win/loss indicators
- 🎯 **Event Details**: See which event each fight took place at, the date, and opponent
- 📺 **Direct Paramount+ Links**: Click any fight to search for that specific fight on Paramount+

## Requirements

- Python 3.8 or higher
- Internet connection

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or if you prefer using a virtual environment (recommended):
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it (Windows)
   venv\Scripts\activate
   
   # Activate it (Mac/Linux)
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and go to:
   ```
   http://localhost:5000
   ```

3. **Search for a fighter**:
   - Start typing a fighter's name (e.g., "Conor", "Khabib")
   - Select the fighter from the autocomplete dropdown that appears
   - The app will automatically load their fight history

4. **Browse fights**:
   - View the fighter's complete fight history
   - Click on any fight to watch it on Paramount+

## How It Works

- **Data Source**: The application fetches fight data from UFC Stats (ufcstats.com)
- **Spoiler-Free**: Fight results are completely hidden - no win/loss/method information shown
- **Full Names**: Displays complete fighter names (first and last)
- **Accurate Records**: Shows actual W-L-D records for each fighter
- **Smart Paramount+ Links**: 
  - Attempts to find direct video codes for specific fights
  - Falls back to targeted search if direct link unavailable
  - Uses fighter last names and event numbers for precise results

## Notes

- The application requires an active internet connection to fetch fighter data
- Paramount+ links will search for the specific event and fighter
- You'll need a Paramount+ subscription to watch the fights
- Some older fights may not be available on Paramount+

## Troubleshooting

**Issue**: "No fighters found"
- Check your spelling
- Try using the fighter's full name
- Try alternative spellings

**Issue**: Application won't start
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that port 5000 is not already in use
- Try running on a different port: `flask run --port 5001`

**Issue**: Can't load fight history
- This might be due to network issues or the UFC Stats website being temporarily unavailable
- Wait a moment and try again

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, JavaScript
- **Data Source**: UFC Stats website
- **Web Scraping**: BeautifulSoup4, Requests

## License

This is a personal project for educational purposes. UFC and Paramount+ are trademarks of their respective owners.

## Disclaimer

This application is not affiliated with, endorsed by, or connected to the UFC or Paramount+. It is an independent tool created to help fans find and watch UFC fights.
