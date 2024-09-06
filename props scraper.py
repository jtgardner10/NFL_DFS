import requests
import pandas as pd

#API key from the-odds-api
API_KEY = '' #add your own API key

#Event IDs for all NFL games this week
event_ids = [
    '612c2c3f6ca9e10d4b7ead21a2b0ff38', 'eca3b71919531e7ae0b4f3f501157e6c',
    '7a5e353202d40a844491fa5753bc3097', '92665529cce6b8089e793d1e7d5e4b66',
    '022add645ca37d612dbb69e8ef02f6b9', 'b5b9d07cdd5c7bd14e943ccd7973e6a2',
    '5f14ebd3a8f10d141a7f0c2dcf510368', '60fdc65ee27ab7dbe07dc06ef35afadc',
    '8c0e75b0a4ea07212e741acf25ad96b6', 'c483f5c8e0ee5f1f5abdd75870eeeffc',
    'afb7e137dbb2a3de38d2d3cb68897e3b', 'a2f9dcdf49ccacf33036a0b795413a6e',
    'a1682ca5d9e0c4b14d19ed69d6299806', 'ba439e5505ce1ee745d2e48f2d2f31e6',
    'fa20351fa9ca26c47f93abc8a9b2c941', 'd94f808523ced7460f7c88c758c481f5'
]

#Base URL for fetching odds for a single event
url_template = 'https://api.the-odds-api.com/v4/sports/americanfootball_nfl/events/{event_id}/odds'

#Function to fetch odds for a single event from a specific bookmaker
def fetch_odds(event_id, api_key, bookmaker_name):
    url = url_template.format(event_id=event_id)
    params = {
        'apiKey': api_key,
        'regions': 'us',  
        'markets': 'player_pass_tds,player_pass_yds,player_rush_yds,player_receptions,player_reception_yds,player_anytime_td',
        'oddsFormat': 'american'
    }

    response = requests.get(url, params=params)

    #Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        #Filter for the specified bookmaker odds
        for bookmaker in data['bookmakers']:
            if bookmaker['title'] == bookmaker_name:
                return bookmaker
        return None
    else:
        print(f"Error: Unable to fetch data for event {event_id} from {bookmaker_name} (Status code: {response.status_code})")
        return None

#Helper function to extract market data for markets with Over/Under odds
def extract_market_data(market, market_source):
    market_data = {}
    
    for outcome in market['outcomes']:
        player_name = outcome.get('description', 'Unknown Player')
        odds = outcome.get('price', 'N/A')
        yard_value = outcome.get('point', None)

        if player_name not in market_data:
            market_data[player_name] = {
                'Player': player_name, 
                'Yardage': yard_value, 
                f'{market_source} Over Odds': None, 
                f'{market_source} Under Odds': None
            }

        if outcome['name'].lower() == 'over':
            market_data[player_name][f'{market_source} Over Odds'] = odds
        elif outcome['name'].lower() == 'under':
            market_data[player_name][f'{market_source} Under Odds'] = odds

    return list(market_data.values())

#Helper function to handle player_anytime_td market
def extract_anytime_td_data(market, market_source):
    anytime_td_data = []

    for outcome in market['outcomes']:
        player_name = outcome.get('description', 'Unknown Player')
        odds = outcome.get('price', 'N/A')

        anytime_td_data.append({
            'Player': player_name,
            f'{market_source} Odds': odds
        })

    return anytime_td_data

#Initialize a dictionary to store all market data across all events
market_sheets = {
    'player_receptions': [],
    'player_anytime_td': [],
    'player_pass_tds': [],
    'player_pass_yds': [],
    'player_rush_yds': [],
    'player_reception_yds': []
}

#Iterate over each event and fetch the player props odds for DraftKings and FanDuel
for event_id in event_ids:
    #Fetch DraftKings data
    draftkings_data = fetch_odds(event_id, API_KEY, 'DraftKings')
    #Fetch FanDuel data
    fanduel_data = fetch_odds(event_id, API_KEY, 'FanDuel')
    
    if draftkings_data:
        print(f"\nFetching DraftKings Odds for Event ID {event_id}:")
        for market in draftkings_data['markets']:
            market_key = market['key']
            if market_key == 'player_anytime_td':
                market_data = extract_anytime_td_data(market, 'DraftKings')
                market_sheets[market_key].extend(market_data)
            elif market_key in market_sheets:
                market_data = extract_market_data(market, 'DraftKings')
                market_sheets[market_key].extend(market_data)
    else:
        print(f"No DraftKings odds found for Event ID {event_id}.")
    
    if fanduel_data:
        print(f"\nFetching FanDuel Odds for Event ID {event_id}:")
        for market in fanduel_data['markets']:
            market_key = market['key']
            if market_key == 'player_receptions':  # Only fallback for player_receptions, due to DK not having any
                market_data = extract_market_data(market, 'FanDuel')
                market_sheets[market_key].extend(market_data)
    else:
        print(f"No FanDuel odds found for Event ID {event_id}.")

#Create a pandas Excel writer to save each market's data into its own sheet
with pd.ExcelWriter('nfl_player_props_odds_consolidated.xlsx', engine='openpyxl') as writer:
    #Loop through each market and create a DataFrame, then save it to the Excel sheet
    for market_key, market_data in market_sheets.items():
        df = pd.DataFrame(market_data)
        
        #Write to a specific sheet in the Excel file
        df.to_excel(writer, sheet_name=market_key, index=False)

print("Odds data has been successfully exported to 'nfl_player_props_odds_consolidated.xlsx'")
