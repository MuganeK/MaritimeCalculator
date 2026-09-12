from app import main


if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Naval Training Cruise Planner", page_icon="⚓", layout="wide")

st.title("⚓ Naval Training Cruise: Watchbill & Task Tracker")
st.markdown("---")

# 1. Initialize Student Roster Data in System Session Memory
if 'students' not in st.session_state:
    st.session_state.students = [
        {"MIDN": "Alex Smith", "Watch Status": "Off-Duty", "Helmo Tasks": "Complete", "Nav Tasks": "Pending"},
        {"MIDN": "Jordan Taylor", "Watch Status": "Off-Duty", "Helmo Tasks": "Pending", "Nav Tasks": "Complete"},
        {"MIDN": "Morgan Brown", "Watch Status": "Off-Duty", "Helmo Tasks": "Pending", "Nav Tasks": "Pending"},
        {"MIDN": "Casey Wilson", "Watch Status": "Off-Duty", "Helmo Tasks": "Complete", "Nav Tasks": "Complete"},
        {"MIDN": "Jamie Davis", "Watch Status": "Off-Duty", "Helmo Tasks": "Pending", "Nav Tasks": "Pending"},
    ]

# Layout Split
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("👥 Student Roster & Qualification Log")
    df = pd.DataFrame(st.session_state.students)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Simple form to adjust training progress on the fly
    st.markdown("#### ⚡ Quick Update Qualification")
    target_student = st.selectbox("Select Student", [s["MIDN"] for s in st.session_state.students])
    target_task = st.radio("Task to Update", ["Helmo Tasks", "Nav Tasks"], horizontal=True)
    target_status = st.radio("Status", ["Pending", "Complete"], horizontal=True)
    
    if st.button("Update Log"):
        for s in st.session_state.students:
            if s["MIDN"] == target_student:
                s[target_task] = target_status
        st.rerun()

with col_right:
    st.subheader("⏰ Automated 4-Hour Watchbill Generator")
    st.write("Assigns off-duty students to mandatory bridge stations seamlessly.")
    
    watch_stations = ["Bridge Watch Officer (Instructor)", "Helmsman (Student)", "Lee Helm (Student)", "Lookout Port (Student)"]
    
    if st.button("🔄 Generate Random Rotation Shift"):
        # Shuffle student list to create a fair assignment rotation
        shuffled_students = [s["MIDN"] for s in st.session_state.students]
        random.shuffle(shuffled_students)
        
        assignments = []
        for i, station in enumerate(watch_stations):
            if i < len(shuffled_students):
                assignments.append({"Watch Station": station, "Assigned Personnel": shuffled_students[i]})
            else:
                assignments.append({"Watch Station": station, "Assigned Personnel": "Unassigned (Roster Depleted)"})
                
        st.markdown("#### 📋 Current Watch Station Bill")
        st.table(pd.DataFrame(assignments))
        st.success("Watch rotation generated. Keep watch standing strict and logs updated.")