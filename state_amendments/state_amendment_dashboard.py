"""State Amendments Dashboard.

Paste a 5-column table (State, Employee Names, MIDs, Total State Tax,
Amendment Title), save to amendments.csv, copy the terminal command, run it.
Mirror of the Voucher Reversal dashboard.

Launch:
    python3 -m streamlit run /Users/franciscolemos/apps/state_amendments/state_amendment_dashboard.py
"""
import io
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from components import inject_global_css, render_header, render_alert

SCRIPT_DIR    = Path(__file__).resolve().parent
INPUT_PATH    = SCRIPT_DIR / "amendments.csv"
RESULTS_PATH  = SCRIPT_DIR / "results.csv"
FAILED_PATH   = SCRIPT_DIR / "failed_amendments.csv"
RUN_SCRIPT    = SCRIPT_DIR / "state_amendment_run.py"

st.set_page_config(page_title="State Amendments", layout="wide", page_icon="🏛️")

# ---------------------------------------------------------------------------
# Header + shared styles
# ---------------------------------------------------------------------------
inject_global_css("sa", accent_color="#8338ec")
render_header("sa", "STATE AMENDMENTS AUTOMATOR",
              "UPLOAD CSV · REVIEW · COPY COMMAND · RUN IN TERMINAL",
              accent_color="#8338ec", secondary_color="#00e5ff", icon="\U0001f3db️")

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------
st.subheader("1 · Upload CSV")
st.caption(
    "Expected columns: **State**, **Employee Name**, **MID**, "
    "**Total State Tax**, **Amendment Title**. Header row required. "
    "One row per employee — rows for the same state are grouped into a "
    "single amendment. `Total State Tax` and `Amendment Title` should "
    "repeat (or be blank on duplicate rows; the first non-empty value per "
    "state wins). MIDs without a leading `M` are auto-prefixed. "
    "Drop in the Large Adjustment Generator's **State Tax Export** directly "
    "— just fill in the blank `Amendment Title` column in Excel first."
)

uploaded = st.file_uploader(
    "Amendments CSV",
    type=["csv"],
    label_visibility="collapsed",
    key="sa_upload",
)

raw = ""
if uploaded is not None:
    _bytes = uploaded.getvalue()
    for _enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            raw = _bytes.decode(_enc)
            break
        except UnicodeDecodeError:
            continue


# ---------------------------------------------------------------------------
# Parse pasted input
# ---------------------------------------------------------------------------
def _norm(s):
    return re.sub(r"[\s_]+", "", str(s).strip().lower())


def _with_m_prefix(mid_str):
    s = str(mid_str).strip()
    if not s:
        return s
    if s[0] in ("M", "m"):
        return "M" + s[1:]
    return "M" + s


def _split_list_cell(cell_value):
    s = str(cell_value or "").strip()
    if not s:
        return []
    for sep in ("\n", ";"):
        if sep in s:
            return [x.strip() for x in s.split(sep) if x.strip()]
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]
    return [s]


def parse_csv_text(text):
    """Parse CSV (or TSV) text into a per-employee DataFrame, then group into
    per-state preview rows. Returns (raw_per_emp_df, state_preview_df, error).
    Only one of (state_preview_df, error) is populated on success/failure."""
    if not text.strip():
        return None, None, None
    first = text.splitlines()[0]
    delim = "\t" if first.count("\t") >= first.count(",") else ","
    try:
        df = pd.read_csv(io.StringIO(text), sep=delim, dtype=str).fillna("")
    except Exception as e:
        return None, None, f"Could not parse CSV: {e}"
    if df.empty:
        return None, None, "No rows found."

    # Accept singular OR plural variants for backward compatibility
    lookup    = {_norm(c): c for c in df.columns}
    state_key = lookup.get("state")
    emp_key   = (lookup.get("employeename")  or lookup.get("employeenames")
                 or lookup.get("employees")  or lookup.get("name")
                 or lookup.get("names"))
    mid_key   = lookup.get("mid") or lookup.get("mids") or lookup.get("memberid") or lookup.get("memberids")
    total_key = (lookup.get("totalstatetax") or lookup.get("statetax")
                 or lookup.get("total"))
    title_key = lookup.get("amendmenttitle") or lookup.get("title")

    missing = []
    if not state_key: missing.append("State")
    if not emp_key:   missing.append("Employee Name")
    if not mid_key:   missing.append("MID")
    if not total_key: missing.append("Total State Tax")
    if not title_key: missing.append("Amendment Title")
    if missing:
        return None, None, f"Missing column(s): {', '.join(missing)}"

    # Normalize the per-employee frame
    out = pd.DataFrame({
        "State":           df[state_key].astype(str).str.strip(),
        "Employee Name":   df[emp_key].astype(str).str.strip(),
        "MID":             df[mid_key].astype(str).str.strip().apply(_with_m_prefix),
        "Total State Tax": df[total_key].astype(str).str.strip(),
        "Amendment Title": df[title_key].astype(str).str.strip(),
    })
    # Drop completely empty rows (Excel trailing blanks etc.)
    out = out[(out["State"].str.len() > 0) | (out["MID"].str.len() > 0)].reset_index(drop=True)

    def _parse_amount(s):
        try:
            return float(str(s).replace(",", "").replace("$", "").strip() or 0)
        except (ValueError, TypeError):
            return 0.0

    # Group by State into a per-state preview
    preview_rows = []
    for state, g in out.groupby("State", sort=True):
        names = [n for n in g["Employee Name"].tolist() if n]
        mids  = [m for m in g["MID"].tolist() if m]
        # Take first non-empty Amendment Title and first non-empty Total
        title_candidates  = [t for t in g["Amendment Title"].tolist() if t]
        amendment_title   = title_candidates[0] if title_candidates else ""
        totals_all        = [_parse_amount(v) for v in g["Total State Tax"].tolist() if str(v).strip()]
        unique_totals     = sorted({round(t, 2) for t in totals_all})
        state_total       = unique_totals[0] if unique_totals else 0.0

        preview_rows.append({
            "State":           state,
            "Amendment Title": amendment_title,
            "Employees":       len(names) if names else len(mids),
            "MIDs":            len(mids),
            "Total State Tax": state_total,
            # Extras for warnings
            "_name_count":     len(names),
            "_mid_count":      len(mids),
            "_title_blank":    amendment_title == "",
            "_total_variance": len(unique_totals) > 1,
        })

    state_df = pd.DataFrame(preview_rows)
    return out, state_df, None


