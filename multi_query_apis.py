import requests
import json

from line_apis import make_lines_dict

def tab_multi_query(proposition_ids):

    url = "https://api.beta.tab.com.au/v1/pricing-service/enquiry"
    propositions = []
    for id in proposition_ids:
        propositions.append({"type": "WIN", "propositionId": int(id)})

    payload = {
        "clientDetails": {
            "jurisdiction": "NSW",
            "channel": "web"
        },
        "bets": [
            {
                "type": "FIXED_ODDS",
                "legs": [
                    {
                        "type": "SAME_GAME_MULTI",
                        "propositions": propositions
                    }
                ]
            }
        ]
    }
    headers = {}
    response = requests.request("POST", url, headers=headers, json=payload)
    response_dict = json.loads(response.text)
    odds = float(response_dict['bets'][0]['legs'][0]['odds']['decimal'])

    return odds


def tab_multi_margin_sweep(lines_dict):
    line_levels = sorted(lines_dict.keys())
    results = []
    for i in range(len(line_levels)-1):
        for j in range(i+1, len(line_levels)):
            line_level_1 = line_levels[i]
            line_level_2 = line_levels[j]
            # print(line_level_1, line_level_2)
            if line_level_2 - line_level_1 < 1:
                continue
            line1 = lines_dict[line_level_1][1]
            line2 = lines_dict[line_level_2][0]
            # if (line1['market_type'] == line2['market_type']):
            #     continue    # TAB doesn't allow multiple legs from same market group
            try:
                odds = tab_multi_query([line1['id'], line2['id']])
            except:
                continue
            results.append({
                'home_line': line2,
                'away_line': line1,
                'price': odds,
            })
    return results
