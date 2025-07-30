import streamlit as st
import pandas as pd

# ----------- SESSION STATE SETUP ----------- #

def init_session():
    defaults = {
        'page': 'setup',
        'player_list': [],
        'own_team': '',
        'opponent_team': '',
        'plus_minus': {},
        'lineup': [],
        'play_log': [],
        'undo_stack': [],
        'current_quarter': 'Q1',
        'quarters_done': [],
        'team_score': 0,
        'opponent_score': 0,
        'possessions_played': {}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ----------- PAGE 1: SETUP ----------- #

def game_setup():
    st.title("🏀 Game Setup – Basketball +/- Tracker")

    st.session_state.own_team = st.text_input("Enter Your Team Name", value=st.session_state.own_team)
    st.session_state.opponent_team = st.text_input("Enter Opponent Team Name", value=st.session_state.opponent_team)

    st.write("### Enter Your Team Roster (One player per line, max 15)")
    roster_input = st.text_area("Player Names", value="")
    players = [p.strip() for p in roster_input.strip().split("\n") if p.strip()]
    if len(players) > 15:
        players = players[:15]
    st.session_state.player_list = players

    if st.button("🚀 Start Game"):
        if len(players) >= 5:
            st.session_state.plus_minus = {p: 0 for p in players}
            st.session_state.possessions_played = {p: 0 for p in players}
            st.session_state.page = 'match'
        else:
            st.warning("Please enter at least 5 players to start the game.")

# ----------- PAGE 2: MATCH ----------- #

def match_page():
    st.title(f"{st.session_state.own_team} vs {st.session_state.opponent_team}")

    quarters = ['Q1', 'Q2', 'Q3', 'Q4']

    if not st.session_state.lineup:
        st.write("### Select Starting 5")
        st.warning("⚠️ Choose 5 unique players. Each player only once.")
        cols = st.columns(5)
        starters = []
        for i in range(5):
            with cols[i]:
                starter = st.selectbox(
                    f"Starter {i+1}",
                    options=[p for p in st.session_state.player_list if p not in starters],
                    key=f"starter_{i}"
                )
                starters.append(starter)

        if len(set(starters)) == 5:
            st.session_state.lineup = starters
            st.success("✅ Starting 5 set!")
        else:
            st.warning("Please choose 5 unique players.")
        return

    st.subheader("🕓 Quarter Progression")
    for q in quarters:
        if q == st.session_state.current_quarter:
            st.success(f"{q} ⏱ In Progress")
        elif q in st.session_state.quarters_done:
            st.info(f"{q} ✅ Completed")
        else:
            st.warning(f"{q} 🔒 Locked")

    if st.button("✅ Complete Current Quarter"):
        if st.session_state.current_quarter not in st.session_state.quarters_done:
            st.session_state.quarters_done.append(st.session_state.current_quarter)
        idx = quarters.index(st.session_state.current_quarter)
        if idx < 3:
            st.session_state.current_quarter = quarters[idx+1]
        else:
            st.session_state.page = 'final'

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.header(st.session_state.own_team)
        st.metric("Score", st.session_state.team_score)
    with col2:
        st.header(st.session_state.opponent_team)
        st.metric("Score", st.session_state.opponent_score)

    st.markdown("### 📊 Log Score")
    score_cols = st.columns(6)
    def log_score(team, points):
        entry = {
            'quarter': st.session_state.current_quarter,
            'team': team,
            'points': points,
            'lineup': list(st.session_state.lineup)
        }
        st.session_state.play_log.append(entry)
        st.session_state.undo_stack.clear()  # clear redo history after new action
        if team == 'Team':
            st.session_state.team_score += points
            for p in st.session_state.lineup:
                st.session_state.plus_minus[p] += points
                st.session_state.possessions_played[p] += 1
        else:
            st.session_state.opponent_score += points
            for p in st.session_state.lineup:
                st.session_state.plus_minus[p] -= points
                st.session_state.possessions_played[p] += 1

    if score_cols[0].button("Team +1 FT"): log_score("Team", 1)
    if score_cols[1].button("Team +2"): log_score("Team", 2)
    if score_cols[2].button("Team +3"): log_score("Team", 3)
    if score_cols[3].button("Opponent +1 FT"): log_score("Opponent", 1)
    if score_cols[4].button("Opponent +2"): log_score("Opponent", 2)
    if score_cols[5].button("Opponent +3"): log_score("Opponent", 3)

    # Undo / Redo Controls
    st.markdown("### 🔁 Undo / Redo")
    ucol1, ucol2 = st.columns(2)
    if ucol1.button("Undo Last Play"):
        if st.session_state.play_log:
            last = st.session_state.play_log.pop()
            st.session_state.undo_stack.append(last)
            if last['team'] == 'Team':
                st.session_state.team_score -= last['points']
                for p in last['lineup']:
                    st.session_state.plus_minus[p] -= last['points']
                    st.session_state.possessions_played[p] -= 1
            else:
                st.session_state.opponent_score -= last['points']
                for p in last['lineup']:
                    st.session_state.plus_minus[p] += last['points']
                    st.session_state.possessions_played[p] -= 1
    if ucol2.button("Redo Last Undo"):
        if st.session_state.undo_stack:
            redo = st.session_state.undo_stack.pop()
            st.session_state.play_log.append(redo)
            if redo['team'] == 'Team':
                st.session_state.team_score += redo['points']
                for p in redo['lineup']:
                    st.session_state.plus_minus[p] += redo['points']
                    st.session_state.possessions_played[p] += 1
            else:
                st.session_state.opponent_score += redo['points']
                for p in redo['lineup']:
                    st.session_state.plus_minus[p] -= redo['points']
                    st.session_state.possessions_played[p] += 1

    st.markdown("---")
    st.subheader("🔄 Substitution")
    sub_out = st.multiselect("Player(s) OUT", st.session_state.lineup, key="sub_out")
    sub_in = st.multiselect("Player(s) IN", [p for p in st.session_state.player_list if p not in st.session_state.lineup], key="sub_in")

    if st.button("Make Substitution"):
        if len(sub_out) != len(sub_in):
            st.warning("Select equal number of players IN and OUT")
        else:
            for o, i in zip(sub_out, sub_in):
                st.session_state.lineup.remove(o)
                st.session_state.lineup.append(i)
            st.success("Substitution(s) made successfully")

    st.markdown("---")
    st.subheader("📈 Live +/- and Possessions Played")
    for p in st.session_state.player_list:
        st.write(f"{p}: +/- {st.session_state.plus_minus[p]:+}, Possessions: {st.session_state.possessions_played[p]}")

# ----------- FINAL PAGE ----------- #

def final_page():
    st.title("🏁 Final Report")
    st.subheader("📋 Player Totals")
    df = pd.DataFrame({
        'Player': list(st.session_state.plus_minus.keys()),
        '+/-': list(st.session_state.plus_minus.values()),
        'Possessions Played': [st.session_state.possessions_played[p] for p in st.session_state.plus_minus.keys()]
    })
    st.dataframe(df.set_index('Player'))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export as CSV", data=csv, file_name="plus_minus_report.csv", mime='text/csv')

    st.subheader("📜 Play-by-Play Log")
    for i, play in enumerate(st.session_state.play_log, 1):
        st.write(f"{i}. [{play['quarter']}] {play['team']} +{play['points']} | Lineup: {', '.join(play['lineup'])}")

# ----------- ROUTER ----------- #

if st.session_state.page == 'setup':
    game_setup()
elif st.session_state.page == 'match':
    match_page()
elif st.session_state.page == 'final':
    final_page()