raw_df, state_df, parse_err = parse_csv_text(raw)

col_preview, col_save = st.columns([3, 1])

with col_preview:
    if parse_err:
        render_alert("sa", "err", "⚠ PARSE ERROR", parse_err)
    elif state_df is not None and not state_df.empty:
        _display = state_df[["State", "Amendment Title", "Employees",
                             "MIDs", "Total State Tax"]].copy()
        _display["Total State Tax"] = _display["Total State Tax"].apply(lambda x: f"${x:,.2f}")
        st.caption(
            f"📝 **{len(raw_df)}** row(s) in CSV → **{len(state_df)}** amendment(s) "
            f"(grouped by state) · "
            f"**{int(state_df['MIDs'].sum())}** total employee(s) · "
            f"**${state_df['Total State Tax'].sum():,.2f}** grand total"
        )
        st.dataframe(_display, use_container_width=True, hide_index=True, height=260)

        # Warnings — operate at STATE level, not row level
        _blank_titles = state_df[state_df["_title_blank"]]
        _variance     = state_df[state_df["_total_variance"]]
        _name_mid_mm  = state_df[
            (state_df["_name_count"] > 0) &
            (state_df["_name_count"] != state_df["_mid_count"])
        ]

        if not _blank_titles.empty:
            _states = ", ".join(_blank_titles["State"].tolist())
            render_alert("sa", "err",
                         f"⚠ {len(_blank_titles)} state(s) missing Amendment Title: {_states}",
                         "The automation needs Amendment Title for Jweg, Period, etc. Fill "
                         "them in Excel (at least on the first row for each state) and re-upload.")

        if not _variance.empty:
            _states = ", ".join(_variance["State"].tolist())
            render_alert("sa", "warn",
                         f"⚠ {len(_variance)} state(s) have different Total State Tax across rows: {_states}",
                         "The state total should repeat on every row of a given state. The "
                         "preview uses the smallest non-empty value; check the CSV if that's not right.")

        if not _name_mid_mm.empty:
            _states = ", ".join(_name_mid_mm["State"].tolist())
            render_alert("sa", "warn",
                         f"⚠ {len(_name_mid_mm)} state(s) have a mismatch between number of Names and MIDs: {_states}",
                         "Names are optional (used only when a state has exactly one employee). "
                         "Safe to save anyway.")
    else:
        st.caption("Upload a CSV above — preview will appear here.")

with col_save:
    st.subheader("2 · Save")
    save_disabled = raw_df is None or raw_df.empty
    if st.button("💾  Save to amendments.csv",
                 type="primary",
                 use_container_width=True,
                 disabled=save_disabled):
        raw_df[["State", "Employee Name", "MID",
                "Total State Tax", "Amendment Title"]].to_csv(INPUT_PATH, index=False)
        st.session_state["sa_saved_count"] = len(raw_df)
        st.session_state["sa_saved_states"] = int(state_df["State"].nunique()) if state_df is not None else 0
        st.rerun()
    if save_disabled:
        st.caption("⬅ Upload a valid CSV first")

if st.session_state.get("sa_saved_count"):
    _saved_states = st.session_state.get("sa_saved_states", 0)
    _states_label = f" → {_saved_states} amendment(s)" if _saved_states else ""
    render_alert("sa", "ok",
                 f"✓ SAVED — {st.session_state['sa_saved_count']} row(s) written to amendments.csv{_states_label}",
                 "")

# ---------------------------------------------------------------------------
# Batch settings (CID + Company Name apply to every row in the batch)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("3 · Batch Settings")
st.caption(
    "These apply to every row in the batch. The automation will use them to "
    "fill out the amendment form."
)

_cid_col, _company_col = st.columns(2)
with _cid_col:
    cid = st.text_input(
        "CID",
        key="sa_cid",
        placeholder="e.g. C12345",
    )
