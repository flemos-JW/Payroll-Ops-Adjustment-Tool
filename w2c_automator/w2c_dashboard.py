"""W-2C Automator Dashboard.

Paste MIDs, pick a year, save them to mids.txt. Dashboard shows the exact
terminal command to run, plus results and retry commands from the last run.

Launch:
    streamlit run /Users/franciscolemos/apps/w2c_automator/w2c_dashboard.py
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from components import (
    inject_global_css, render_alert, render_header, render_app_sidebar,
    render_step_progress, render_metric_row, render_section_divider,
    render_results_table, page_config,
)

SCRIPT_DIR   = Path(__file__).resolve().parent
MIDS_PATH    = SCRIPT_DIR / "mids.txt"
RESULTS_PATH = SCRIPT_DIR / "results.csv"
FAILED_PATH  = SCRIPT_DIR / "failed_mids.txt"
RUN_SCRIPT   = SCRIPT_DIR / "w2c_run.py"

page_config("W-2C Automator", "🤖")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def _clear_data():
    for k in list(st.session_state.keys()):
        if k != "authenticated":
            del st.session_state[k]
    st.rerun()

render_app_sidebar("W-2C Automator", "v1.2", "#00e5ff",
                   quick_actions=[{"label": "Clear Session", "callback": _clear_data, "key": "w2c_clear"}])

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
inject_global_css("w2c")
render_header("w2c", "W-2C AUTOMATOR", "PASTE MIDs · PICK YEAR · RUN AUTOMATION",
              icon="🤖")

# ---------------------------------------------------------------------------
# Step Progress
# ---------------------------------------------------------------------------
_has_mids = bool(st.session_state.get("w2c_saved_count"))
_has_results = RESULTS_PATH.exists()
steps = [
    {"label": "Paste MIDs", "complete": len(st.session_state.get("mids_raw", "").strip()) > 0},
    {"label": "Save", "complete": _has_mids},
    {"label": "Run", "complete": _has_results},
    {"label": "Results", "complete": _has_results},
]
_current = 0
if steps[0]["complete"]:
    _current = 1
if steps[1]["complete"]:
    _current = 2
if steps[2]["complete"]:
    _current = 3
render_step_progress("w2c", steps, _current, "#00e5ff")

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------
left, right = st.columns([2, 1])

with left:
    mids_raw = st.text_area(
        "One MID per line. Blank lines and `#` comments are ignored. Duplicates are removed automatically.",
        height=340,
        placeholder="M12345\nM67890\nM24680",
        key="mids_raw",
    )

with right:
    year_options = ["2024", "2023", "2022", "2021", "2020", "2025", "2026"]
    year = st.selectbox("Tax Year", year_options, key="year_sel")

    st.markdown(f"""
    <div style="color:#8a9bb0; font-size:0.8rem; margin:6px 0 14px 0; line-height:1.4;">
        The script will click <b>Generate W2c</b> on the <b style="color:#00e5ff;">{year}</b> row
        and <b>Upload W2c</b> on the highest <b style="color:#00e5ff;">{year}</b> Correction.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Parse pasted MIDs
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
# Command & Run
# ---------------------------------------------------------------------------
render_section_divider("w2c", "EXECUTE", "#00e5ff")

cmd = f"python3 {RUN_SCRIPT} --year {year}"
st.code(cmd, language="bash")

st.markdown("""
<div style="color:#8a9bb0; font-size:0.82rem; line-height:1.7; margin-top:-6px;">
    1. Open a Terminal &rarr; paste the command above.<br>
    2. Chromium opens &mdash; log in via Okta Verify if needed, then press <b>Enter</b> to start.<br>
    3. Progress streams live; results save to <code>results.csv</code> after every MID.
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
# Results
# ---------------------------------------------------------------------------
render_section_divider("w2c", "RESULTS", "#06ffa5")

if st.button("Refresh Results", key="w2c_refresh"):
    st.rerun()

if not RESULTS_PATH.exists():
    render_alert("w2c", "info", "NO RESULTS YET",
                 "Save MIDs above and run the command to populate this panel.")
else:
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

        render_metric_row([
            {"label": "Processed", "value": str(total), "color": "#00e5ff"},
            {"label": "Successful", "value": str(ok_n), "color": "#06ffa5"},
            {"label": "Not Found", "value": str(nf_n), "color": "#ffbe0b"},
            {"label": "Errors", "value": str(err_n), "color": "#ff006e"},
        ])

        st.write("")
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

        render_results_table(display_df, "Status")

        # Retry section for failures
        if FAILED_PATH.exists() and FAILED_PATH.stat().st_mtime >= RESULTS_PATH.stat().st_mtime:
            failed_mids = [l.strip() for l in FAILED_PATH.read_text().splitlines() if l.strip()]
            if failed_mids:
                st.write("")
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
