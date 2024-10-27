import openai
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt


openai.api_key = "your-api-key"  # Replace with your actual API key

# Initialize SQLite database
conn = sqlite3.connect('tennis_app.db')
cursor = conn.cursor()

# Create the players table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,  -- Make 'name' unique to avoid duplicates
        utr REAL,
        preferred_format TEXT,
        first_serve_percentage INTEGER,
        winners INTEGER,
        unforced_error_percentage INTEGER,
        win_rate INTEGER,
        double_faults INTEGER
    )
''')
conn.commit()

# Function to save player data to SQLite
def save_player_to_db(player_data):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO players (name, utr, preferred_format, first_serve_percentage, winners, 
                                           unforced_error_percentage, win_rate, double_faults)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            player_data["Name"], player_data["UTR"], player_data["Preferred Format"],
            player_data["First Serve %"], player_data["Winners"], player_data["Unforced Error %"],
            player_data["Win Rate %"], player_data["Double Faults"]
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass

# Function to retrieve all players from SQLite
def get_players_from_db():
    cursor.execute("SELECT * FROM players")
    rows = cursor.fetchall()
    players = [
        {
            "ID": row[0],
            "Name": row[1],
            "UTR": row[2],
            "Preferred Format": row[3],
            "First Serve %": row[4],
            "Winners": row[5],
            "Unforced Error %": row[6],
            "Win Rate %": row[7],
            "Double Faults": row[8]
        }
        for row in rows
    ]
    return players

# Function to delete a player from SQLite by ID
def delete_player_from_db(player_id):
    cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()

# Function to get AI-based pairing suggestions
def get_ai_pairing_suggestions(players):
    messages = [{"role": "system", "content": "You are a tennis pairing expert."}]
    
    prompt = "Create a tennis team line-up based on their qualities: UTR, preferred format, first serve percentage, winners, unforced error percentage, win rate, and double faults. Make sure that you are always outputting the lineup in the same format. It should be like this:(2 New lines) -Singles 1: “Player Name” (new line) -Singles 2: “Player Name” etc. (2 new lines) -Doubles 1: “Player Name & Player Name”(New line) -Doubles 2: “Player Name & Player Name” etc. (2 new lines)(if there are extra players you could also possibly make substitutions combos). Then after you list them out like that make sure to offer a straightforward and simple explanation to the lineup.\n Here is the list of players:"
    
    # Add player information to the prompt
    for player in players:
        prompt += (f"Name: {player['Name']}, UTR: {player['UTR']}, Format: {player['Preferred Format']}, "
                   f"First Serve %: {player['First Serve %']}, Winners: {player['Winners']}, "
                   f"Unforced Error %: {player['Unforced Error %']}, Win Rate %: {player['Win Rate %']}, "
                   f"Double Faults: {player['Double Faults']}\n")
        
        prompt += "Number of sinlges players: " + singles + "Number of doubles pairs: " + doubles
    
    messages.append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# App title and description
st.title("CourtBot")
st.subheader("Add Players and Find Optimal Pairings using AI")

# CSV Template for users to download with two example players and up to 20 rows
def create_csv_template():
    template = pd.DataFrame({
        "Name": ["Player1", "Player2"] + [""] * 18,
        "UTR": [5.00, 3.50] + [""] * 18,
        "Preferred Format": ["Singles", "Doubles"] + [""] * 18,
        "First Serve %": [75, 80] + [""] * 18,
        "Winners": [10, 15] + [""] * 18,
        "Unforced Error %": [20, 25] + [""] * 18,
        "Win Rate %": [60, 55] + [""] * 18,
        "Double Faults": [5, 3] + [""] * 18
    })
    return template

# Button to download CSV template
st.write("### Download CSV Template")
csv_template = create_csv_template()
csv = csv_template.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV Template", data=csv, file_name="tennis_players_template.csv", mime="text/csv")

# Upload CSV file option
uploaded_file = st.file_uploader("Or upload a CSV file with player data", type=["csv"])

# Process uploaded file
if uploaded_file:
    uploaded_data = pd.read_csv(uploaded_file)
    uploaded_data = uploaded_data.dropna(subset=["Name"])
    
    required_columns = {"Name", "UTR", "Preferred Format", "First Serve %", "Winners", "Unforced Error %", "Win Rate %", "Double Faults"}
    if set(uploaded_data.columns) >= required_columns:
        for _, row in uploaded_data.iterrows():
            player_data = {
                "Name": row["Name"],
                "UTR": row["UTR"],
                "Preferred Format": row["Preferred Format"],
                "First Serve %": row["First Serve %"],
                "Winners": row["Winners"],
                "Unforced Error %": row["Unforced Error %"],
                "Win Rate %": row["Win Rate %"],
                "Double Faults": row["Double Faults"]
            }
            save_player_to_db(player_data)
        st.success("Players successfully added from CSV file!")
    else:
        st.error("Uploaded CSV file is missing one or more required columns.")

# Manual Player Entry Form
st.write("### Enter Lineup Format")
singles = st.text_input("Number of singles players")
doubles = st.text_input("Number of doubles pairs")

st.write("### Enter Player Details Manually")
name = st.text_input("Player Name")
utr = st.text_input("UTR")
preferred_format = st.selectbox("Preferred Format", ["Singles", "Doubles", "Either"])
first_serve_percentage = st.slider("First Serve Percentage (%)", 0, 100)
winners = st.text_input("Winners")
unforced_error_percentage = st.slider("Unforced Error Percentage (%)", 0, 100)
win_rate = st.slider("Win Rate (%)", 0, 100)
double_faults = st.text_input("Double Faults")

# Add player to SQLite database
if st.button("Add Player"):
    if name:
        player_data = {
            "Name": name,
            "UTR": utr,
            "Preferred Format": preferred_format,
            "First Serve %": first_serve_percentage,
            "Winners": winners,
            "Unforced Error %": unforced_error_percentage,
            "Win Rate %": win_rate,
            "Double Faults": double_faults
        }
        save_player_to_db(player_data)
        st.success(f"Added player {name} to the database.")
    else:
        st.error("Please enter the player's name.")

# Display current list of players with delete option
st.write("### Player List")
players = get_players_from_db()
for player in players:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"{player['Name']} - UTR: {player['UTR']}, Format: {player['Preferred Format']}, "
                 f"First Serve %: {player['First Serve %']}, Winners: {player['Winners']}, "
                 f"Unforced Error %: {player['Unforced Error %']}, Win Rate %: {player['Win Rate %']}, "
                 f"Double Faults: {player['Double Faults']}")
    with col2:
        if st.button(f"Delete {player['Name']}", key=f"delete_{player['ID']}"):
            delete_player_from_db(player["ID"])
            st.experimental_rerun()  # Refresh the page to show updated player list

# Button to get AI-generated pairs
if st.button("Pair Players Using AI"):
    ai_suggestions = get_ai_pairing_suggestions(players)
    
    # Display AI pairing suggestions
    st.write("### AI-Recommended Pairs")
    st.write(ai_suggestions)

# Plotting player metrics with Matplotlib
st.write("### Player Metrics Comparison")
metric = st.selectbox("Choose a metric to visualize", ["UTR", "First Serve %", "Winners", "Unforced Error %", "Win Rate %", "Double Faults"])

# Function to create a bar chart for the selected metric
def plot_metric(players, metric):
    try:
        names = [player['Name'] for player in players]
        values = [float(player[metric]) for player in players]  # Convert values to float for consistent plotting

        plt.figure(figsize=(10, 6))
        plt.bar(names, values, color="skyblue")
        plt.title(f"Player Comparison by {metric}")
        plt.xlabel("Players")
        plt.ylabel(metric)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)


    except ValueError:
        st.error("Failed to plot the metric. Please ensure all values are numeric.")
    except KeyError:
        st.error(f"Metric '{metric}' is not available in the player data.")

# Call the plotting function with current player data
plot_metric(players, metric)