with _company_col:
    company = st.text_input(
        "Company Name",
        key="sa_company",
        placeholder="e.g. Zip Co US Inc.",
    )

_missing_batch = []
if not (cid or "").strip():     _missing_batch.append("CID")
if not (company or "").strip(): _missing_batch.append("Company Name")
if _missing_batch:
    render_alert("sa", "warn",
                 f"⚠ MISSING — {', '.join(_missing_batch)} not filled in",
                 "The run command below will be missing these flags. Fill them in before copying the command.")

# ---------------------------------------------------------------------------
# Command display
# ---------------------------------------------------------------------------
st.divider()
st.subheader("4 · Run This Command in Terminal")

_cmd_parts = [f"python3 {RUN_SCRIPT}"]
if (cid or "").strip():
    _cmd_parts.append(f"--cid {shlex.quote(cid.strip())}")
if (company or "").strip():
    _cmd_parts.append(f"--company {shlex.quote(company.strip())}")
cmd = " ".join(_cmd_parts)
st.code(cmd, language="bash")

st.markdown("""
<div style="color:#8a9bb0; font-size:0.85rem; line-height:1.7; margin-top:-6px;">
    1. Open a Terminal.<br>
    2. Paste the command above, hit <b>Enter</b>.<br>
    3. Chromium opens. Log in via Okta Verify if needed, then press <b>Enter</b> in the terminal to start.<br>
    4. Progress streams live; results save to <code>results.csv</code> after every row.<br>
    5. When it's done, refresh this dashboard to see the results below.
</div>
""", unsafe_allow_html=True)

st.caption("If Okta login is required, use the terminal command above instead.")
if st.button("Run Now", type="primary", use_container_width=True, key="sa_run_now"):
    _run_cmd = ["python3", str(RUN_SCRIPT)]
    if (cid or "").strip():
        _run_cmd += ["--cid", cid.strip()]
    if (company or "").strip():
        _run_cmd += ["--company", company.strip()]
    with st.spinner("Running state amendment automation..."):
        _proc = subprocess.run(_run_cmd, capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR))
    if _proc.returncode == 0:
        render_alert("sa", "ok", "✓ RUN COMPLETE", "Automation finished successfully. Results are below.")
    else:
        render_alert("sa", "err", "⚠ RUN FAILED", f"Exit code {_proc.returncode}. Check terminal output for details.")
    st.rerun()

# ---------------------------------------------------------------------------
# Results viewer
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📊 Last Run Results")

if st.button("Refresh Results", key="sa_refresh"):
    st.rerun()

if not RESULTS_PATH.exists():
    render_alert("sa", "info", "NO RESULTS YET",
                 "Save rows above and run the command to populate this panel.")
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
        ph_n  = int((df["Status"] == "placeholder").sum())
        nf_n  = int((df["Status"] == "not_found").sum())
        err_n = total - ok_n - ph_n - nf_n

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Processed", total)
        m2.metric("Successful", ok_n)
        m3.metric("Placeholder", ph_n)
        m4.metric("Not Found",  nf_n)
        m5.metric("Errors",     err_n)

        filter_mode = st.radio(
            "Show",
            ["All", "Failures only", "Successes only"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if filter_mode == "Failures only":
            display_df = df[~df["Status"].isin(["ok", "placeholder"])]
        elif filter_mode == "Successes only":
            display_df = df[df["Status"] == "ok"]
        else:
            display_df = df

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=420)

        if FAILED_PATH.exists() and FAILED_PATH.stat().st_size:
            try:
                failed_rows = pd.read_csv(FAILED_PATH, dtype=str)
            except Exception:
                failed_rows = pd.DataFrame()
            if not failed_rows.empty:
                render_alert("sa", "warn",
                             f"⚠ {len(failed_rows)} row(s) FAILED",
                             "Edit below to remove rows you don't want to retry.")
                edited_csv = st.text_area(
                    "Failed rows (CSV format)", value=failed_rows.to_csv(index=False),
                    height=150, key="sa_retry_edit")
                retry_cmd = f"python3 {RUN_SCRIPT} {FAILED_PATH}"
                st.code(retry_cmd, language="bash")
                st.caption("Tip: a succeeded retry overwrites its row in results.csv.")
                if st.button("Retry Now", type="primary", key="sa_retry_btn"):
                    FAILED_PATH.write_text(edited_csv)
                    _retry_cmd = ["python3", str(RUN_SCRIPT), str(FAILED_PATH)]
                    with st.spinner(f"Retrying {len(failed_rows)} row(s)..."):
                        _rproc = subprocess.run(_retry_cmd, capture_output=True, text=True, timeout=600, cwd=str(SCRIPT_DIR))
                    if _rproc.returncode == 0:
                        render_alert("sa", "ok", "✓ RETRY COMPLETE", "All retried rows processed.")
                    else:
                        render_alert("sa", "err", "⚠ RETRY FAILED", f"Exit code {_rproc.returncode}.")
                    st.rerun()
    else:
        render_alert("sa", "info", "RESULTS FILE IS EMPTY", "")
