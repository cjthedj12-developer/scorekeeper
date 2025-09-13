import streamlit as st
import pandas as pd
import json
import os

SAVE_FILE = "scoreboard.json"
NEWS_FILE = "news.json"

# --- Load Data ---
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"2025 Spring": {"Division A": [], "Division B": []}}

def save_data(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r") as f:
            return json.load(f)
    return []

def save_news(news):
    with open(NEWS_FILE, "w") as f:
        json.dump(news, f)

# --- App Start ---
st.title("🏈 Scorekeeper App")

scoreboard = load_data()
news_feed = load_news()

# Pick season/division
season = st.selectbox("Season", list(scoreboard.keys()))
division = st.selectbox("Division", list(scoreboard[season].keys()))

st.subheader("➕ Add a Game")
home = st.text_input("Home Team")
away = st.text_input("Away Team")
home_score = st.number_input("Home Score", value=0)
away_score = st.number_input("Away Score", value=0)

if st.button("Add Game"):
    scoreboard[season][division].append({
        "Home": home, "Away": away,
        "HomeScore": home_score, "AwayScore": away_score
    })
    save_data(scoreboard)
    st.success("Game added!")

# Show scoreboard
st.subheader("📊 Scoreboard")
if scoreboard[season][division]:
    df = pd.DataFrame(scoreboard[season][division])
    st.dataframe(df)
else:
    st.write("No games yet.")

# Rankings
st.subheader("🏆 Rankings")
standings = {}
for game in scoreboard[season][division]:
    if game["Home"] not in standings:
        standings[game["Home"]] = {"Wins": 0, "Losses": 0}
    if game["Away"] not in standings:
        standings[game["Away"]] = {"Wins": 0, "Losses": 0}

    if game["HomeScore"] > game["AwayScore"]:
        standings[game["Home"]]["Wins"] += 1
        standings[game["Away"]]["Losses"] += 1
    elif game["AwayScore"] > game["HomeScore"]:
        standings[game["Away"]]["Wins"] += 1
        standings[game["Home"]]["Losses"] += 1

rank_df = pd.DataFrame([
    {"Team": t, "Wins": s["Wins"], "Losses": s["Losses"]}
    for t, s in standings.items()
]).sort_values(by=["Wins", "Losses"], ascending=[False, True])

if not rank_df.empty:
    st.dataframe(rank_df)
else:
    st.write("No rankings yet.")

# News Feed
st.subheader("📰 News Feed")
for item in news_feed[::-1]:
    st.write(f"- {item}")

new_post = st.text_input("Write a news update")
if st.button("Post News"):
    if new_post.strip():
        news_feed.append(new_post.strip())
        save_news(news_feed)
        st.success("News posted!")
