import streamlit as st
import pandas as pd
import json
import os

SAVE_FILE = "scoreboard.json"
NEWS_FILE = "news.json"
TEAMS_FILE = "teams.json"

# --- Login ---
USERNAME = "admin"
PASSWORD = "1981"  # Change to your own password

# --- Load / Save Functions ---
def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

# --- Load Data ---
scoreboard = load_json(SAVE_FILE, {})
news_feed = load_json(NEWS_FILE, [])
teams = load_json(TEAMS_FILE, {})

# --- Defaults ---
DEFAULT_DIVISIONS = ["Senior D1 Nord", "Sophomore D1 Nord", "Sophomore D2 Nord"]
DEFAULT_SEASON = "Nord 2025 Season"

# --- Ensure default season/divisions exist ---
if DEFAULT_SEASON not in scoreboard:
    scoreboard[DEFAULT_SEASON] = {div: [] for div in DEFAULT_DIVISIONS}

for season_name in scoreboard.keys():
    for div in DEFAULT_DIVISIONS:
        if div not in scoreboard[season_name]:
            scoreboard[season_name][div] = []
        if div not in teams:
            teams[div] = []

# --- App Title ---
st.title("🏈 Scorekeeper App")

# --- Select Season & Division for Viewing ---
season_list = list(scoreboard.keys())
if DEFAULT_SEASON not in season_list:
    season_list.insert(0, DEFAULT_SEASON)

selected_season = st.selectbox("Season", season_list, index=season_list.index(DEFAULT_SEASON))
division = st.selectbox("Division", list(scoreboard[selected_season].keys()))

# --- Public View: Scoreboard ---
st.header("📊 Scoreboard")
games = scoreboard[selected_season][division]
if games:
    df = pd.DataFrame(games)
    st.dataframe(df)
else:
    st.write("No games yet.")

# --- Rankings (Wins, then Points Differential) ---
st.header("🏆 Rankings")
standings = {}
for game in games:
    home, away = game["Home"], game["Away"]
    hs, as_ = game["HomeScore"], game["AwayScore"]
    status = game.get("Status","Upcoming")

    # Only count Wins/Losses for Final games
    if status == "Final":
        for team in [home, away]:
            if team not in standings:
                standings[team] = {"Wins":0, "Losses":0,"Points For":0,"Points Against":0}

        standings[home]["Points For"] += hs
        standings[home]["Points Against"] += as_
        standings[away]["Points For"] += as_
        standings[away]["Points Against"] += hs

        if hs>as_:
            standings[home]["Wins"] += 1
            standings[away]["Losses"] +=1
        elif as_>hs:
            standings[away]["Wins"] +=1
            standings[home]["Losses"] +=1
    else:
        for team in [home, away]:
            if team not in standings:
                standings[team] = {"Wins":0,"Losses":0,"Points For":0,"Points Against":0}
        standings[home]["Points For"] += hs
        standings[home]["Points Against"] += as_
        standings[away]["Points For"] += as_
        standings[away]["Points Against"] += hs

rank_data = []
for team, stats in standings.items():
    diff = stats["Points For"] - stats["Points Against"]
    rank_data.append({
        "Team": team,
        "Wins": stats["Wins"],
        "Losses": stats["Losses"],
        "Points For": stats["Points For"],
        "Points Against": stats["Points Against"],
        "Diff": diff
    })

if rank_data:
    rank_df = pd.DataFrame(rank_data).sort_values(
        by=["Wins","Diff"], ascending=[False, False]
    ).reset_index(drop=True)
    rank_df.index = rank_df.index+1
    st.dataframe(rank_df)
else:
    st.write("No rankings yet.")

# --- News Feed ---
st.header("📰 News Feed")
if news_feed:
    for item in news_feed[::-1]:
        st.write(f"- {item}")
else:
    st.write("No news yet.")

