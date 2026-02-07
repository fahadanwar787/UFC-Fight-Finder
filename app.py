from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os
import re

app = Flask(__name__)

# =============================================================================
# Paramount+ Fight Database — maps fighter names to direct video URLs
# =============================================================================
class ParamountMatcher:
    """Matches UFC fights to Paramount+ video URLs using scraped data"""
    
    def __init__(self):
        self.fights = []
        self.load_database()
    
    def load_database(self):
        """Load the scraped Paramount+ fight database"""
        db_path = os.path.join(os.path.dirname(__file__), 'paramount_fights.json')
        if os.path.exists(db_path):
            with open(db_path, 'r', encoding='utf-8') as f:
                self.fights = json.load(f)
            # Filter out entries without fighter names
            self.fights = [f for f in self.fights if f.get('fighter1') and f.get('fighter2')]
            print(f"Loaded {len(self.fights)} Paramount+ fight links")
        else:
            print("WARNING: paramount_fights.json not found! Run scrape_paramount.py first.")
    
    @staticmethod
    def normalize(name):
        """Normalize a name for matching — lowercase, strip accents/punctuation"""
        name = name.lower().strip()
        # Remove common accent characters
        replacements = {'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
                        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
                        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                        'ñ': 'n', 'ç': 'c', 'ø': 'o', 'š': 's', 'ž': 'z'}
        for k, v in replacements.items():
            name = name.replace(k, v)
        # Remove non-alphanumeric (keep spaces)
        name = re.sub(r'[^a-z0-9 ]', '', name)
        return name
    
    @staticmethod
    def get_last_name(full_name):
        """Extract last name from a full name"""
        parts = full_name.strip().split()
        return parts[-1] if parts else ''
    
    @staticmethod
    def extract_event_number(event_name):
        """Extract UFC event number from event name like 'UFC 278: ...'"""
        match = re.search(r'UFC\s+(\d+)', event_name)
        return match.group(1) if match else ''
    
    def find_match(self, fighter_name, opponent_name, event_name=''):
        """Find the best matching Paramount+ video for a fight.
        Returns the video URL or None.
        """
        fighter_last = self.normalize(self.get_last_name(fighter_name))
        opponent_last = self.normalize(self.get_last_name(opponent_name))
        fighter_full = self.normalize(fighter_name)
        opponent_full = self.normalize(opponent_name)
        event_num = self.extract_event_number(event_name)
        
        if not fighter_last or not opponent_last:
            return None
        
        best_match = None
        best_score = 0
        
        for fight in self.fights:
            f1 = self.normalize(fight['fighter1'])
            f2 = self.normalize(fight['fighter2'])
            f1_last = self.normalize(self.get_last_name(fight['fighter1']))
            f2_last = self.normalize(self.get_last_name(fight['fighter2']))
            fight_event = fight.get('event', '')
            fight_event_num = self.extract_event_number(fight_event)
            
            score = 0
            
            # Check if both fighters match (in either order)
            fighters_match = False
            
            # Full name match (strongest)
            if (fighter_full in f1 or f1 in fighter_full) and (opponent_full in f2 or f2 in opponent_full):
                fighters_match = True
                score += 10
            elif (fighter_full in f2 or f2 in fighter_full) and (opponent_full in f1 or f1 in opponent_full):
                fighters_match = True
                score += 10
            # Last name match
            elif (fighter_last == f1_last and opponent_last == f2_last):
                fighters_match = True
                score += 5
            elif (fighter_last == f2_last and opponent_last == f1_last):
                fighters_match = True
                score += 5
            
            if not fighters_match:
                continue
            
            # Event number match (bonus)
            if event_num and fight_event_num and event_num == fight_event_num:
                score += 3
            
            # Prefer Main Card over Prelims
            card = fight.get('card', '')
            if 'Main' in card:
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = fight
        
        if best_match:
            return best_match['url']
        
        return None

paramount = ParamountMatcher()

