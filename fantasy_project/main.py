from yahoo_oauth import OAuth2
import json
import pandas as pd
from collections import defaultdict

def pretty(data):
    print(json.dumps(data, indent=2))

def fetch_available_game_keys(session):
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games"
    params = {"format": "json"}
    response = session.get(url, params=params)

    if response.status_code != 200:
        print(f"Error fetching games: {response.status_code}")
        return []

    data = response.json()
    try:
        user = data["fantasy_content"]["users"]["0"]["user"]
        games_container = next((section for section in user if isinstance(section, dict) and "games" in section), None)
        if not games_container:
            print("No games found.")
            return []

        games = games_container["games"]
        game_keys = []
        for key in games:
            if key.isdigit():
                game_list = games[key]["game"]
                game = game_list[0] if isinstance(game_list, list) else game_list
                game_key = game["game_key"]
                season = game["season"]
                name = game["name"]
                print(f"🗓️ Season {season} | Game Key: {game_key} | Name: {name}")
                game_keys.append(game_key)

        return game_keys

    except Exception as e:
        print("Error parsing game data:", e)
        pretty(data)
        return []

def fetch_league_keys(session, game_key):
    url = f"https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys={game_key}/leagues"
    params = {"format": "json"}
    response = session.get(url, params=params)

    if response.status_code != 200:
        print(f"Error fetching leagues for game {game_key}: {response.status_code}")
        return []

    data = response.json()
    try:
        game_list = data["fantasy_content"]["users"]["0"]["user"][1]["games"]["0"]["game"]
        if isinstance(game_list, list) and len(game_list) > 1 and "leagues" in game_list[1]:
            leagues = game_list[1]["leagues"]
            league_keys = []
            for key in leagues:
                if key.isdigit():
                    league = leagues[key]["league"][0]
                    league_key = league["league_key"]
                    name = league["name"]
                    print(f"🏈 League: {name} | Key: {league_key}")
                    league_keys.append(league_key)
            return league_keys
        else:
            print("No leagues found in game object.")
            pretty(game_list)
            return []

    except Exception as e:
        print("Error parsing league data:", e)
        pretty(data)
        return []

def fetch_players_from_league(session, league_key, team_filter=None, position_filter=None, points_lookup=None):
    base_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league_key}/players;sort=AR"
    start = 0
    step = 25
    categorized = defaultdict(list)

    while True:
        url = f"{base_url};count={step};start={start}"
        params = {"format": "json"}
        response = session.get(url, params=params)

        if response.status_code != 200:
            print(f"Error fetching players from start {start}: {response.status_code}")
            break

        data = response.json()
        try:
            league_data = data["fantasy_content"]["league"]
            if len(league_data) < 2 or "players" not in league_data[1]:
                print("✅ Reached end of player list.")
                break

            players = league_data[1]["players"]
            if not any(k.isdigit() for k in players):
                print("✅ No more digit-keyed players — done.")
                break

            for key in players:
                if not key.isdigit():
                    continue
                player_wrapper = players[key]["player"]
                if isinstance(player_wrapper, list) and len(player_wrapper) == 1:
                    player_wrapper = player_wrapper[0]

                player_data = {}
                for entry in player_wrapper:
                    if isinstance(entry, dict):
                        player_data.update(entry)

                name = player_data.get("name", {}).get("full", "N/A")
                team = player_data.get("editorial_team_abbr", "N/A").upper()
                position = player_data.get("primary_position", player_data.get("display_position", "N/A"))
                uniform_number = player_data.get("uniform_number", "N/A")
                bye_week = player_data.get("bye_weeks", {}).get("week", "N/A")
                profile_url = player_data.get("url", "")
                headshot = player_data.get("headshot", {}).get("url", "")

                # Apply filters
                if team_filter and team.lower() != team_filter.lower():
                    continue
                if position_filter and position.upper() != position_filter.upper():
                    continue

                # Look up points if function provided
                points = points_lookup(name, position, team) if points_lookup else "N/A"

                categorized[position].append({
                    "name": name,
                    "team": team,
                    "uniform_number": uniform_number,
                    "bye_week": bye_week,
                    "profile": profile_url,
                    "headshot": headshot,
                    "points": points
                })

            start += step

        except Exception as e:
            print("Error parsing player data at start", start, ":", e)
            pretty(data)
            break

    print(f"\n👥 Players in League {league_key} (Grouped by Position):\n{'='*60}")
    if not categorized:
        print("No players match the specified filter.\n")
        return

    for position in sorted(categorized):
        print(f"\n🔸 Position: {position}\n{'-'*40}")
        for player in categorized[position]:
            print(f"{player['name']} – {player['team']} | #: {player['uniform_number']} | Bye: {player['bye_week']}")
            print(f"  Fantasy Points: {player['points']}")
            print(f"  Profile: {player['profile']}")
            print(f"  Headshot: {player['headshot']}\n")

def main():
    # Load and clean fantasy points data from Google Drive
    try:
        file_id = "1gUsD8YS9_lPfyJtWs_eGKF9yBjkL2Mbj"
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        points_df = pd.read_csv(url)
        points_df = points_df[['Player', 'Pos', 'Team', 'TTL']].dropna()
        points_df['Player'] = points_df['Player'].str.strip().str.lower()
        points_df['Team'] = points_df['Team'].str.upper()
        points_df['Pos'] = points_df['Pos'].str.upper()
    except Exception as e:
        print("❌ Failed to load Fantasy Points file:", e)
        return

    # Build a lookup dictionary: (name, position, team) → total points
    player_points_lookup = {
        (row['Player'], row['Pos'], row['Team']): row['TTL']
        for _, row in points_df.iterrows()
    }

    # OAuth
    sc = OAuth2(None, None, from_file='oauth2.json')
    if not sc.token_is_valid():
        sc.refresh_access_token()
    session = sc.session

    print("🎯 Fetching Game Keys")
    game_keys = fetch_available_game_keys(session)

    # Ask for filters
    print("\n🔍 Optional: Filter players")
    team_filter = input("Enter a team name (e.g., San Francisco 49ers), or leave blank: ").strip()
    position_filter = input("Enter a position (e.g., QB, RB, WR), or leave blank: ").strip()

    # Helper function for looking up total points
    def get_points(name, position, team):
        key = (name.lower().strip(), position.upper(), team.upper())
        return player_points_lookup.get(key, "N/A")

    for game_key in game_keys:
        print(f"\n🔍 Checking leagues for game {game_key}")
        league_keys = fetch_league_keys(session, game_key)
        for league_key in league_keys:
            fetch_players_from_league(
                session,
                league_key,
                team_filter=team_filter if team_filter else None,
                position_filter=position_filter if position_filter else None,
                points_lookup=get_points
            )

if __name__ == "__main__":
    main()
