import io
import csv
from datetime import date, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="FICA Adjustment", layout="wide")
st.title("FICA Adjustment")

with st.sidebar:
    if st.button("Clear Data", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()

# Hide +/- stepper buttons on all number inputs
st.markdown("""
<style>
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SS_WAGE_BASES = {
    2023: 160_200,
    2024: 168_600,
    2025: 176_100,
    2026: 184_500,
}
ADD_MEDICARE_THRESH = 200_000
ADD_MEDICARE_RATE   = 0.009

# ---------------------------------------------------------------------------
# Helper: quarter-end date adjusted to previous Friday if on a weekend
# ---------------------------------------------------------------------------
_QUARTER_ENDS = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}

def quarter_end_date(year, qnum):
    month, day = _QUARTER_ENDS[qnum]
    d = date(year, month, day)
    if d.weekday() == 5:    # Saturday → Friday
        d -= timedelta(days=1)
    elif d.weekday() == 6:  # Sunday → Friday
        d -= timedelta(days=2)
    return d

YEARS = [2026, 2025, 2024, 2023]

COLS = [
    "account_type", "entry_type", "adjustment_date", "amount",
    "cid", "tax_code", "member_id", "taxable_amount", "subj_gross",
    "adjusted_gross", "adjusted_supl_gross", "gross_earnings_amount",
    "reference_type", "reference_id", "notes",
]

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_refund, tab_debit = st.tabs(["FICA Refund", "FICA Debit"])

# -----------------------------------------------------------------------
# TAB 1 — FICA Refund
# -----------------------------------------------------------------------
with tab_refund:
    if "selected_year" not in st.session_state:
        st.session_state.selected_year = 2026
    if "year_version" not in st.session_state:
        st.session_state.year_version = 0

    def on_year_change():
        new_year = st.session_state.year_selector
        st.session_state.selected_year = new_year
        st.session_state.year_version += 1
        new_v = st.session_state.year_version
        if "quarters" in st.session_state:
            for q in st.session_state.quarters:
                new_date = quarter_end_date(new_year, q["qnum"])
                q["adj_date"] = new_date
                st.session_state[f"adj_date_{q['qnum']}_v{new_v}"] = new_date

    if "member_id" not in st.session_state:
        st.session_state.member_id = ""
    if "company_id" not in st.session_state:
        st.session_state.company_id = ""
    if "notes" not in st.session_state:
        st.session_state.notes = ""

    mid_col, cid_col, yr_col = st.columns([1, 1, 1])
    with mid_col:
        st.session_state.member_id = st.text_input("Member ID", value=st.session_state.member_id, max_chars=20)
    with cid_col:
        st.session_state.company_id = st.text_input("Company ID", value=st.session_state.company_id, max_chars=20)
    with yr_col:
        st.selectbox("Tax Year", YEARS, index=YEARS.index(st.session_state.selected_year),
                     key="year_selector", on_change=on_year_change)

    st.divider()

    if "quarters" not in st.session_state:
        yr = st.session_state.selected_year
        st.session_state.quarters = [
            {"qnum": n, "ss_wages": 0.0, "ss_tax": 0.0, "med_wages": 0.0, "med_tax": 0.0, "futa_wages": 0.0, "futa_tax": 0.0, "adj_date": quarter_end_date(yr, n)}
            for n in [1, 2, 3, 4]
        ]

    def remove_quarter(idx):
        st.session_state.quarters.pop(idx)

    for i, q in enumerate(st.session_state.quarters):
        qn = q["qnum"]
        with st.expander(f"Q{qn} — {q['adj_date'].strftime('%m/%d/%Y')}", expanded=(i == 0)):
            ss_col, med_col, futa_col = st.columns(3)
            with ss_col:
                st.caption("**Social Security**")
                q["ss_wages"] = st.number_input("SS Wages ($)", min_value=0.0, value=q["ss_wages"], step=0.01, format="%.2f", key=f"ss_wages_{qn}")
                q["ss_tax"]   = st.number_input("SS Tax ($)",   min_value=0.0, value=q["ss_tax"],   step=0.01, format="%.2f", key=f"ss_tax_{qn}")
            with med_col:
                st.caption("**Medicare**")
                q["med_wages"] = st.number_input("Medicare Wages ($)", min_value=0.0, value=q["med_wages"], step=0.01, format="%.2f", key=f"med_wages_{qn}")
                q["med_tax"]   = st.number_input("Medicare Tax ($)",   min_value=0.0, value=q["med_tax"],   step=0.01, format="%.2f", key=f"med_tax_{qn}")
            with futa_col:
                st.caption("**FUTA**")
                q["futa_wages"] = st.number_input("FUTA Wages ($)", min_value=0.0, value=q["futa_wages"], step=0.01, format="%.2f", key=f"futa_wages_{qn}")
                q["futa_tax"]   = st.number_input("FUTA Tax ($)",   min_value=0.0, value=q["futa_tax"],   step=0.01, format="%.2f", key=f"futa_tax_{qn}")

            _dk = f"adj_date_{qn}_v{st.session_state.year_version}"
            _di_kwargs = {} if _dk in st.session_state else {"value": q["adj_date"]}
            q["adj_date"] = st.date_input("Adjustment Date", format="MM/DD/YYYY", key=_dk, **_di_kwargs)

            if len(st.session_state.quarters) > 1:
                st.button(f"Remove Q{qn}", key=f"remove_{qn}", on_click=remove_quarter, args=(i,))

    if st.button("+ Add Quarter", use_container_width=True):
        existing = {q["qnum"] for q in st.session_state.quarters}
        next_q = next((n for n in [1, 2, 3, 4] if n not in existing), None)
        if next_q is not None:
            st.session_state.quarters.append({
                "qnum": next_q,
                "ss_wages": 0.0, "ss_tax": 0.0,
                "med_wages": 0.0, "med_tax": 0.0,
                "futa_wages": 0.0, "futa_tax": 0.0,
                "adj_date": quarter_end_date(st.session_state.selected_year, next_q),
            })
            st.session_state.quarters.sort(key=lambda q: q["qnum"])
            st.rerun()

    # Tax rate validation
    _refund_alerts = []
    for q in st.session_state.quarters:
        qn = q["qnum"]
        ss_expected   = round(q["ss_wages"]   * 0.062,  2)
        med_expected  = round(q["med_wages"]  * 0.0145, 2)
        futa_expected = round(q["futa_wages"] * 0.006,  2)
        if abs(q["ss_tax"] - ss_expected) > 0.10:
            _refund_alerts.append(f"Q{qn}: SS Tax is ${q['ss_tax']:.2f} but expected ${ss_expected:.2f} (6.2% of ${q['ss_wages']:,.2f})")
        if abs(q["med_tax"] - med_expected) > 0.10:
            _refund_alerts.append(f"Q{qn}: Medicare Tax is ${q['med_tax']:.2f} but expected ${med_expected:.2f} (1.45% of ${q['med_wages']:,.2f})")
        if q["futa_wages"] > 0 or q["futa_tax"] > 0:
            if abs(q["futa_tax"] - futa_expected) > 0.10:
                _refund_alerts.append(f"Q{qn}: FUTA Tax is ${q['futa_tax']:.2f} but expected ${futa_expected:.2f} (0.6% of ${q['futa_wages']:,.2f})")
    if _refund_alerts:
        alerts_html = "".join(
            f'<p style="margin:4px 0; font-size:0.9rem; color:#b45309;">&#9888; {a}</p>'
            for a in _refund_alerts
        )
        st.markdown(
            f'<div style="background:#fffbeb; border-left:3px solid #b45309; padding:10px 14px; border-radius:4px; margin-bottom:8px;">'
            f'<p style="margin:0 0 6px 0; font-size:0.85rem; font-weight:600; color:#b45309;">Review the following values before downloading:</p>'
            f'{alerts_html}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.subheader("Notes")
    st.session_state.notes = st.text_area(
        "Notes", value=st.session_state.notes, height=80,
        label_visibility="collapsed", placeholder="Add any notes here...",
    )

    st.divider()

    def build_quarter_rows(q, cid, mid, notes):
        adj_date_str = q["adj_date"].strftime("%m/%d/%Y")
        ss_wages, ss_tax     = q["ss_wages"], q["ss_tax"]
        med_wages, med_tax   = q["med_wages"], q["med_tax"]
        futa_wages, futa_tax = q["futa_wages"], q["futa_tax"]

        def tax_row(tax_code, amount, wages):
            return {
                "account_type": "Clearing", "entry_type": "Debit",
                "adjustment_date": adj_date_str, "amount": amount,
                "cid": cid, "tax_code": tax_code, "member_id": mid,
                "taxable_amount": wages, "subj_gross": 0.0,
                "adjusted_gross": wages, "adjusted_supl_gross": 0.0,
                "gross_earnings_amount": 0.0,
                "reference_type": "x", "reference_id": 1, "notes": notes,
            }

        return [
            tax_row("00-403", ss_tax,   ss_wages),
            tax_row("00-404", ss_tax,   ss_wages),
            tax_row("00-406", med_tax,  med_wages),
            tax_row("00-407", med_tax,  med_wages),
            *([tax_row("00-402", futa_tax, futa_wages)] if futa_tax > 0 or futa_wages > 0 else []),
            {
                "account_type": "Member", "entry_type": "Credit",
                "adjustment_date": adj_date_str, "amount": round(ss_tax + med_tax, 2),
                "cid": cid, "tax_code": "", "member_id": mid,
                "taxable_amount": "", "subj_gross": "",
                "adjusted_gross": "", "adjusted_supl_gross": "",
                "gross_earnings_amount": "",
                "reference_type": "x", "reference_id": 1, "notes": notes,
            },
            {
                "account_type": "Company", "entry_type": "Credit",
                "adjustment_date": adj_date_str, "amount": round(ss_tax + med_tax + futa_tax, 2),
                "cid": cid, "tax_code": "", "member_id": "",
                "taxable_amount": "", "subj_gross": "",
                "adjusted_gross": "", "adjusted_supl_gross": "",
                "gross_earnings_amount": "",
                "reference_type": "", "reference_id": "", "notes": "",
            },
        ]

    cid   = st.session_state.company_id.lstrip("C").lstrip("c")
    mid   = st.session_state.member_id.lstrip("M").lstrip("m")
    notes = " ".join(st.session_state.notes.splitlines()).strip()

    all_rows = []
    for q in st.session_state.quarters:
        all_rows.extend(build_quarter_rows(q, cid, mid, notes))

    st.subheader("Preview")
    st.dataframe(pd.DataFrame(all_rows, columns=COLS), use_container_width=True)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLS)
    writer.writeheader()
    writer.writerows(all_rows)
    csv_data = buf.getvalue()

    missing = []
    if not st.session_state.member_id.strip():
        missing.append("Member ID")
    if not st.session_state.company_id.strip():
        missing.append("Company ID")

    if missing:
        st.error(f"Please enter a {' and '.join(missing)} before downloading.")
    else:
        downloaded = st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{st.session_state.member_id} {st.session_state.company_id} FICA FUTA Refund.csv",
            mime="text/csv",
            use_container_width=True,
        )
        if downloaded:
            st.session_state.refund_csv_downloaded = True

    _active_quarters = [
        q for q in st.session_state.quarters
        if round(q["ss_tax"] + q["med_tax"], 2) > 0 or round(q["ss_tax"] + q["med_tax"] + q["futa_tax"], 2) > 0
    ]

    if _active_quarters:
        st.divider()
        st.subheader("CS Tools Adjustment Summary")

        st.caption("Paste a CS Tools link for each quarter to make the header clickable")
        for q in _active_quarters:
            st.text_input(f"Q{q['qnum']} CS Tools Link", placeholder="Paste link here...", key=f"refund_q{q['qnum']}_link", label_visibility="visible")
        st.text_input("Credit Date", placeholder="e.g. 01/15/2025", key="refund_credit_date", label_visibility="visible")

        st.divider()

        _credit_date = st.session_state.get("refund_credit_date", "").strip() or "XXXXX"
        _summary_html = '<div style="font-size:0.9rem; line-height:1.8;">'
        if len(_active_quarters) == 1:
            _summary_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustment has been completed and can be viewed below:</p>'
        elif len(_active_quarters) >= 2:
            _summary_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustments have been completed and can be viewed below:</p>'
        for q in _active_quarters:
            qn          = q["qnum"]
            member_amt  = round(q["ss_tax"] + q["med_tax"], 2)
            company_amt = round(q["ss_tax"] + q["med_tax"] + q["futa_tax"], 2)
            url         = st.session_state.get(f"refund_q{qn}_link", "").strip()
            date_val    = _credit_date
            header      = (f'<a href="{url}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">Q{qn} ADJ in CS Tools</a>'
                           if url else f'<strong>Q{qn} ADJ in CS Tools</strong>')
            _summary_html += (
                f'<p style="margin:0 0 8px 0; line-height:1.4;">'
                f'{header}<br>'
                f'Employee Credit: ${member_amt:,.2f} on {date_val}<br>'
                f'Employer Credit: ${company_amt:,.2f} on {date_val}'
                f'</p>'
            )
        if st.session_state.selected_year < date.today().year:
            _summary_html += '<p style="margin:0; line-height:1.4;">The W-2c has been generated and can be viewed in the member documents center.</p>'
        _summary_html += '</div>'

        st.markdown(_summary_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------
# TAB 2 — FICA Debit
# -----------------------------------------------------------------------
with tab_debit:
    if "ficad_selected_year" not in st.session_state:
        st.session_state.ficad_selected_year = 2026
    if "ficad_year_version" not in st.session_state:
        st.session_state.ficad_year_version = 0

    def on_ficad_year_change():
        new_year = st.session_state.ficad_year_select
        st.session_state.ficad_selected_year = new_year
        st.session_state.ficad_year_version += 1
        new_v = st.session_state.ficad_year_version
        if "ficad_quarters" in st.session_state:
            for q in st.session_state.ficad_quarters:
                new_date = quarter_end_date(new_year, q["qnum"])
                q["adj_date"] = new_date
                st.session_state[f"ficad_adj_date_{q['qnum']}_v{new_v}"] = new_date

    if "ficad_member_id" not in st.session_state:
        st.session_state.ficad_member_id = ""
    if "ficad_company_id" not in st.session_state:
        st.session_state.ficad_company_id = ""
    if "ficad_notes" not in st.session_state:
        st.session_state.ficad_notes = ""
    if "ficad_debit_member" not in st.session_state:
        st.session_state.ficad_debit_member = "Yes"
    if "ficad_fica_only" not in st.session_state:
        st.session_state.ficad_fica_only = "No"

    _mid_col, _cid_col, _yr_col, _dm_col, _fo_col = st.columns([1, 1, 1, 0.5, 0.5])
    with _mid_col:
        st.session_state.ficad_member_id = st.text_input("Member ID", value=st.session_state.ficad_member_id, max_chars=20, key="ficad_member_id_input")
    with _cid_col:
        st.session_state.ficad_company_id = st.text_input("Company ID", value=st.session_state.ficad_company_id, max_chars=20, key="ficad_company_id_input")
    with _yr_col:
        st.selectbox("Tax Year", YEARS, index=YEARS.index(st.session_state.ficad_selected_year),
                     key="ficad_year_select", on_change=on_ficad_year_change)
    with _dm_col:
        st.session_state.ficad_debit_member = st.selectbox("Debit Member", ["Yes", "No"],
            index=["Yes", "No"].index(st.session_state.ficad_debit_member),
            key="ficad_debit_member_select")
    with _fo_col:
        st.session_state.ficad_fica_only = st.selectbox("FICA only", ["No", "Yes"],
            index=["No", "Yes"].index(st.session_state.ficad_fica_only),
            key="ficad_fica_only_select")

    st.divider()

    if "ficad_quarters" not in st.session_state:
        _yr = st.session_state.ficad_selected_year
        st.session_state.ficad_quarters = [
            {"qnum": n, "gross_wages": 0.0, "ss_wages": 0.0, "ss_tax": 0.0, "med_wages": 0.0, "med_tax": 0.0, "futa_wages": 0.0, "futa_tax": 0.0, "adj_date": quarter_end_date(_yr, n)}
            for n in [1, 2, 3, 4]
        ]

    def remove_ficad_quarter(idx):
        st.session_state.ficad_quarters.pop(idx)

    _FICAD_WAGE_BASES = {
        yr: {"ss": SS_WAGE_BASES[yr], "futa": 7_000}
        for yr in SS_WAGE_BASES
    }
    _ficad_year = st.session_state.get("ficad_year_select", st.session_state.ficad_selected_year)
    _ficad_limits = _FICAD_WAGE_BASES[_ficad_year]

    _ytd_gross = 0.0
    _ytd_ss_wages = _ytd_ss_tax = 0.0
    _ytd_med_wages = _ytd_med_tax = 0.0
    _ytd_add_med_wages = _ytd_add_med_tax = 0.0
    _ytd_futa_wages = _ytd_futa_tax = 0.0

    for i, q in enumerate(st.session_state.ficad_quarters):
        qn = q["qnum"]
        if "gross_wages" not in q:
            q["gross_wages"] = q.get("ss_wages", 0.0)
        with st.expander(f"Q{qn} — {q['adj_date'].strftime('%m/%d/%Y')}", expanded=(i == 0)):
            gross_col, ss_col, med_col, futa_col, ytd_col = st.columns([1, 1, 1, 1, 1])
            with gross_col:
                st.caption("**Gross**")
                q["gross_wages"] = st.number_input("Gross Wages ($)", min_value=0.0, value=q["gross_wages"], step=0.01, format="%.2f", key=f"ficad_gross_wages_{qn}")

            # SS and FUTA — capped at annual wage base
            _ss_rem   = max(0.0, _ficad_limits["ss"]   - _ytd_ss_wages)
            _futa_rem = max(0.0, _ficad_limits["futa"] - _ytd_futa_wages)
            q["ss_wages"]   = round(min(q["gross_wages"], _ss_rem),   2)
            q["futa_wages"] = round(min(q["gross_wages"], _futa_rem), 2)
            q["ss_tax"]     = round(q["ss_wages"]   * 0.062, 2)
            q["futa_tax"]   = round(q["futa_wages"] * 0.006, 2)

            # Regular Medicare — no wage base cap, applies to all wages
            q["med_wages"] = q["gross_wages"]
            q["med_tax"]   = round(q["med_wages"] * 0.0145, 2)

            # Additional Medicare — 0.9% on gross wages exceeding $200k YTD threshold
            _ytd_gross_after   = _ytd_gross + q["gross_wages"]
            _prev_over         = max(0.0, _ytd_gross       - ADD_MEDICARE_THRESH)
            _curr_over         = max(0.0, _ytd_gross_after - ADD_MEDICARE_THRESH)
            q["add_med_wages"] = round(max(0.0, _curr_over - _prev_over), 2)
            q["add_med_tax"]   = round(q["add_med_wages"] * ADD_MEDICARE_RATE, 2)

            with ss_col:
                st.caption("**Social Security**")
                st.write(f"SS Wages: ${q['ss_wages']:,.2f}")
                st.write(f"SS Tax: ${q['ss_tax']:,.2f}")
            with med_col:
                st.caption("**Medicare**")
                st.write(f"Medicare Wages: ${q['med_wages']:,.2f}")
                st.write(f"Medicare Tax: ${q['med_tax']:,.2f}")
            with futa_col:
                st.caption("**FUTA**")
                st.write(f"FUTA Wages: ${q['futa_wages']:,.2f}")
                st.write(f"FUTA Tax: ${q['futa_tax']:,.2f}")

            _ytd_gross         += q["gross_wages"]
            _ytd_ss_wages      += q["ss_wages"]
            _ytd_ss_tax        += q["ss_tax"]
            _ytd_med_wages     += q["med_wages"]
            _ytd_med_tax       += q["med_tax"]
            _ytd_add_med_wages += q["add_med_wages"]
            _ytd_add_med_tax   += q["add_med_tax"]
            _ytd_futa_wages    += q["futa_wages"]
            _ytd_futa_tax      += q["futa_tax"]

            with ytd_col:
                st.caption(f"**YTD through Q{qn}**")
                st.write(f"Gross Wages: ${_ytd_gross:,.2f}")

                st.caption(f"**Social Security** (limit ${_ficad_limits['ss']:,.0f})")
                st.write(f"SS Wages: ${_ytd_ss_wages:,.2f}")
                st.write(f"SS Tax: ${_ytd_ss_tax:,.2f}")

                st.caption("**Medicare**")
                st.write(f"Med Wages: ${_ytd_med_wages:,.2f}")
                st.write(f"Med Tax (1.45%): ${_ytd_med_tax:,.2f}")

                if _ytd_add_med_wages > 0:
                    st.caption("**Additional Medicare**")
                    st.write(f"Add. Med Wages: ${_ytd_add_med_wages:,.2f}")
                    st.write(f"Add. Med Tax (0.9%): ${_ytd_add_med_tax:,.2f}")

                st.caption(f"**FUTA** (limit ${_ficad_limits['futa']:,.0f})")
                st.write(f"FUTA Wages: ${_ytd_futa_wages:,.2f}")
                st.write(f"FUTA Tax (0.6%): ${_ytd_futa_tax:,.2f}")

            _dk = f"ficad_adj_date_{qn}_v{st.session_state.ficad_year_version}"
            _di_kwargs = {} if _dk in st.session_state else {"value": q["adj_date"]}
            q["adj_date"] = st.date_input("Adjustment Date", format="MM/DD/YYYY", key=_dk, **_di_kwargs)

            if len(st.session_state.ficad_quarters) > 1:
                st.button(f"Remove Q{qn}", key=f"ficad_remove_{qn}", on_click=remove_ficad_quarter, args=(i,))

    if st.button("+ Add Quarter", use_container_width=True, key="ficad_add_quarter"):
        _existing = {q["qnum"] for q in st.session_state.ficad_quarters}
        _next = next((n for n in [1, 2, 3, 4] if n not in _existing), None)
        if _next is not None:
            st.session_state.ficad_quarters.append({
                "qnum": _next,
                "gross_wages": 0.0,
                "ss_wages": 0.0, "ss_tax": 0.0,
                "med_wages": 0.0, "med_tax": 0.0,
                "futa_wages": 0.0, "futa_tax": 0.0,
                "adj_date": quarter_end_date(st.session_state.ficad_selected_year, _next),
            })
            st.session_state.ficad_quarters.sort(key=lambda q: q["qnum"])
            st.rerun()

    st.divider()
    st.subheader("Notes")
    st.session_state.ficad_notes = st.text_area(
        "Notes", value=st.session_state.ficad_notes, height=80,
        label_visibility="collapsed", placeholder="Add any notes here...",
        key="ficad_notes_input",
    )

    st.divider()

    def build_ficad_quarter_rows(q, cid, mid, notes, debit_member, fica_only=False):
        adj_date_str = q["adj_date"].strftime("%m/%d/%Y")
        ss_wages, ss_tax         = q["ss_wages"], q["ss_tax"]
        med_wages, med_tax       = q["med_wages"], q["med_tax"]
        futa_wages, futa_tax     = q["futa_wages"], q["futa_tax"]
        add_med_wages            = q.get("add_med_wages", 0.0)
        add_med_tax              = q.get("add_med_tax", 0.0)

        member_amount  = round(ss_tax + med_tax + add_med_tax, 2)
        company_amount = round(ss_tax + med_tax, 2) if fica_only else round(ss_tax + med_tax + futa_tax, 2)

        def tax_row(tax_code, amount, wages):
            return {
                "account_type": "Clearing", "entry_type": "Credit",
                "adjustment_date": adj_date_str, "amount": amount,
                "cid": cid, "tax_code": tax_code, "member_id": mid,
                "taxable_amount": wages, "subj_gross": 0.0,
                "adjusted_gross": wages, "adjusted_supl_gross": 0.0,
                "gross_earnings_amount": 0.0,
                "reference_type": "x", "reference_id": 1, "notes": notes,
            }

        clearing_rows = [
            *([tax_row("00-403", ss_tax,      ss_wages)]      if ss_tax      > 0 or ss_wages      > 0 else []),
            *([tax_row("00-404", ss_tax,      ss_wages)]      if ss_tax      > 0 or ss_wages      > 0 else []),
            tax_row("00-406", med_tax,  med_wages),
            tax_row("00-407", med_tax,  med_wages),
            *([tax_row("00-402", futa_tax,    futa_wages)]    if (futa_tax   > 0 or futa_wages    > 0) and not fica_only else []),
            *([tax_row("00-901", add_med_tax, add_med_wages)] if add_med_tax > 0 or add_med_wages > 0 else []),
        ]

        if debit_member:
            return [
                *clearing_rows,
                {
                    "account_type": "Member", "entry_type": "Debit",
                    "adjustment_date": adj_date_str, "amount": member_amount,
                    "cid": cid, "tax_code": "", "member_id": mid,
                    "taxable_amount": "", "subj_gross": "",
                    "adjusted_gross": "", "adjusted_supl_gross": "",
                    "gross_earnings_amount": "",
                    "reference_type": "x", "reference_id": 1, "notes": notes,
                },
                {
                    "account_type": "Company", "entry_type": "Debit",
                    "adjustment_date": adj_date_str, "amount": company_amount,
                    "cid": cid, "tax_code": "", "member_id": "",
                    "taxable_amount": "", "subj_gross": "",
                    "adjusted_gross": "", "adjusted_supl_gross": "",
                    "gross_earnings_amount": "",
                    "reference_type": "", "reference_id": "", "notes": "",
                },
            ]
        else:
            return [
                *clearing_rows,
                {
                    "account_type": "Company", "entry_type": "Debit",
                    "adjustment_date": adj_date_str, "amount": round(member_amount + company_amount, 2),
                    "cid": cid, "tax_code": "", "member_id": "",
                    "taxable_amount": "", "subj_gross": "",
                    "adjusted_gross": "", "adjusted_supl_gross": "",
                    "gross_earnings_amount": "",
                    "reference_type": "", "reference_id": "", "notes": "",
                },
            ]

    _ficad_cid   = st.session_state.ficad_company_id.lstrip("C").lstrip("c")
    _ficad_mid   = st.session_state.ficad_member_id.lstrip("M").lstrip("m")
    _ficad_notes = " ".join(st.session_state.ficad_notes.splitlines()).strip()
    _ficad_debit_member = st.session_state.ficad_debit_member == "Yes"
    _ficad_fica_only    = st.session_state.ficad_fica_only == "Yes"

    _ficad_rows = []
    for q in st.session_state.ficad_quarters:
        _ficad_rows.extend(build_ficad_quarter_rows(q, _ficad_cid, _ficad_mid, _ficad_notes, _ficad_debit_member, _ficad_fica_only))

    st.subheader("Preview")
    st.dataframe(pd.DataFrame(_ficad_rows, columns=COLS), use_container_width=True)

    ficad_buf = io.StringIO()
    ficad_writer = csv.DictWriter(ficad_buf, fieldnames=COLS)
    ficad_writer.writeheader()
    ficad_writer.writerows(_ficad_rows)
    ficad_csv = ficad_buf.getvalue()

    _ficad_missing = []
    if not st.session_state.ficad_member_id.strip():
        _ficad_missing.append("Member ID")
    if not st.session_state.ficad_company_id.strip():
        _ficad_missing.append("Company ID")

    if _ficad_missing:
        st.error(f"Please enter a {' and '.join(_ficad_missing)} before downloading.")
    else:
        st.download_button(
            label="Download CSV",
            data=ficad_csv,
            file_name=f"{st.session_state.ficad_member_id} {st.session_state.ficad_company_id} FICA Debit.csv",
            mime="text/csv",
            use_container_width=True,
            key="ficad_download_csv",
        )

    _ficad_active_quarters = [
        q for q in st.session_state.ficad_quarters
        if round(q["ss_tax"] + q["med_tax"], 2) > 0
    ]
    if _ficad_active_quarters:
        st.divider()
        st.subheader("CS Tools Adjustment Summary")
        st.caption("Paste a CS Tools link for each quarter to make the header clickable")
        for q in _ficad_active_quarters:
            st.text_input(f"Q{q['qnum']} CS Tools Link", placeholder="Paste link here...", key=f"ficad_q{q['qnum']}_link", label_visibility="visible")
        st.text_input("Credit Date", placeholder="e.g. 01/15/2025", key="ficad_credit_date", label_visibility="visible")

        st.divider()

        _ficad_debit_credit_date = st.session_state.get("ficad_credit_date", "").strip() or "XXXXX"
        _ficad_debit_fica_only   = st.session_state.ficad_fica_only == "Yes"
        _ficad_debit_html = '<div style="font-size:0.9rem; line-height:1.8;">'
        if len(_ficad_active_quarters) == 1:
            _ficad_debit_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustment has been completed and can be viewed below:</p>'
        elif len(_ficad_active_quarters) >= 2:
            _ficad_debit_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustments have been completed and can be viewed below:</p>'
        for q in _ficad_active_quarters:
            qn          = q["qnum"]
            member_amt  = round(q["ss_tax"] + q["med_tax"] + q.get("add_med_tax", 0.0), 2)
            company_amt = round(q["ss_tax"] + q["med_tax"], 2) if _ficad_debit_fica_only else round(q["ss_tax"] + q["med_tax"] + q["futa_tax"], 2)
            url         = st.session_state.get(f"ficad_q{qn}_link", "").strip()
            date_val    = _ficad_debit_credit_date
            header      = (f'<a href="{url}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">Q{qn} ADJ in CS Tools</a>'
                           if url else f'<strong>Q{qn} ADJ in CS Tools</strong>')
            _ficad_debit_html += (
                f'<p style="margin:0 0 8px 0; line-height:1.4;">'
                f'{header}<br>'
                f'Employee Debit: ${member_amt:,.2f} on {date_val}<br>'
                f'Employer Debit: ${company_amt:,.2f} on {date_val}'
                f'</p>'
            )
        if st.session_state.ficad_selected_year < date.today().year:
            _ficad_debit_html += '<p style="margin:0; line-height:1.4;">The W-2c has been generated and can be viewed in the member documents center.</p>'
        _ficad_debit_html += '</div>'

        st.markdown(_ficad_debit_html, unsafe_allow_html=True)