class UFCFighterSearch:
    """Handles searching for UFC fighters and their fight history"""
    
    def __init__(self):
        self.base_url = "http://ufcstats.com"
        self.search_url = f"{self.base_url}/statistics/fighters/search"
        
    def search_fighter(self, fighter_name):
        """Search for a fighter by name"""
        try:
            # Search on UFC Stats website
            params = {
                'query': fighter_name
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                fighters = []
                
                # Find fighter links in the search results
                fighter_rows = soup.find_all('tr', class_='b-statistics__table-row')
                
                for row in fighter_rows[1:]:  # Skip header row
                    cols = row.find_all('td')
                    
                    if len(cols) >= 10:
                        # Column 0: First name
                        first_name_link = cols[0].find('a', class_='b-link')
                        # Column 1: Last name
                        last_name_link = cols[1].find('a', class_='b-link')
                        
                        if first_name_link and last_name_link:
                            # Get full name
                            first_name = first_name_link.text.strip()
                            last_name = last_name_link.text.strip()
                            full_name = f"{first_name} {last_name}"
                            fighter_url = first_name_link.get('href')
                            
                            # Build record from columns 7, 8, 9 (Wins, Losses, Draws)
                            wins = cols[7].text.strip()
                            losses = cols[8].text.strip()
                            draws = cols[9].text.strip()
                            record = f"{wins}-{losses}-{draws}"
                            
                            fighters.append({
                                'name': full_name,
                                'url': fighter_url,
                                'record': record
                            })
                
                return fighters
            
            return []
        except Exception as e:
            print(f"Error searching for fighter: {e}")
            return []
    
    def get_fighter_fights(self, fighter_url):
        """Get all fights for a specific fighter"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(fighter_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                fights = []
                
                # Find the fight history table
                fight_rows = soup.find_all('tr', class_='b-fight-details__table-row')
                
                # Get the fighter's name from the page
                fighter_name_elem = soup.find('span', class_='b-content__title-highlight')
                current_fighter = fighter_name_elem.text.strip() if fighter_name_elem else ""
                
                for row in fight_rows[1:]:  # Skip header
                    cols = row.find_all('td')
                    
                    if len(cols) >= 7:
                        # Column 0: W/L/D - SKIP THIS to avoid spoilers
                        # Column 1: Both fighters (current fighter and opponent)
                        # Column 6: Event name and date
                        
                        fighters_col = cols[1]
                        event_col = cols[6]
                        
                        # Get event info from column 6
                        event_link = event_col.find('a', class_='b-link')
                        date_elems = event_col.find_all('p', class_='b-fight-details__table-text')
                        
                        if event_link:
                            event_name = event_link.text.strip()
                            event_url = event_link.get('href', '')
                            event_date = date_elems[1].text.strip() if len(date_elems) > 1 else "Date Unknown"
                            
                            # Get opponent from column 1 (has both fighters)
                            fighter_links = fighters_col.find_all('a', class_='b-link')
                            opponent = "Unknown"
                            
                            if len(fighter_links) >= 2:
                                # Second link is the opponent
                                opponent = fighter_links[1].text.strip()
                            
                            fights.append({
                                'event': event_name,
                                'date': event_date,
                                'opponent': opponent,
                                'event_url': event_url
                            })
                
                return fights
            
            return []
        except Exception as e:
            print(f"Error getting fighter fights: {e}")
            return []
    
# Initialize the fighter search
ufc_search = UFCFighterSearch()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['GET'])
def search():
    """API endpoint to search for fighters"""
    fighter_name = request.args.get('name', '')
    
    if not fighter_name:
        return jsonify({'error': 'Please provide a fighter name'}), 400
    
    fighters = ufc_search.search_fighter(fighter_name)
    
    return jsonify({
        'fighters': fighters,
        'count': len(fighters)
    })

@app.route('/api/fights', methods=['GET'])
def get_fights():
    """API endpoint to get fights for a specific fighter"""
    fighter_url = request.args.get('url', '')
    
    if not fighter_url:
        return jsonify({'error': 'Please provide a fighter URL'}), 400
    
    fights = ufc_search.get_fighter_fights(fighter_url)
    
    return jsonify({
        'fights': fights,
        'count': len(fights)
    })


@app.route('/api/paramount-link', methods=['GET'])
def get_paramount_link():
    """API endpoint to find the direct Paramount+ video URL for a fight"""
    fighter = request.args.get('fighter', '')
    opponent = request.args.get('opponent', '')
    event = request.args.get('event', '')
    
    if not fighter or not opponent:
        return jsonify({'error': 'Please provide fighter and opponent names'}), 400
    
    url = paramount.find_match(fighter, opponent, event)
    
    if url:
        return jsonify({'url': url, 'found': True})
    else:
        # Fallback: construct a Paramount+ search URL
        event_clean = event.split(':')[0].strip() if event else ''
        search_query = f"{event_clean} {fighter} vs {opponent}".strip()
        fallback_url = f"https://www.paramountplus.com/search/?q={search_query}"
        return jsonify({'url': fallback_url, 'found': False})


if __name__ == '__main__':
    print("Starting UFC Fight Finder...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
