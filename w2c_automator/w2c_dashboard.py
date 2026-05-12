"""W-2C Automator Dashboard.

Paste MIDs, pick a year, save them to mids.txt. Dashboard shows the exact
terminal command to run, plus results and retry commands from the last run.

Launch:
    streamlit run /Users/franciscolemos/apps/w2c_automator/w2c_dashboard.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from components import inject_global_css, render_alert, render_header

SCRIPT_DIR   = Path(__file__).resolve().parent
MIDS_PATH    = SCRIPT_DIR / "mids.txt"
RESULTS_PATH = SCRIPT_DIR / "results.csv"
FAILED_PATH  = SCRIPT_DIR / "failed_mids.txt"
RUN_SCRIPT   = SCRIPT_DIR / "w2c_run.py"

st.set_page_config(page_title="W-2C Automator", layout="wide", page_icon="🤖")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
inject_global_css("w2c")
render_header("w2c", "W-2C AUTOMATOR", "PASTE MIDs · PICK YEAR · COPY THE COMMAND · RUN IT IN TERMINAL",
              icon="🤖")

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("1 · Paste MIDs")
    mids_raw = st.text_area(
        "One MID per line. Blank lines and `#` comments are ignored. Duplicates are removed automatically.",
        height=340,
        placeholder="M12345\nM67890\nM24680",
        key="mids_raw",
    )

with right:
    st.subheader("2 · Tax Year")
    year_options = ["2024", "2023", "2022", "2021", "2020", "2025", "2026"]
    year = st.selectbox("Tax Year", year_options, key="year_sel",
                        label_visibility="collapsed")

    st.markdown(f"""
    <div style="color:#8a9bb0; font-size:0.8rem; margin:6px 0 14px 0; line-height:1.4;">
        The script will click <b>Generate W2c</b> on the <b style="color:#00e5ff;">{year}</b> row
        and <b>Upload W2c</b> on the highest <b style="color:#00e5ff;">{year}</b> Correction.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("3 · Save & Prepare")

# ---------------------------------------------------------------------------
# Parse pasted MIDs (live, before save)
# ---------------------------------------------------------------------------
parsed = []
seen   = set()
for line in mids_raw.splitlines():
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    if s in seen:
        continue
    seen.add(s)
    parsed.append(s)

with left:
    st.caption(f"📝 **{len(parsed)}** unique MID(s) ready to save")

with right:
    save_disabled = len(parsed) == 0
    if st.button("💾  Save to mids.txt",
                 type="primary",
                 use_container_width=True,
                 disabled=save_disabled):
        MIDS_PATH.write_text("\n".join(parsed) + "\n")
        st.session_state["w2c_saved_count"] = len(parsed)
        st.rerun()
    if save_disabled:
        st.caption("⬅ Paste at least one MID first")

# ---------------------------------------------------------------------------
# Saved confirmation
# ---------------------------------------------------------------------------
if st.session_state.get("w2c_saved_count"):
    render_alert("w2c", "ok",
                 f"✓ SAVED — {st.session_state['w2c_saved_count']} MID(s) written to mids.txt", "")

# ---------------------------------------------------------------------------
# Command display
# ---------------------------------------------------------------------------
st.divider()
st.subheader("4 · Run This Command in Terminal")

cmd = f"python3 {RUN_SCRIPT} --year {year}"
st.code(cmd, language="bash")

st.markdown("""
<div style="color:#8a9bb0; font-size:0.85rem; line-height:1.7; margin-top:-6px;">
    1. Open a Terminal.<br>
    2. Paste the command above, hit <b>Enter</b>.<br>
    3. Chromium opens. Log in via Okta Verify if needed, then press <b>Enter</b> in the terminal to start.<br>
    4. Progress streams live; results save to <code>results.csv</code> after every MID.<br>
    5. When it's done, refresh this dashboard to see the results below.
</div>
""", unsafe_allow_html=True)

