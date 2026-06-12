import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

TORONTO_TZ = ZoneInfo("America/Toronto")

today_date = datetime.now(TORONTO_TZ).date()

from db import (
    init_db,
    add_entry,
    get_entries_by_date,
    get_all_entries,
    delete_entry,
    get_recent_activities,
    get_latest_entry_by_date,
    init_notes_table,
    get_notes,
    save_notes,
    get_back_on_track,
    save_back_on_track,
    get_anchors,
    save_anchors
)

st.set_page_config(page_title="Activity Tracker", layout="wide")

init_db()
init_notes_table()

if "selected_activity_name" not in st.session_state:
    st.session_state.selected_activity_name = ""

if "last_end_time" not in st.session_state:
    st.session_state.last_end_time = ""

if "selected_activity_type" not in st.session_state:
    st.session_state.selected_activity_type = "Education"

ACTIVITY_TYPES = [
    "Education",
    "Health",
    "Personal Care",
    "House Chores",
    "Social",
    "Relax",
    "Time Waster",
    "Work",
    "Productive Block"
]

st.title("Activity Tracker")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Log Entry", "Reports", "Notes", "Back on Track", "Anchors"])


def calculate_duration_minutes(start_t: time, end_t: time) -> int:
    start_dt = datetime.combine(today_date, start_t)
    end_dt = datetime.combine(today_date, end_t)

    if end_dt <= start_dt:
        raise ValueError("End time must be after start time.")

    return int((end_dt - start_dt).total_seconds() // 60)


def parse_time_input(t_str):
    t_str = t_str.strip()

    if not t_str.isdigit():
        raise ValueError("Time must be numeric (e.g. 615 or 1815)")

    if len(t_str) == 3:  # e.g. 615 → 06:15
        hour = int(t_str[0])
        minute = int(t_str[1:])
    elif len(t_str) == 4:  # e.g. 1815 → 18:15
        hour = int(t_str[:2])
        minute = int(t_str[2:])
    else:
        raise ValueError("Invalid format. Use 615 or 1815")

    if hour > 23 or minute > 59:
        raise ValueError("Invalid time value")

    return time(hour, minute)

with tab1:
    st.subheader("Quick Logging")

    recent_rows = get_recent_activities(limit=10)
    latest_entry = get_latest_entry_by_date(today_date.isoformat())

    default_start_time = ""

    if latest_entry:
        default_start_time = latest_entry["end_time"].replace(":", "")

    if recent_rows:
        recent_options = ["-- Select a recent activity --"] + [
            f"{row['activity_name']} ({row['activity_type']})" for row in recent_rows
        ]

        selected_recent = st.selectbox(
            "Recent Activities",
            recent_options,
            key="recent_activity_select"
        )

        if selected_recent != "-- Select a recent activity --":
            selected_index = recent_options.index(selected_recent) - 1
            selected_row = recent_rows[selected_index]
            st.session_state.selected_activity_name = selected_row["activity_name"]
            st.session_state.selected_activity_type = selected_row["activity_type"]

    st.divider()
    st.subheader("Add a new entry")

    with st.form("entry_form"):
        col1, col2 = st.columns(2)

        with col1:
            entry_date = st.date_input("Date", value=today_date)
            activity_name = st.text_input(
                "Activity Name",
                value=st.session_state.selected_activity_name,
                placeholder="e.g. Having Dinner"
            )

        with col2:
            default_type_index = ACTIVITY_TYPES.index(st.session_state.selected_activity_type) \
                if st.session_state.selected_activity_type in ACTIVITY_TYPES else 0

            activity_type = st.selectbox(
                "Activity Type",
                ACTIVITY_TYPES,
                index=default_type_index
            )

            start_time_str = st.text_input(
                "Start Time (e.g. 615 or 1815)",
                value=default_start_time            
            )
            end_time_str = st.text_input("End Time (e.g. 700 or 1900)")

        submitted = st.form_submit_button("Save Entry")

        if submitted:
            if not activity_name.strip():
                st.error("Please enter an activity name.")
            elif not start_time_str or not end_time_str:
                st.error("Please enter both start time and end time.")
            else:
                try:
                    start_time = parse_time_input(start_time_str)
                    end_time = parse_time_input(end_time_str)
                    
                    duration_minutes = calculate_duration_minutes(start_time, end_time)

                    add_entry(
                        entry_date=entry_date.isoformat(),
                        activity_name=activity_name.strip(),
                        activity_type=activity_type,
                        start_time=start_time.strftime("%H:%M"),
                        end_time=end_time.strftime("%H:%M"),
                        duration_minutes=duration_minutes,
                    )

                    # keep latest selection for convenience
                    st.session_state.selected_activity_name = activity_name.strip()
                    st.session_state.selected_activity_type = activity_type

                    st.success(f"Saved. Duration: {duration_minutes} minutes.")
                    st.rerun()

                except ValueError as e:
                    st.error(str(e))

    st.divider()
    st.subheader("Today's Entries")

    today_rows = get_entries_by_date(today_date.isoformat())

    if today_rows:
        today_df = pd.DataFrame([dict(row) for row in today_rows])

        display_df = today_df[
            ["id", "start_time", "end_time", "activity_name", "activity_type", "duration_minutes"]
        ].rename(
            columns={
                "id": "ID",
                "start_time": "Start",
                "end_time": "End",
                "activity_name": "Activity",
                "activity_type": "Type",
                "duration_minutes": "Minutes",
            }
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.subheader("Delete an entry")
        entry_ids = today_df["id"].tolist()
        entry_to_delete = st.selectbox("Select entry ID to delete", entry_ids)

        if st.button("Delete Selected Entry"):
            delete_entry(int(entry_to_delete))
            st.success("Entry deleted.")
            st.rerun()
    else:
        st.info("No entries for today yet.")


with tab2:
    st.subheader("Reports")

    all_rows = get_all_entries()

    if not all_rows:
        st.info("No data yet. Add some entries first.")
    else:
        df = pd.DataFrame([dict(row) for row in all_rows])

        # Clean types
        df["entry_date"] = pd.to_datetime(df["entry_date"], errors="coerce")
        df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce")

        # Drop bad rows just in case
        df = df.dropna(subset=["entry_date", "duration_minutes"])

        if df.empty:
            st.warning("No valid data available for reports.")
        else:
            min_date = df["entry_date"].dt.date.min()
            max_date = df["entry_date"].dt.date.max()

            col1, col2 = st.columns(2)
            with col1:
                start_filter = st.date_input("From", value=min_date, key="report_start")
            with col2:
                end_filter = st.date_input("To", value=max_date, key="report_end")

            if start_filter > end_filter:
                st.error("'From' date cannot be after 'To' date.")
            else:
                filtered_df = df[
                    (df["entry_date"].dt.date >= start_filter)
                    & (df["entry_date"].dt.date <= end_filter)
                ].copy()

                if filtered_df.empty:
                    st.warning("No data for selected date range.")
                else:
                    total_minutes = int(filtered_df["duration_minutes"].sum())
                    total_hours = round(total_minutes / 60, 2)
                    total_entries = len(filtered_df)

                    m1, m2 = st.columns(2)
                    with m1:
                        st.metric("Total Hours", total_hours)
                    with m2:
                        st.metric("Entries Logged", total_entries)

                    # Summaries
                    category_summary = (
                        filtered_df.groupby("activity_type", as_index=False)["duration_minutes"]
                        .sum()
                        .sort_values("duration_minutes", ascending=False)
                    )

                    activity_summary = (
                        filtered_df.groupby("activity_name", as_index=False)["duration_minutes"]
                        .sum()
                        .sort_values("duration_minutes", ascending=False)
                        .head(10)
                    )

                    daily_summary = (
                        filtered_df.assign(entry_day=filtered_df["entry_date"].dt.date)
                        .groupby("entry_day", as_index=False)["duration_minutes"]
                        .sum()
                        .rename(columns={"entry_day": "entry_date"})
                        .sort_values("entry_date")
                    )

                    # Add hours column for display-friendly charts
                    category_summary["hours"] = (category_summary["duration_minutes"] / 60).round(2)
                    activity_summary["hours"] = (activity_summary["duration_minutes"] / 60).round(2)
                    daily_summary["hours"] = (daily_summary["duration_minutes"] / 60).round(2)

                    # Charts
                    st.markdown("### Time by Category")
                    pie_fig = px.pie(
                        category_summary,
                        names="activity_type",
                        values="hours",
                        title="Category Split (Hours)"
                    )
                    st.plotly_chart(pie_fig, use_container_width=True)

                    st.markdown("### Top Activities")
                    bar_fig = px.bar(
                        activity_summary,
                        x="activity_name",
                        y="hours",
                        title="Top Activities by Hours"
                    )
                    bar_fig.update_layout(xaxis_title="Activity", yaxis_title="Hours")
                    st.plotly_chart(bar_fig, use_container_width=True)

                    st.markdown("### Daily Totals")
                    daily_fig = px.bar(
                        daily_summary,
                        x="entry_date",
                        y="hours",
                        title="Hours Logged Per Day"
                    )
                    daily_fig.update_layout(xaxis_title="Date", yaxis_title="Hours")
                    st.plotly_chart(daily_fig, use_container_width=True)

                    st.markdown("### Category Summary")
                    st.dataframe(
                        category_summary[["activity_type", "duration_minutes", "hours"]].rename(
                            columns={
                                "activity_type": "Category",
                                "duration_minutes": "Minutes",
                                "hours": "Hours",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.markdown("### All Entries in Selected Range")
                    display_df = filtered_df.copy()
                    display_df["entry_date"] = display_df["entry_date"].dt.date.astype(str)

                    st.dataframe(
                        display_df[
                            [
                                "entry_date",
                                "start_time",
                                "end_time",
                                "activity_name",
                                "activity_type",
                                "duration_minutes",
                            ]
                        ].rename(
                            columns={
                                "entry_date": "Date",
                                "start_time": "Start",
                                "end_time": "End",
                                "activity_name": "Activity",
                                "activity_type": "Type",
                                "duration_minutes": "Minutes",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )


with tab3:
    st.subheader("Notes")

    current_notes = get_notes()

    new_note = st.text_input("Add a note")

    if st.button("Add Note"):
        if not new_note.strip():
            st.error("Note cannot be empty.")
        else:
            current_notes.append(new_note.strip())
            save_notes(current_notes)
            st.success("Note added.")
            st.rerun()

    st.divider()

    if current_notes:
        st.markdown("### Current Notes")

        for idx, note in enumerate(current_notes):
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(f"{idx + 1}. {note}")

            with col2:
                if st.button("Remove", key=f"remove_note_{idx}"):
                    updated_notes = current_notes.copy()
                    updated_notes.pop(idx)
                    save_notes(updated_notes)
                    st.rerun()
    else:
        st.info("No notes yet.")


with tab4:
    st.subheader("Back on Track")

    current_track = get_back_on_track()

    new_track = st.text_input("Add a track")

    if st.button("Add Track"):
        if not new_track.strip():
            st.error("Track cannot be empty.")
        else:
            current_track.append(new_track.strip())
            save_back_on_track(current_track)
            st.success("Track added.")
            st.rerun()

    st.divider()

    if current_track:
        st.markdown("### Current Track")

        for idx, track in enumerate(current_track):
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(f"{idx + 1}. {track}")

            with col2:
                if st.button("Remove", key=f"remove_track_{idx}"):
                    updated_track = current_track.copy()
                    updated_track.pop(idx)
                    save_back_on_track(updated_track)
                    st.rerun()
    else:
        st.info("No track yet.")


with tab5:
    st.subheader("Anchors")

    current_anchors = get_anchors()

    new_anchor = st.text_input("Add a anchor")

    if st.button("Add Anchor"):
        if not new_anchor.strip():
            st.error("Anchor cannot be empty.")
        else:
            current_anchors.append(new_anchor.strip())
            save_anchors(current_anchors)
            st.success("Anchor added.")
            st.rerun()

    st.divider()

    if current_anchors:
        st.markdown("### Current Anchors")

        for idx, anchor in enumerate(current_anchors):
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(f"{idx + 1}. {anchor}")

            with col2:
                if st.button("Remove", key=f"remove_anchor_{idx}"):
                    updated_anchors = current_anchors.copy()
                    updated_anchors.pop(idx)
                    save_anchors(updated_anchors)
                    st.rerun()
    else:
        st.info("No anchors yet.")

