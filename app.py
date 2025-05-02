
from flask import Flask, render_template, request, jsonify
from yahoo_oauth import OAuth2
import json
import pandas as pd
from collections import defaultdict
import os

app = Flask(__name__, static_url_path='', static_folder='.', template_folder='.')

TEAM_NAME_TO_ABBR = {
    "arizona cardinals": "ARI", "atlanta falcons": "ATL", "baltimore ravens": "BAL", "buffalo bills": "BUF",
    "carolina panthers": "CAR", "chicago bears": "CHI", "cincinnati bengals": "CIN", "cleveland browns": "CLE",
    "dallas cowboys": "DAL", "denver broncos": "DEN", "detroit lions": "DET", "green bay packers": "GB",
    "houston texans": "HOU", "indianapolis colts": "IND", "jacksonville jaguars": "JAX", "kansas city chiefs": "KC",
    "las vegas raiders": "LV", "los angeles chargers": "LAC", "los angeles rams": "LAR", "miami dolphins": "MIA",
    "minnesota vikings": "MIN", "new england patriots": "NE", "new orleans saints": "NO", "new york giants": "NYG",
    "new york jets": "NYJ", "philadelphia eagles": "PHI", "pittsburgh steelers": "PIT", "san francisco 49ers": "SF",
    "seattle seahawks": "SEA", "tampa bay buccaneers": "TB", "tennessee titans": "TEN", "washington commanders": "WAS"
}

# Load fantasy points
points_url = "https://drive.google.com/uc?export=download&id=1gUsD8YS9_lPfyJtWs_eGKF9yBjkL2Mbj"
points_df = pd.read_csv(points_url)
points_df = points_df[['Player', 'Pos', 'Team', 'TTL'] + [str(i) for i in range(1, 19)]].dropna(subset=['Player', 'Pos', 'Team'])
points_df['Player'] = points_df['Player'].str.strip().str.lower()
points_df['Team'] = points_df['Team'].str.upper()
points_df['Pos'] = points_df['Pos'].str.upper()
player_points_lookup = {(row['Player'], row['Pos'], row['Team']): row for _, row in points_df.iterrows()}

def get_points(name, position, team):
    key = (name.lower().strip(), position.upper(), team.upper())
    row = player_points_lookup.get(key)
    if row is not None:
        ttl = row['TTL']
        all_scores = [float(row[str(w)]) for w in range(1, 19) if pd.notna(row[str(w)])]
        last_5_scores = [float(row[str(w)]) for w in range(14, 19) if pd.notna(row[str(w)])]
        return {
            "ttl": ttl,
            "overall_avg": round(sum(all_scores) / len(all_scores), 1) if all_scores else "N/A",
            "last5_avg": round(sum(last_5_scores) / len(last_5_scores), 1) if last_5_scores else "N/A"
        }
    return {"ttl": "N/A", "overall_avg": "N/A", "last5_avg": "N/A"}

def get_session():
    oauth_path = os.path.join(os.path.dirname(__file__), 'oauth2.json')
    sc = OAuth2(None, None, from_file=oauth_path)
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc.session

def fetch_game_keys(session):
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games"
    response = session.get(url, params={"format": "json"})
    if response.status_code != 200:
        return []
    try:
        data = response.json()
        user = data["fantasy_content"]["users"]["0"]["user"]
        games_container = next((section for section in user if isinstance(section, dict) and "games" in section), None)
        games = games_container["games"]
        return [games[key]["game"][0]["game_key"] for key in games if key.isdigit()]
    except Exception:
        return []

def fetch_league_keys(session, game_key):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys={game_key}/leagues"
    response = session.get(url, params={"format": "json"})
    if response.status_code != 200:
        return []
    try:
        data = response.json()
        game_list = data["fantasy_content"]["users"]["0"]["user"][1]["games"]["0"]["game"]
        leagues = game_list[1]["leagues"]
        return [leagues[key]["league"][0]["league_key"] for key in leagues if key.isdigit()]
    except Exception:
        return []

def fetch_players_from_league(session, league_key, team_filter=None, position_filter=None):
    base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;sort=AR"
    start, step = 0, 25
    categorized = defaultdict(list)

    while True:
        url = f"{base_url};count={step};start={start}"
        response = session.get(url, params={"format": "json"})
        if response.status_code != 200:
            break
        data = response.json()
        try:
            players = data["fantasy_content"]["league"][1].get("players", {})
            if not any(key.isdigit() for key in players):
                break
            for key in players:
                if not key.isdigit():
                    continue
                player_data = {}
                for item in players[key]["player"]:
                    if isinstance(item, dict):
                        player_data.update(item)
                name = player_data.get("name", {}).get("full", "N/A")
                team = player_data.get("editorial_team_abbr", "N/A").upper()
                position = player_data.get("primary_position", player_data.get("display_position", "N/A"))
                if team_filter and team != team_filter:
                    continue
                if position_filter and position.upper() != position_filter.upper():
                    continue
                stats = get_points(name, position, team)
                categorized[position].append({
                    "name": name,
                    "team": team,
                    "uniform_number": player_data.get("uniform_number", "N/A"),
                    "profile": player_data.get("url", ""),
                    "headshot": player_data.get("headshot", {}).get("url", ""),
                    "points": stats["ttl"],
                    "overall_avg": stats["overall_avg"],
                    "last5_avg": stats["last5_avg"]
                })
            start += step
        except Exception:
            break
    return categorized

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    return render_template('Search.html')

@app.route('/team')
def team():
    return render_template('Team.html')

@app.route('/api/players')
def api_players():
    team = request.args.get('team')
    position = request.args.get('position')
    session = get_session()
    all_data = defaultdict(list)
    for game_key in fetch_game_keys(session):
        for league_key in fetch_league_keys(session, game_key):
            data = fetch_players_from_league(session, league_key, team_filter=team, position_filter=position)
            for pos, players in data.items():
                all_data[pos].extend(players)
    return jsonify(all_data)

if __name__ == '__main__':
    app.run(debug=True)
