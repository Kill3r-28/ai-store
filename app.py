import streamlit as st
import json
import os

# --- CONFIGURATION ---
DATA_FILE = "tools.json"

# --- DATA HELPER FUNCTIONS ---
def load_tools():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_tools(tools):
    with open(DATA_FILE, "w") as f:
        json.dump(tools, f)

# --- APP UI ---
st.set_page_config(page_title="NxtWave AI Store", layout="wide")
st.title("🚀 NxtWave AI App Store")

# Initialize session state
if "tools" not in st.session_state:
    st.session_state.tools = load_tools()

# Sidebar: Add new tool
with st.sidebar:
    st.header("Register a New Tool")
    with st.form("add_tool"):
        name = st.text_input("Tool Name")
        url = st.text_input("App URL")
        desc = st.text_area("Description")
        if st.form_submit_button("Add to Store"):
            new_tool = {"name": name, "url": url, "desc": desc, "launches": 0}
            st.session_state.tools.append(new_tool)
            save_tools(st.session_state.tools)
            st.success("Tool added!")

# Main Area: Display tools
st.subheader("Available AI Tools")
cols = st.columns(3)

for i, tool in enumerate(st.session_state.tools):
    with cols[i % 3]:
        st.markdown(f"### {tool['name']}")
        st.write(tool['desc'])
        # Use a button as a "Launch" link to track clicks
        if st.button(f"Launch {tool['name']}", key=f"btn_{i}"):
            tool['launches'] += 1
            save_tools(st.session_state.tools)
            st.link_button("Go to App", tool['url'])
        st.caption(f"Total Launches: {tool['launches']}")
