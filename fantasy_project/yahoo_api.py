import os
import pandas as pd
from yahoo_oauth import OAuth2
from collections import defaultdict

TEAM_NAME_TO_ABBR = {
    "arizona cardinals": "ARI", "atlanta falcons": "ATL", "baltimore ravens": "BAL",
    "buffalo bills": "BUF", "carolina panthers": "CAR", "chicago bears": "CHI",
    "cincinnati bengals": "CIN", "cleveland browns": "CLE", "dallas cowboys": "DAL",
    "denver broncos": "DEN", "detroit lions": "DET", "green bay packers": "GB",
    "houston texans": "HOU", "indianapolis colts": "IND", "jacksonville jaguars": "JAX",
    "kansas city chiefs": "KC", "las vegas raiders": "LV", "los angeles chargers": "LAC",
    "los angeles rams": "LAR", "miami dolphins": "MIA", "minnesota vikings": "MIN",
    "new england patriots": "NE", "new orleans saints": "NO", "new york giants": "NYG",
    "new york jets": "NYJ", "philadelphia eagles": "PHI", "pittsburgh steelers": "PIT",
    "san francisco 49ers": "SF", "seattle seahawks": "SEA", "tampa bay buccaneers": "TB",
    "tennessee titans": "TEN", "washington commanders": "WAS"
}


def fetch_available_game_keys(session):
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games"
    params = {"format": "json"}
    resp = session.get(url, params=params)
    resp.raise_for_status()

    data = resp.json()["fantasy_content"]["users"]["0"]["user"]
    games_section = next((sec for sec in data if isinstance(sec, dict) and "games" in sec), None)
    if not games_section:
        return []

    game_entries = games_section["games"]
    keys = []
    for k, v in game_entries.items():
        if k.isdigit():
            game = v["game"][0] if isinstance(v["game"], list) else v["game"]
            keys.append(game["game_key"])
    return keys


def fetch_league_keys(session, game_key):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys={game_key}/leagues"
    params = {"format": "json"}
    resp = session.get(url, params=params)
    resp.raise_for_status()

    game_list = resp.json()["fantasy_content"]["users"]["0"]["user"][1]["games"]["0"]["game"]
    leagues_part = game_list[1].get("leagues") if isinstance(game_list, list) and len(game_list) > 1 else None
    if not leagues_part:
        return []

    keys = []
    for k, v in leagues_part.items():
        if k.isdigit():
            league = v["league"][0]
            keys.append(league["league_key"])
    return keys


def fetch_players_from_league(session, league_key, team_filter=None, position_filter=None, points_lookup=None):
    base = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;sort=AR"
    start, step = 0, 25
    players = []

    while True:
        url = f"{base};count={step};start={start}"
        resp = session.get(url, params={"format": "json"})
        resp.raise_for_status()

        content = resp.json()["fantasy_content"]["league"]
        if len(content) < 2 or "players" not in content[1]:
            break

        entries = content[1]["players"]
        digit_keys = [k for k in entries if k.isdigit()]
        if not digit_keys:
            break

        for k in digit_keys:
            node = entries[k]["player"]
            if isinstance(node, list):
                node = node[0]
            info = {}
            for part in node:
                if isinstance(part, dict):
                    info.update(part)

            name = info.get("name", {}).get("full", "N/A")
            team = info.get("editorial_team_abbr", "N/A").upper()
            pos  = info.get("primary_position", info.get("display_position", "N/A"))

            if team_filter and team != team_filter:
                continue
            if position_filter and pos.upper() != position_filter.upper():
                continue

            pts = "N/A"
            if points_lookup:
                lookup = points_lookup(name, pos, team)
                pts = lookup.get("ttl", "N/A")

            players.append({
                "name": name,
                "team": team,
                "position": pos,
                "points": pts,
                "profile": info.get("url", ""),
                "headshot": info.get("headshot", {}).get("url", "")
            })

        start += step
    return players


def get_all_players(team_filter=None, position_filter=None):
    csv_url = (
        "https://drive.google.com/uc?export=download"
        "&id=1gUsD8YS9_lPfyJtWs_eGKF9yBjkL2Mbj"
    )
    df = pd.read_csv(csv_url)
    df = df[['Player','Pos','Team','TTL'] + [str(i) for i in range(1,19)]].dropna(subset=['Player','Pos','Team'])
    df['Player'] = df['Player'].str.strip().str.lower()
    df['Team']   = df['Team'].str.upper()
    df['Pos']    = df['Pos'].str.upper()

    points_lookup = {
        (row['Player'], row['Pos'], row['Team']): row
        for _, row in df.iterrows()
    }

    def get_points(name, pos, team):
        key = (name.lower().strip(), pos.upper(), team.upper())
        row = points_lookup.get(key)
        if row is None:
            return {"ttl":"N/A","overall_avg":"N/A","last5_avg":"N/A"}

        ttl = row['TTL']
        scores = []
        for week in range(1,19):
            val = row.get(str(week))
            try:
                num = float(val)
                scores.append(num)
            except (TypeError, ValueError):
                continue
        overall_avg = round(sum(scores)/len(scores),1) if scores else "N/A"

        recent = scores[-5:] if len(scores) >= 5 else scores
        last5_avg = round(sum(recent)/len(recent),1) if recent else "N/A"

        return {"ttl":ttl, "overall_avg":overall_avg, "last5_avg":last5_avg}

    # OAuth2 session
    oauth_path = os.path.join(os.path.dirname(__file__), 'oauth2.json')
    sc = OAuth2(None, None, from_file=oauth_path)
    if not sc.token_is_valid():
        sc.refresh_access_token()
    session = sc.session

    all_players = []
    for game_key in fetch_available_game_keys(session):
        for league_key in fetch_league_keys(session, game_key):
            all_players.extend(
                fetch_players_from_league(
                    session,
                    league_key,
                    team_filter=team_filter,
                    position_filter=position_filter,
                    points_lookup=get_points
                )
            )
    return all_players