st.caption("If Okta login is required, use the terminal command above instead.")
if st.button("Run Now", type="primary", use_container_width=True, key="w2c_run_now"):
    _cmd = ["python3", "w2c_run.py", str(MIDS_PATH), "--year", str(year)]
    with st.spinner("Running W-2C automation..."):
        _proc = subprocess.run(_cmd, capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR))
    if _proc.returncode == 0:
        render_alert("w2c", "ok", "✓ RUN COMPLETE", "Automation finished successfully. Results are below.")
    else:
        render_alert("w2c", "err", "⚠ RUN FAILED", f"Exit code {_proc.returncode}. Check terminal output for details.")
    st.rerun()

# ---------------------------------------------------------------------------
# Results viewer
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📊 Last Run Results")

if st.button("Refresh Results", key="w2c_refresh"):
    st.rerun()

if not RESULTS_PATH.exists():
    render_alert("w2c", "info", "NO RESULTS YET",
                 "Save MIDs above and run the command to populate this panel.")
else:
    from datetime import datetime
    import os
    _results_mtime = os.path.getmtime(RESULTS_PATH)
    _results_ago = datetime.now() - datetime.fromtimestamp(_results_mtime)
    _mins_ago = int(_results_ago.total_seconds() / 60)
    _time_str = f"{_mins_ago} min ago" if _mins_ago < 60 else f"{_mins_ago // 60}h {_mins_ago % 60}m ago"
    st.caption(f"Results from: {datetime.fromtimestamp(_results_mtime).strftime('%I:%M %p')} ({_time_str})")

    try:
        df = pd.read_csv(RESULTS_PATH, dtype=str).fillna("")
    except Exception as e:
        st.error(f"Couldn't read results.csv: {e}")
        df = None

    if df is not None and not df.empty:
        total = len(df)
        ok_n  = int((df["Status"] == "ok").sum())
        nf_n  = int((df["Status"] == "not_found").sum())
        err_n = total - ok_n - nf_n

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Processed", total)
        m2.metric("Successful", ok_n)
        m3.metric("Not Found",  nf_n)
        m4.metric("Errors",     err_n)

        filter_mode = st.radio(
            "Show",
            ["All", "Failures only", "Successes only"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if filter_mode == "Failures only":
            display_df = df[df["Status"] != "ok"]
        elif filter_mode == "Successes only":
            display_df = df[df["Status"] == "ok"]
        else:
            display_df = df

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)

        # Retry section for failures
        if FAILED_PATH.exists() and FAILED_PATH.stat().st_mtime >= RESULTS_PATH.stat().st_mtime:
            failed_mids = [l.strip() for l in FAILED_PATH.read_text().splitlines() if l.strip()]
            if failed_mids:
                render_alert("w2c", "warn",
                             f"⚠ {len(failed_mids)} MID(s) FAILED", "Edit below to remove any you don't want to retry.")
                edited_mids = st.text_area(
                    "Failed MIDs (one per line)", value="\n".join(failed_mids),
                    height=120, key="w2c_retry_edit")
                retry_cmd = f"python3 {RUN_SCRIPT} {FAILED_PATH} --year {year}"
                st.code(retry_cmd, language="bash")
                st.caption("Tip: if a MID succeeds on retry, its row in results.csv gets overwritten.")
                if st.button("Retry Now", type="primary", key="w2c_retry_btn"):
                    retry_list = [m.strip() for m in edited_mids.splitlines() if m.strip()]
                    FAILED_PATH.write_text("\n".join(retry_list) + "\n")
                    _retry_cmd = ["python3", "w2c_run.py", str(FAILED_PATH), "--year", str(year)]
                    with st.spinner(f"Retrying {len(retry_list)} MID(s)..."):
                        _rproc = subprocess.run(_retry_cmd, capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR))
                    if _rproc.returncode == 0:
                        render_alert("w2c", "ok", "✓ RETRY COMPLETE", "All retried MIDs processed.")
                    else:
                        render_alert("w2c", "err", "⚠ RETRY FAILED", f"Exit code {_rproc.returncode}.")
                    st.rerun()
    else:
        render_alert("w2c", "info", "RESULTS FILE IS EMPTY", "")