# --- Sidebar: Admin Login ---
st.sidebar.header("🔑 Admin Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login = st.sidebar.button("Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if login:
    if username==USERNAME and password==PASSWORD:
        st.session_state.logged_in=True
        st.sidebar.success("Logged in!")
    else:
        st.sidebar.error("Wrong username or password")

# --- Admin Mode ---
if st.session_state.logged_in:
    st.sidebar.subheader("Admin Mode")

    # --- Add / Change Season ---
    st.subheader("➕ Create New Season")
    new_season = st.text_input("New Season Name")
    if st.button("Add Season"):
        if new_season.strip() and new_season.strip() not in scoreboard:
            scoreboard[new_season.strip()] = {div: [] for div in DEFAULT_DIVISIONS}
            save_json(SAVE_FILE, scoreboard)
            st.success(f"Season '{new_season}' created!")
        elif new_season.strip() in scoreboard:
            st.warning("Season already exists!")

    # --- Add Team by Division ---
    st.subheader("➕ Add a Team")
    new_team = st.text_input("Team Name")
    team_div = st.selectbox("Select Division for Team", DEFAULT_DIVISIONS)
    if st.button("Add Team"):
        if new_team.strip() and new_team.strip() not in teams[team_div]:
            teams[team_div].append(new_team.strip())
            save_json(TEAMS_FILE, teams)
            st.success(f"Team '{new_team}' added to {team_div}!")
        elif new_team.strip() in teams[team_div]:
            st.warning("Team already exists!")

    # --- Add / Edit Game (with Division Selection) ---
    st.subheader("➕ Add / Edit a Game")
    game_div = st.selectbox("Select Division for Game", DEFAULT_DIVISIONS)
    game_list = scoreboard[selected_season][game_div]
    game_options = [f"{g['Home']} vs {g['Away']} ({g.get('Status','Upcoming')})" for g in game_list]
    selected_game_index = st.selectbox("Select Game to Edit (or New)", [-1]+list(range(len(game_list))),
                                       format_func=lambda x:"New Game" if x==-1 else game_options[x])
    
    if selected_game_index==-1:
        # Add new game
        if teams[game_div]:
            home_team = st.selectbox("Home Team", teams[game_div], key="new_home")
            away_team = st.selectbox("Away Team", teams[game_div], key="new_away")
        else:
            home_team = st.text_input("Home Team")
            away_team = st.text_input("Away Team")
        home_score = st.number_input("Home Score", value=0, key="new_hs")
        away_score = st.number_input("Away Score", value=0, key="new_as")
        status = st.selectbox("Game Status", ["Upcoming","Live","Final"], key="new_status")
        if st.button("Add Game"):
            scoreboard[selected_season][game_div].append({
                "Home": home_team,
                "Away": away_team,
                "HomeScore": home_score,
                "AwayScore": away_score,
                "Status": status
            })
            save_json(SAVE_FILE, scoreboard)
            st.success("Game added!")
    else:
        # Edit existing game
        game = game_list[selected_game_index]
        home_team = st.text_input("Home Team", value=game["Home"], key="edit_home")
        away_team = st.text_input("Away Team", value=game["Away"], key="edit_away")
        home_score = st.number_input("Home Score", value=game["HomeScore"], key="edit_hs")
        away_score = st.number_input("Away Score", value=game["AwayScore"], key="edit_as")
        status = st.selectbox("Game Status", ["Upcoming","Live","Final"], index=["Upcoming","Live","Final"].index(game.get("Status","Upcoming")), key="edit_status")
        if st.button("Update Game"):
            game_list[selected_game_index].update({
                "Home": home_team,
                "Away": away_team,
                "HomeScore": home_score,
                "AwayScore": away_score,
                "Status": status
            })
            save_json(SAVE_FILE, scoreboard)
            st.success("Game updated!")

    # --- Post News ---
    st.subheader("📰 Post News")
    new_post = st.text_input("Write a news update")
    if st.button("Post News"):
        if new_post.strip():
            news_feed.append(new_post.strip())
            save_json(NEWS_FILE, news_feed)
            st.success("News posted!")
