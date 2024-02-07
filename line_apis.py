import requests
import json


def make_lines_dict(lines):
    """Maps home_line to [home_bet, away_bet]"""
    lines_dict = {}
    for line in lines:
        home_line = line['home_line']
        home_side = line['home_side']
        if home_line not in lines_dict:
            lines_dict[home_line] = [None, None]
        set_index = 0 if home_side else 1
        lines_dict[home_line][set_index] = line
    return lines_dict


def pointsbet_get_lines(market_id_str):
    session = requests.session()
    url = f'https://api.au.pointsbet.com/api/mes/v3/events/{market_id_str}'
    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    response = session.request("GET", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)

    market_dicts = response_dict['fixedOddsMarkets']

    home_team = response_dict['homeTeam']
    away_team = response_dict['awayTeam']

    lines = []
    for market_dict in market_dicts:
        if market_dict['eventClass'] == 'Moneyline' or market_dict['eventClass'] == 'Point Spread' or market_dict['eventClass'] == 'Pick Your Own Line':
            outcome_dicts = market_dict['outcomes']
            for outcome_dict in outcome_dicts:
                home_side = outcome_dict['side'] == 'Home'
                home_line = outcome_dict['points'] if home_side else -outcome_dict['points']
                lines.append({
                    'home_line': home_line,
                    'home_side': home_side,
                    'price': outcome_dict['price'],
                    'market_type': market_dict['eventClass'],
                })

    return (home_team, away_team), lines


def tab_get_lines(match_str, jurisdiction='NSW'):
    url = f'https://api.beta.tab.com.au/v1/tab-info-service/sports/Basketball/competitions/NBA/matches/{match_str}?jurisdiction={jurisdiction}'
    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)
    teams = response_dict['competitors']
    market_dicts = response_dict['markets']

    lines = []
    for market_dict in market_dicts:
        if market_dict['betOption'] == 'Head To Head' or market_dict['betOption'] == 'Line' or market_dict['betOption'] == 'Pick Your Own Line':
            outcome_dicts = market_dict['propositions']
            for outcome_dict in outcome_dicts:
                team_line = outcome_dict['name']
                split = team_line.split(' ')
                if market_dict['betOption'] == 'Head To Head':
                    line = 0
                    team = team_line
                else:
                    line = float(split[-1])
                    team = ' '.join(split[0:-1])
                home_line = line if team == teams[0] else -line

                lines.append({
                    'home_line': home_line,
                    'home_side': team == teams[0],
                    'price': outcome_dict['returnWin'],
                    'id': outcome_dict['id'],
                    'market_type': market_dict['betOption'],
                })

    return (teams[0], teams[1]), lines


def neds_get_lines(event_id_str):
    session = requests.session()
    url = f'https://api.neds.com.au/v2/sport/event-card?id={event_id_str}'
    payload = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    headers = {
        'authority': 'api.neds.com.au',
        'accept': '*/*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'if-modified-since': 'Sun, 04 Feb 2024 09:49:08 GMT',
        'origin': 'https://www.neds.com.au',
        'referer': 'https://www.neds.com.au/',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    }
    response = session.request("GET", url, headers=headers, data=payload)
    response_dict = json.loads(response.text)

    teams = [None, None]
    assert len(response_dict['event_participants'].values()) == 2
    for team_dict in response_dict['event_participants'].values():
        if team_dict['home_away'] == 'HOME':
            teams[0] = team_dict['name']
        else:
            teams[1] = team_dict['name']
    assert None not in teams

    market_type_mapping = {}
    market_types = set(['Alternate Lines'])

    for market_type_dict in response_dict['market_type_groups'].values():
        if market_type_dict['name'] in market_types:
            market_type_mapping[market_type_dict['id']] = market_type_dict['name']

    event_ids = response_dict['events'].keys()
    assert len(event_ids) == 1
    event_id = list(event_ids)[0]

    lines = []

    price_map = {}
    for key, odds_dict in response_dict['prices'].items():
        odds = (odds_dict['odds']['numerator'] + odds_dict['odds']['denominator']) / odds_dict['odds']['denominator']
        entrant_id = key.split(':')[0]
        price_map[entrant_id] = odds

    for market_group in response_dict['events'][event_id]['market_type_group_markets']:
        if market_group['market_type_group_id'] in market_type_mapping:
            for market_id in market_group['market_ids']:
                entrant_ids = response_dict['markets'][market_id]['entrant_ids']
                for entrant_id in entrant_ids:
                    entrant_dict = response_dict['entrants'][entrant_id]
                    odds = price_map[entrant_id]
                    team_line = entrant_dict['name']
                    split = team_line.split(' ')
                    line = float(split[-1])
                    team = ' '.join(split[:-1])
                    home_side = team == teams[0]
                    lines.append({
                        'home_line': line if home_side else -line,
                        'home_side': home_side,
                        'price': odds,
                    })


    remaining_market_types = set(['Head To Head', 'Line'])

    for market_dict in response_dict['markets'].values():
        if market_dict['name'] == 'Head To Head':
            for entrant_id in market_dict['entrant_ids']:
                entrant_dict = response_dict['entrants'][entrant_id]
                odds = price_map[entrant_id]
                home_side = entrant_dict['home_away'] == 'HOME'
                lines.append({
                    'home_line': 0,
                    'home_side': home_side,
                    'price': odds,
                })
            remaining_market_types.remove('Head To Head')

        if market_dict['name'] == 'Line':
            home_line = -market_dict['handicap']
            for entrant_id in market_dict['entrant_ids']:
                entrant_dict = response_dict['entrants'][entrant_id]
                odds = price_map[entrant_id]
                home_side = entrant_dict['home_away'] == 'HOME'
                lines.append({
                    'home_line': home_line,
                    'home_side': home_side,
                    'price': odds,
                })
            remaining_market_types.remove('Line')

        if len(remaining_market_types) == 0:
            break

    return teams, lines
    




if __name__ == '__main__':



    # _, lines = pointsbet_get_lines('1761691')
    # print(lines)

    # _, lines = tab_get_lines('Detroit%20v%20Orlando')
    # print(lines)

    _, lines = neds_get_lines('eeaf068d-0a07-4675-9a6c-f0d94748b96c')
    # print(lines)

    print(make_lines_dict(lines))