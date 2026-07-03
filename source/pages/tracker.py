import pandas as pd
import streamlit as st

from source.services.job_tracker import (
    PRIORITY_OPTIONS,
    STATUS_OPTIONS,
    TRACKER_COLUMNS,
    load_job_tracker,
    new_job_from_analysis,
    normalize_tracker_df,
    save_job_tracker,
    upsert_job_from_analysis,
)
import source.ui.components as ui


def add_current_analysis_to_tracker():
    if not st.session_state.analysis_result:
        st.warning("Run an analysis before adding a role to the tracker.")
        return

    st.session_state.job_tracker_df, message = upsert_job_from_analysis(
        st.session_state.job_tracker_df,
        st.session_state.analysis_result,
    )
    save_job_tracker(st.session_state.job_tracker_df)
    st.success(message)


def show_tracker_page():
    ui.render_page_header(
        "Job Tracker",
        "Track applications, follow-ups, target salary, and match scores in one clean table.",
    )

    st.session_state.job_tracker_df = normalize_tracker_df(st.session_state.job_tracker_df)

    if st.session_state.job_tracker_df.empty and st.session_state.analysis_result:
        st.session_state.job_tracker_df = pd.DataFrame(
            [new_job_from_analysis(st.session_state.analysis_result)]
        )[TRACKER_COLUMNS]
        save_job_tracker(st.session_state.job_tracker_df)

    metric_cols = st.columns(4, gap="medium")
    tracker_df = st.session_state.job_tracker_df

    status_counts = (
        tracker_df["Status"].value_counts().to_dict()
        if not tracker_df.empty and "Status" in tracker_df.columns
        else {}
    )

    with metric_cols[0]:
        ui.render_summary_card("Total Roles", str(len(tracker_df)), "Tracked opportunities")
    with metric_cols[1]:
        ui.render_summary_card("Applied", str(status_counts.get("Applied", 0)), "Submitted applications")
    with metric_cols[2]:
        ui.render_summary_card("Interview", str(status_counts.get("Interview", 0)), "Active conversations")
    with metric_cols[3]:
        ui.render_summary_card("Offers", str(status_counts.get("Offer", 0)), "Offer stage")

    left, right = st.columns([1, 1], gap="medium")

    with left:
        if st.button("Add Current Analysis", type="primary", width="stretch"):
            add_current_analysis_to_tracker()
            st.rerun()

    with right:
        if st.button("Reload Tracker", width="stretch"):
            st.session_state.job_tracker_df = load_job_tracker()
            st.rerun()

    edited_df = st.data_editor(
        st.session_state.job_tracker_df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "Priority": st.column_config.SelectboxColumn("Priority", options=PRIORITY_OPTIONS),
            "Job Link": st.column_config.LinkColumn("Job Link"),
            "Match Score": st.column_config.NumberColumn("Match Score", min_value=0, max_value=100),
        },
        hide_index=True,
        key="job_tracker_editor",
    )

    save_col, export_col = st.columns([1, 1], gap="medium")

    with save_col:
        if st.button("Save Tracker", type="primary", width="stretch"):
            st.session_state.job_tracker_df = normalize_tracker_df(edited_df)
            save_job_tracker(st.session_state.job_tracker_df)
            st.success("Tracker saved locally.")

    with export_col:
        st.download_button(
            "Export CSV",
            data=edited_df.to_csv(index=False).encode("utf-8"),
            file_name="truthfit_job_tracker.csv",
            mime="text/csv",
            width="stretch",
        )
