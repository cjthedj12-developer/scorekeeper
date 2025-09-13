import streamlit as st
import pandas as pd
import json
import os

SAVE_FILE = "scoreboard.json"
NEWS_FILE = "news.json"
TEAMS_FILE = "teams.json"

# --- Login ---
USERNAME = "admin"
PASSWORD = "1234"  # Change this to your own password

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
scoreboard = load_json(SAVE_FILE, {
    "Nord 2025 Season": {
        "Senior D1 Nord": [],
        "Sophomore D1 Nord": [],
        "Sophomore D2 Nord": []
    }
})
news_feed = load_json(NEWS_FILE, [])
teams = load_json(TEAMS_FILE, {
    "Senior D1 Nord": [],
    "Sophomore D1 Nord": [],
    "Sophomore D2 Nord": []
})

# --- App Title ---
st.title("🏈 Scorekeeper App")

# --- Select Season & Division ---
# Default season = Nord 2025 Season
season_list = list(scoreboard.keys())
if "Nord 2025 Season" not in season_list:
    season_list.insert(0, "Nord 2025 Season")

selected_season = st.selectbox("Season", season_list, index=season_list.index("Nord 2025 Season"))
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

    for team in [home, away]:
        if team not in standings:
            standings[team] = {"Wins": 0, "Losses": 0, "Points For": 0, "Points Against": 0}

    standings[home]["Points For"] += hs
    standings[home]["Points Against"] += as_
    standings[away]["Points For"] += as_
    standings[away]["Points Against"] += hs

    if hs > as_:
        standings[home]["Wins"] += 1
        standings[away]["Losses"] += 1
    elif as_ > hs:
        standings[away]["Wins"] += 1
        standings[home]["Losses"] += 1

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
        by=["Wins", "Diff"], ascending=[False, False]
    ).reset_index(drop=True)
    rank_df.index = rank_df.index + 1
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
    if username == USERNAME and password == PASSWORD:
        st.session_state.logged_in = True
        st.sidebar.success("Logged in!")
    else:
        st.sidebar.error("Wrong username or password")

# --- Admin Mode ---
if st.session_state.logged_in:
    st.sidebar.subheader("Admin Mode")

    # --- Add / Change Season ---
    st.subheader("➕ Create New Season")
    new_season = st.text_input("New Season Name (e.g. 2026 Season)")
    if st.button("Add Season"):
        if new_season.strip() and new_season.strip() not in scoreboard:
            scoreboard[new_season.strip()] = {
                "Senior D1 Nord": [],
                "Sophomore D1 Nord": [],
                "Sophomore D2 Nord": []
            }
            save_json(SAVE_FILE, scoreboard)
            st.success(f"Season '{new_season}' created!")
        elif new_season.strip() in scoreboard:
            st.warning("Season already exists!")

    # --- Add Team ---
    st.subheader("➕ Add a Team")
    new_team = st.text_input("Team Name")
    if st.button("Add Team"):
        if new_team.strip() and new_team.strip() not in teams[division]:
            teams[division].append(new_team.strip())
            save_json(TEAMS_FILE, teams)
            st.success(f"Team '{new_team}' added to {division}!")
        elif new_team.strip() in teams[division]:
            st.warning("Team already exists!")

    # --- Add Game ---
    st.subheader("➕ Add a Game")
    if teams[division]:
        home_team = st.selectbox("Home Team", teams[division], key="home")
        away_team = st.selectbox("Away Team", teams[division], key="away")
    else:
        home_team = st.text_input("Home Team")
        away_team = st.text_input("Away Team")

    home_score = st.number_input("Home Score", value=0)
    away_score = st.number_input("Away Score", value=0)

    if st.button("Add Game Score"):
        scoreboard[selected_season][division].append({
            "Home": home_team,
            "Away": away_team,
            "HomeScore": home_score,
            "AwayScore": away_score
        })
        save_json(SAVE_FILE, scoreboard)
        st.success("Game added!")

    # --- Post News ---
    st.subheader("📰 Post News")
    new_post = st.text_input("Write a news update")
    if st.button("Post News"):
        if new_post.strip():
            news_feed.append(new_post.strip())
            save_json(NEWS_FILE, news_feed)
            st.success("News posted!")
