"""
Scrape ALL UFC fight video links from Paramount+
Uses Selenium to navigate through event dropdowns and load all fights.
Builds a JSON database mapping fighter names to video codes.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re
import json
import time
import sys

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_fights_on_page(driver):
    """Extract all fight video links currently visible on the page"""
    fights = []
    video_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
    
    for elem in video_elements:
        try:
            href = elem.get_attribute('href')
            if not href:
                continue
            
            video_match = re.search(r'/video/([A-Za-z0-9_-]+)', href)
            if not video_match:
                continue
            
            code = video_match.group(1)
            
            # Get text from parent for fight title
            try:
                parent = elem.find_element(By.XPATH, './..')
                text = parent.text.strip()
            except:
                text = elem.text.strip()
            
            # Only include if it looks like a fight (has "vs" in the title)
            if 'vs' in text.lower() or 'vs.' in text.lower():
                # Find the actual fight title line (skip "SUBSCRIBE" button text)
                title_line = ''
                for line in text.split('\n'):
                    line = line.strip()
                    if ('vs' in line.lower() or 'vs.' in line.lower()) and line.upper() != 'SUBSCRIBE':
                        title_line = line
                        break
                
                if title_line:
                    fights.append({
                        'code': code,
                        'url': href,
                        'title': title_line
                    })
        except:
            continue
    
    return fights

def click_show_more(driver, max_clicks=10):
    """Click 'Show More' button until all fights are loaded"""
    for i in range(max_clicks):
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, 'button.load-more-button')
            if show_more.is_displayed():
                driver.execute_script("arguments[0].click();", show_more)
                time.sleep(2)
            else:
                break
        except:
            break

def scrape_show_page(driver, show_url, show_name):
    """Scrape all fights from a Paramount+ show page with season dropdown"""
    all_fights = {}
    
    print(f"\n{'='*60}")
    print(f"Scraping: {show_name}")
    print(f"URL: {show_url}")
    print(f"{'='*60}")
    
    driver.get(show_url)
    time.sleep(5)
    
    # Find the season/event dropdown
    try:
        select_elem = driver.find_element(By.CSS_SELECTOR, 'select.dropdown__filter__fake')
        select = Select(select_elem)
        options = select.options
        event_names = [(opt.get_attribute('value'), opt.text.strip()) for opt in options]
        print(f"Found {len(event_names)} events")
    except Exception as e:
        print(f"No dropdown found: {e}")
        # Just get what's on the page
        click_show_more(driver)
        fights = get_fights_on_page(driver)
        for f in fights:
            all_fights[f['code']] = f
        print(f"Got {len(fights)} fights from page")
        return all_fights
    
    # Iterate through each event
    for idx, (value, name) in enumerate(event_names):
        print(f"\n  [{idx+1}/{len(event_names)}] {name}...")
        
        try:
            # Use JavaScript to change the select value and trigger change event
            # First, click the filter button to open dropdown
            filter_btn = driver.find_element(By.CSS_SELECTOR, 'button.js-filter')
            driver.execute_script("arguments[0].click();", filter_btn)
            time.sleep(0.5)
            
            # Find and click the dropdown option
            dropdown_items = driver.find_elements(By.CSS_SELECTOR, 'ul.dropdown__filter__fake li, .dropdown__filter__list li')
            clicked = False
            for item in dropdown_items:
                if item.text.strip() == name:
                    driver.execute_script("arguments[0].click();", item)
                    clicked = True
                    break
            
            if not clicked:
                # Fallback: use JavaScript to change the select
                driver.execute_script(f"""
                    var select = document.querySelector('select.dropdown__filter__fake');
                    select.value = '{value}';
                    select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                """)
            
            time.sleep(3)
            
            # Click "Show More" to load all fights for this event
            click_show_more(driver)
            
            # Get fights
            fights = get_fights_on_page(driver)
            
            for f in fights:
                if f['code'] not in all_fights:
                    all_fights[f['code']] = f
            
            print(f"    Found {len(fights)} fights (Total unique: {len(all_fights)})")
            
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    return all_fights

def parse_fight_title(title):
    """Parse a fight title into structured data.
    Handles multiple formats:
    1. 'Alexander Volkanovski vs. Diego Lopes (UFC 325: ... - Main)'
    2. '323: Blachowicz vs. Guskov Main Card'
    3. 'UFC 307: Ketlen Vieira vs. Kayla Harrison Main Card'
    4. 'Watch the UFC 313 showdown between Joshua Van vs. Rei Tsuruya streamed on ...'
    5. 'Watch the Alexandre Pantoja vs. Yuta Sasaki bout from UFC Fight Night...'
    6. 'Diego Lopes vs. Jean Silva'
    7. 'UFC 110: Cain Velasquez vs. Antonio Rodrigo Nogueira'
    """
    result = {
        'fighter1': '',
        'fighter2': '',
        'event': '',
        'card': '',
        'raw': title
    }
    
    # Remove "SUBSCRIBE" prefix
    title = re.sub(r'^SUBSCRIBE\s*', '', title).strip()
    
    # Skip event recaps and non-fight content
    if 'Event Recap' in title or 'Storylines' in title or 'Breakdown' in title:
        return result
    
    # FORMAT 1: "Fighter1 vs. Fighter2 (Event - Card)"
    match = re.match(r'(.+?)\s+vs\.?\s+(.+?)\s*\((.+?)\)', title)
    if match:
        result['fighter1'] = match.group(1).strip()
        result['fighter2'] = match.group(2).strip()
        event_part = match.group(3).strip()
        if ' - ' in event_part:
            parts = event_part.rsplit(' - ', 1)
            result['event'] = parts[0].strip()
            result['card'] = parts[1].strip()
        else:
            result['event'] = event_part
        return result
    
    # FORMAT 2: "323: Fighter vs. Fighter Main Card/Prelims"
    match = re.match(r'^(\d+):\s+(.+?)\s+vs\.?\s+(.+?)(?:\s+(Main Card|Prelims|Early Prelims))?\s*$', title)
    if match:
        result['event'] = f"UFC {match.group(1)}"
        result['fighter1'] = match.group(2).strip()
        result['fighter2'] = match.group(3).strip()
        result['card'] = match.group(4).strip() if match.group(4) else ''
        return result
    
    # FORMAT 3: "UFC 307: Fighter vs. Fighter Main Card/Prelims"
    match = re.match(r'^(UFC\s+\d+):\s+(.+?)\s+vs\.?\s+(.+?)(?:\s+(Main Card|Prelims|Early Prelims))?\s*$', title)
    if match:
        result['event'] = match.group(1).strip()
        result['fighter1'] = match.group(2).strip()
        result['fighter2'] = match.group(3).strip()
        result['card'] = match.group(4).strip() if match.group(4) else ''
        return result
    
    # FORMAT 4: "Watch the UFC NNN showdown between Fighter1 vs. Fighter2 streamed on..."
    match = re.match(r'Watch the (?:UFC\s+\d+\s+showdown between\s+)?(.+?)\s+vs\.?\s+(.+?)\s+(?:bout\s+from\s+|streamed\s+on)', title)
    if match:
        result['fighter1'] = match.group(1).strip()
        result['fighter2'] = match.group(2).strip()
        # Try to get event name
        evt = re.search(r'(UFC\s+\d+|UFC Fight Night[^:]*)', title)
        if evt:
            result['event'] = evt.group(1).strip()
        return result
    
    # FORMAT 5: "Watch the Fighter1 vs. Fighter2 bout from EVENT from DATE in LOCATION"
    match = re.match(r'Watch the\s+(.+?)\s+vs\.?\s+(.+?)\s+bout\s+from\s+(.+?)(?:\s+from\s+|\s+streamed)', title)
    if match:
        result['fighter1'] = match.group(1).strip()
        result['fighter2'] = match.group(2).strip()
        result['event'] = match.group(3).strip()
        return result
    
    # FORMAT 6: Simple "Fighter1 vs. Fighter2"
    match = re.match(r'^(.+?)\s+vs\.?\s+(.+?)$', title)
    if match:
        result['fighter1'] = match.group(1).strip()
        result['fighter2'] = match.group(2).strip()
        return result
    
    return result

def main():
    print("UFC Paramount+ Fight Scraper")
    print("="*60)
    
    driver = setup_driver()
    all_fights = {}
    
    # Shows to scrape
    shows = [
        ('https://www.paramountplus.com/shows/ufc/', 'UFC (Numbered Events)'),
        ('https://www.paramountplus.com/shows/ufc-fight-night/', 'UFC Fight Night'),
        ('https://www.paramountplus.com/shows/ufc-2010s/', 'UFC 2010s'),
        ('https://www.paramountplus.com/shows/ufc-2000s/', 'UFC 2000s'),
    ]
    
    for show_url, show_name in shows:
        try:
            fights = scrape_show_page(driver, show_url, show_name)
            all_fights.update(fights)
            print(f"\n  Total unique fights so far: {len(all_fights)}")
        except Exception as e:
            print(f"\n  Error scraping {show_name}: {e}")
            continue
    
    driver.quit()
    
    # Build the final database
    fight_db = []
    for code, fight in all_fights.items():
        parsed = parse_fight_title(fight['title'])
        entry = {
            'code': code,
            'url': fight['url'],
            'title': fight['title'],
            'fighter1': parsed['fighter1'],
            'fighter2': parsed['fighter2'],
            'event': parsed['event'],
            'card': parsed['card']
        }
        fight_db.append(entry)
    
    # Sort by event name
    fight_db.sort(key=lambda x: x['event'], reverse=True)
    
    # Save to JSON file
    with open('paramount_fights.json', 'w', encoding='utf-8') as f:
        json.dump(fight_db, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*60}")
    print(f"SCRAPING COMPLETE!")
    print(f"Total fights found: {len(fight_db)}")
    print(f"Saved to: paramount_fights.json")
    print(f"{'='*60}")
    
    # Show some stats
    events = set(f['event'] for f in fight_db if f['event'])
    print(f"Unique events: {len(events)}")
    
    # Show a few examples
    print(f"\nSample entries:")
    for fight in fight_db[:5]:
        print(f"  {fight['fighter1']} vs {fight['fighter2']} ({fight['event']})")
        print(f"    URL: {fight['url']}")

if __name__ == '__main__':
    main()
