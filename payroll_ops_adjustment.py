import io
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# SUI taxable wage bases  (hardcoded — sourced from uploaded table)
# ---------------------------------------------------------------------------
SUI_WAGE_BASES = {
    "Alabama":              {2025: 8000,   2026: 8000},
    "Alaska":               {2025: 51700,  2026: 54200},
    "Arizona":              {2025: 8000,   2026: 8000},
    "Arkansas":             {2025: 7000,   2026: 7000},
    "California":           {2025: 7000,   2026: 7000},
    "Colorado":             {2025: 27200,  2026: 30600},
    "Connecticut":          {2025: 26100,  2026: 27000},
    "Delaware":             {2025: 12500,  2026: 14500},
    "District of Columbia": {2025: 9000,   2026: 9000},
    "Florida":              {2025: 7000,   2026: 7000},
    "Georgia":              {2025: 9500,   2026: 9500},
    "Hawaii":               {2025: 62000,  2026: 64500},
    "Idaho":                {2025: 55300,  2026: 58300},
    "Illinois":             {2025: 13916,  2026: 14250},
    "Indiana":              {2025: 9500,   2026: 9500},
    "Iowa":                 {2025: 39500,  2026: 20400},
    "Kansas":               {2025: 14000,  2026: 15100},
    "Kentucky":             {2025: 11700,  2026: 12000},
    "Louisiana":            {2025: 7700,   2026: 7000},
    "Maine":                {2025: 12000,  2026: 12000},
    "Maryland":             {2025: 8500,   2026: 8500},
    "Massachusetts":        {2025: 15000,  2026: 15000},
    "Michigan":             {2025: 9000,   2026: 9000},
    "Minnesota":            {2025: 43000,  2026: 44000},
    "Mississippi":          {2025: 14000,  2026: 14000},
    "Missouri":             {2025: 9500,   2026: 9000},
    "Montana":              {2025: 45100,  2026: 47300},
    "Nebraska":             {2025: 9000,   2026: 9000},
    "Nevada":               {2025: 41800,  2026: 43700},
    "New Hampshire":        {2025: 14000,  2026: 14000},
    "New Jersey":           {2025: 43300,  2026: 44800},
    "New Mexico":           {2025: 33200,  2026: 34800},
    "New York":             {2025: 12800,  2026: 17600},
    "North Carolina":       {2025: 32600,  2026: 34200},
    "North Dakota":         {2025: 45100,  2026: 46600},
    "Ohio":                 {2025: 9000,   2026: 9000},
    "Oklahoma":             {2025: 28200,  2026: 25000},
    "Oregon":               {2025: 54300,  2026: 56700},
    "Pennsylvania":         {2025: 10000,  2026: 10000},
    "Puerto Rico":          {2025: 7000,   2026: 7000},
    "Rhode Island":         {2025: 29800,  2026: 30800},
    "South Carolina":       {2025: 14000,  2026: 14000},
    "South Dakota":         {2025: 15000,  2026: 15000},
    "Tennessee":            {2025: 7000,   2026: 7000},
    "Texas":                {2025: 9000,   2026: 9000},
    "Utah":                 {2025: 48900,  2026: 50700},
    "Vermont":              {2025: 14800,  2026: 15400},
    "Virginia":             {2025: 8000,   2026: 8000},
    "Virgin Islands":       {2025: 31100,  2026: 32100},
    "Washington":           {2025: 72800,  2026: 78200},
    "West Virginia":        {2025: 9500,   2026: 9500},
    "Wisconsin":            {2025: 14000,  2026: 14000},
    "Wyoming":              {2025: 32400,  2026: 33800},
    "FUTA":                 {2025: 7000,   2026: 7000},
}

def get_sui_wage_base(state, year):
    return SUI_WAGE_BASES.get(state, {}).get(year)

# ---------------------------------------------------------------------------
# Tax constants
# ---------------------------------------------------------------------------
SS_WAGE_BASES = {
    2023: 160_200,
    2024: 168_600,
    2025: 176_100,
    2026: 184_500,
}

SS_RATE              = 0.062
MEDICARE_RATE        = 0.0145
ADD_MEDICARE_RATE    = 0.009
ADD_MEDICARE_THRESH  = 200_000

# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------
def calc_taxes(gross, ytd_ss, ytd_med, ss_wage_base, custom_rates):
    # Social Security
    ss_room     = max(0.0, ss_wage_base - ytd_ss)
    ss_taxable  = min(gross, ss_room)
    ss_amount   = round(ss_taxable * SS_RATE, 2)

    # Medicare
    med_amount  = round(gross * MEDICARE_RATE, 2)

    # Additional Medicare (0.9% on wages over $200k YTD)
    ytd_after        = ytd_med + gross
    prev_over        = max(0.0, ytd_med    - ADD_MEDICARE_THRESH)
    curr_over        = max(0.0, ytd_after  - ADD_MEDICARE_THRESH)
    add_med_taxable  = max(0.0, curr_over - prev_over)
    add_med_amount   = round(add_med_taxable * ADD_MEDICARE_RATE, 2)

    # FUTA (employer only — does not affect employee net pay)
    futa_room     = max(0.0, 7000.0 - ytd_med)
    futa_taxable  = min(gross, futa_room)
    futa_amount   = round(futa_taxable * 0.006, 2)

    # Custom taxes — tuple format: (name, code, rate, limit_room, ytd_display)
    custom_items = []
    for name, code, rate, limit_room, ytd_display in custom_rates:
        taxable = min(gross, limit_room) if limit_room is not None else gross
        amt     = round(taxable * rate / 100, 2)
        custom_items.append((name, code, rate, taxable, amt, ytd_display))

    total_tax = ss_amount + med_amount + add_med_amount + sum(item[4] for item in custom_items)
    net       = round(gross - total_tax, 2)

    return {
        "ss_taxable":      ss_taxable,
        "ss_amount":       ss_amount,
        "ss_room":         ss_room,
        "med_amount":      med_amount,
        "add_med_taxable": add_med_taxable,
        "add_med_amount":  add_med_amount,
        "futa_taxable":    futa_taxable,
        "futa_amount":     futa_amount,
        "custom_items":    custom_items,
        "total_tax":       round(total_tax, 2),
        "net":             net,
    }

def gross_up(desired_net, ytd_ss, ytd_med, ss_wage_base, custom_rates):
    """Binary search: find gross that produces the desired net."""
    lo, hi = desired_net, desired_net * 10
    for _ in range(300):
        mid    = (lo + hi) / 2
        result = calc_taxes(mid, ytd_ss, ytd_med, ss_wage_base, custom_rates)
        diff   = result["net"] - desired_net
        if abs(diff) < 0.001:
            break
        if diff < 0:
            lo = mid
        else:
            hi = mid
    return round(mid, 2), calc_taxes(mid, ytd_ss, ytd_med, ss_wage_base, custom_rates)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fmt(n):
    return f"${n:,.2f}"

def fmtmd(n):
    """Dollar-escaped version for use inside st.info / st.markdown text."""
    return f"\\${n:,.2f}"

def render_tax_table(gross, ytd_med, ss_wage_base, result, employer_items=None):
    st.markdown("### Tax Detail")

    headers = ["Tax", "Tax Code", "YTD Taxable", "Subjected Gross", "Taxable Amount", "Tax Amount"]

    def th(label):
        align = "left" if label in ("Tax", "Tax Code") else "right"
        return f'<th style="text-align:{align}; padding:6px 8px; font-weight:600; border-bottom:2px solid #ccc; white-space:nowrap;">{label}</th>'

    def td(val, left=False):
        align = "left" if left else "right"
        return f'<td style="text-align:{align}; padding:6px 8px; font-variant-numeric:tabular-nums; white-space:nowrap; border-bottom:1px solid #f0f0f0;">{val}</td>'

    def tr(cells):
        return "<tr>" + "".join(cells) + "</tr>"

    adj = fmt(gross)
    rows = []

    # Federal - Employee Withholding (always shown; $0 when not selected in Additional Tax Rates)
    # new fmt: (name, code, rate, taxable, amt, ytd) len=6 | legacy len=5: (name, rate, taxable, amt, ytd)
    _fed_item    = next((item for item in result.get("custom_items", []) if item[0] == "Federal - Employee Withholding"), None)
    _fed_taxable = gross  # always show full wages as taxable regardless of whether the tax is selected
    _fed_amt     = (_fed_item[4] if len(_fed_item) >= 6 else _fed_item[3]) if _fed_item else 0.0
    rows.append(tr([
        td("Federal - Employee Withholding", left=True),
        td("00-400",                         left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(_fed_taxable)),
        td(fmt(_fed_amt)),
    ]))

    # Social Security Employee
    rows.append(tr([
        td("Social Security - Employee", left=True),
        td("00-403",                   left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(result["ss_taxable"])),
        td(fmt(result["ss_amount"])),
    ]))

    # Social Security Employer
    rows.append(tr([
        td("Social Security - Employer", left=True),
        td("00-404",                   left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(result["ss_taxable"])),
        td(fmt(result["ss_amount"])),
    ]))

    # Medicare Employee
    rows.append(tr([
        td("Medicare - Employee",    left=True),
        td("00-406",                 left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(gross)),
        td(fmt(result["med_amount"])),
    ]))

    # Additional Medicare Employee (only when applicable)
    if result["add_med_taxable"] > 0:
        rows.append(tr([
            td("Addt. Medicare - Employee", left=True),
            td("00-406",                  left=True),
            td(fmt(ytd_med)),
            td(adj),
            td(fmt(result["add_med_taxable"])),
            td(fmt(result["add_med_amount"])),
        ]))

    # Medicare Employer
    rows.append(tr([
        td("Medicare - Employer",    left=True),
        td("00-407",                 left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(gross)),
        td(fmt(result["med_amount"])),
    ]))

    # FUTA (employer only — always shown, $0 taxable when over the $7,000 wage base)
    rows.append(tr([
        td("FUTA",               left=True),
        td("00-402",             left=True),
        td(fmt(ytd_med)),
        td(adj),
        td(fmt(result.get("futa_taxable", 0))),
        td(fmt(result.get("futa_amount", 0))),
    ]))

    # Employee custom taxes (Federal - Employee Withholding has its own dedicated row above)
    for item in result.get("custom_items", []):
        if item[0] == "Federal - Employee Withholding":
            continue
        # new fmt: (name, code, rate, taxable, amt, ytd) len=6
        # legacy:  (name, rate, taxable, amt, ytd)       len=5
        if len(item) >= 6:
            name, code, rate, taxable, amt, ytd_display = item
        else:
            name, rate, taxable = item[0], item[1], item[2]
            amt         = item[3] if len(item) >= 4 else item[2]
            ytd_display = item[4] if len(item) >= 5 else None
            code        = DESC_TO_CODE.get(name, "")
        ytd_str = fmt(ytd_display) if ytd_display is not None else fmt(ytd_med)
        rows.append(tr([
            td(name,              left=True),
            td(code or "—",       left=True),
            td(ytd_str),
            td(adj),
            td(fmt(taxable)),
            td(fmt(amt)),
        ]))

    # Employer taxes (display only — not in gross up or net pay calc)
    # fmt: (name, code, rate, limit_room, ytd_display)
    for name, code, rate, limit_room, ytd_display in (employer_items or []):
        taxable = min(gross, limit_room) if limit_room is not None else gross
        amt     = round(taxable * rate / 100, 2)
        ytd_str = fmt(ytd_display) if ytd_display is not None else fmt(ytd_med)
        rows.append(tr([
            td(name,              left=True),
            td(code or "—",       left=True),
            td(ytd_str),
            td(adj),
            td(fmt(taxable)),
            td(fmt(amt)),
        ]))

    html = (
        '<div style="overflow-x:auto;">'
        '<table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:0.9rem;">'
        "<thead><tr>" + "".join(th(h) for h in headers) + "</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody>"
        "</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)

def render_breakdown(gross, result, ss_wage_base, ytd_ss):
    st.markdown("### Breakdown")

    def row(label, amount, rate="", note="", bold=False):
        amt_str  = f"<b>{amount}</b>" if bold else amount
        lbl_str  = f"<b>{label}</b>"  if bold else label
        note_str = f' <span style="color:#888; font-size:0.85em;">({note})</span>' if note else ""
        return f"""
        <tr style="border-bottom:1px solid #f0f0f0;">
          <td style="padding:7px 4px;">{lbl_str}{note_str}</td>
          <td style="text-align:right; padding:7px 8px; font-variant-numeric:tabular-nums; white-space:nowrap;">{amt_str}</td>
        </tr>"""

    html = """
    <table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:1rem;">
      <thead>
        <tr style="border-bottom:2px solid #ccc;">
          <th style="text-align:left; padding:6px 4px; font-weight:600;">Item</th>
          <th style="text-align:right; padding:6px 8px; font-weight:600;">Amount</th>
        </tr>
      </thead>
      <tbody>"""

    html += row("Gross Pay", fmt(gross))

    if result["ss_amount"] > 0:
        note = f"partial — {fmt(result['ss_taxable'])} taxable" if result["ss_taxable"] < gross else ""
        html += row("&minus; Social Security", fmt(-result["ss_amount"]), "6.20%", note)
    else:
        html += row("&minus; Social Security", "$0.00", "6.20%", "wage base met")

    html += row("&minus; Medicare", fmt(-result["med_amount"]), "1.45%")

    if result["add_med_amount"] > 0:
        html += row(
            "&minus; Additional Medicare",
            fmt(-result["add_med_amount"]),
            "0.90%",
            f"{fmt(result['add_med_taxable'])} over $200k threshold",
        )

    for item in result["custom_items"]:
        # format: (name, code, rate, taxable, amt, ytd_display) — len 6
        # legacy:  (name, rate, taxable, amt, ytd_display)       — len 5
        name = item[0]
        rate = item[2] if len(item) >= 6 else item[1]
        amt  = item[4] if len(item) >= 6 else (item[3] if len(item) >= 4 else item[2])
        if amt == 0:
            continue
        html += row(f"&minus; {name}", fmt(-amt), f"{rate:.2f}%")

    html += row("= Net Pay", fmt(result["net"]), bold=True)

    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # SS wage base callout
    remaining = max(0.0, ss_wage_base - ytd_ss)
    if remaining == 0:
        st.info(f"SS wage base of {fmtmd(ss_wage_base)} already met — no Social Security withheld.")
    elif result["ss_taxable"] < gross:
        st.info(
            f"SS wage base reached mid-payment: only {fmtmd(result['ss_taxable'])} of "
            f"{fmtmd(gross)} was subject to SS. Remaining room was {fmtmd(remaining)}."
        )

# ---------------------------------------------------------------------------
# Hardcoded tax code data
# ---------------------------------------------------------------------------
DESC_TO_CODE = {
    "Alabama - Employee Withholding": "01-450",
    "Alabama - Employer Employment Security Assessment": "01-461",
    "Alabama - Employer Unemployment": "01-459",
    "Alaska - Employee Unemployment": "02-458",
    "Alaska - Employer Unemployment": "02-459",
    "Arizona - Employee Withholding": "03-450",
    "Arizona - Employer Unemployment": "03-459",
    "Arkansas - Employee Withholding": "04-450",
    "Arkansas - Employer Unemployment": "04-459",
    "Aurora, - Employer OPT": "060050030-533",
    "California - Employee Disability": "05-466",
    "California - Employee Withholding": "05-450",
    "California - Employer Employment Training": "05-461",
    "California - Employer Unemployment": "05-459",
    "Colorado - Employee Withholding": "06-450",
    "Colorado - Employer Bond Repayment Assessment": "06-465",
    "Colorado - Employer Unemployment": "06-459",
    "Connecticut - Employee Withholding": "07-450",
    "Connecticut - Employer Unemployment": "07-459",
    "Delaware - Employee Withholding": "08-450",
    "Delaware - Employer Unemployment": "08-459",
    "Delaware - Employment Training Fund": "08-461",
    "Denver, Denver - Employer OPT": "060310140-533",
    "District of Columbia - Administrative Funding Assessment": "09-461",
    "District of Columbia - Employee Withholding": "09-450",
    "District of Columbia - Employer Unemployment": "09-459",
    "Federal - Employee Additional Medicare": "00-901",
    "Federal - Employee Medicare": "00-406",
    "Federal - Employee Social Security  (OASDI)": "00-403",
    "Federal - Employee Third Party Sick Pay Tax": "00-900",
    "Federal - Employee Withholding": "00-400",
    "Federal - Employer Medicare": "00-407",
    "Federal - Employer Social Security (OASDI)": "00-404",
    "Federal - Employer Unemployment": "00-402",
    "Florida - Employer Unemployment": "10-459",
    "Georgia - Employee Withholding": "11-450",
    "Georgia - Employer Administrative Assessment": "11-461",
    "Georgia - Employer Unemployment": "11-459",
    "Greenwood Village, Arapahoe - Employer OPT": "060050850-536",
    "Hawaii - Employee Withholding": "12-450",
    "Hawaii - Employer Employment & Training Assessment": "12-461",
    "Hawaii - Employer Unemployment": "12-459",
    "Idaho - Employee Withholding": "13-450",
    "Idaho - Employer Unemployment": "13-459",
    "Idaho - Employer Workforce Development": "13-461",
    "Illinois - Employee Withholding": "14-450",
    "Illinois - Employer Unemployment": "14-459",
    "Indiana - Employee Withholding": "15-450",
    "Indiana - Employer Unemployment": "15-459",
    "Iowa - Employee Withholding": "16-450",
    "Iowa - Employer Unemployment": "16-459",
    "Kansas - Employee Withholding": "17-450",
    "Kansas - Employer Unemployment": "17-459",
    "Kentucky - Employee Withholding": "18-450",
    "Kentucky - Employer Unemployment": "18-459",
    "Kentucky - Employer Unemployment Surcharge": "18-461",
    "Louisiana - Employee Withholding": "19-450",
    "Louisiana - Employer Unemployment": "19-459",
    "Maine - Competitive Skills Scholarship Fund Assessment": "20-461",
    "Maine - Employee Withholding": "20-450",
    "Maine - Employer Unemployment": "20-459",
    "Maryland - Employee Withholding": "21-450",
    "Maryland - Employer Unemployment": "21-459",
    "Massachusetts - Employee Withholding": "22-450",
    "Massachusetts - Employer Medical Assistance Contribution": "22-453",
    "Massachusetts - Employer Unemployment": "22-459",
    "Massachusetts - Workforce Training Fund": "22-461",
    "Michigan - Employee Withholding": "23-450",
    "Michigan - Employer Obligation Assessment": "23-461",
    "Michigan - Employer Unemployment": "23-459",
    "Minnesota - Employee Withholding": "24-450",
    "Minnesota - Employer Additional Unemployment Assessment": "24-465",
    "Minnesota - Employer Interest Assessment on Federal Loan": "24-463",
    "Minnesota - Employer Unemployment": "24-459",
    "Minnesota - Workforce Enhancement Fee": "24-461",
    "Mississippi - Employee Withholding": "25-450",
    "Mississippi - Employer Training Contribution": "25-461",
    "Mississippi - Employer Unemployment": "25-459",
    "Missouri - Employee Withholding": "26-450",
    "Missouri - Employer Unemployment": "26-459",
    "Montana - Administrative Fund Tax": "27-461",
    "Montana - Employee Withholding": "27-450",
    "Montana - Employer Unemployment": "27-459",
    "Nebraska - Employee Withholding": "28-450",
    "Nebraska - Employer Unemployment": "28-459",
    "Nevada - Employer Bond Contribution": "29-463",
    "Nevada - Employer Career Enhancement Program": "29-457",
    "Nevada - Employer Unemployment": "29-459",
    "New Hampshire - Administrative Contribution": "30-461",
    "New Hampshire - Employer Unemployment": "30-459",
    "New Jersey - Employee Disability": "31-466",
    "New Jersey - Employee Family Leave Insurance": "31-468",
    "New Jersey - Employee Unemployment": "31-458",
    "New Jersey - Employee Withholding": "31-450",
    "New Jersey - Employer Disability": "31-467",
    "New Jersey - Employer Unemployment": "31-459",
    "New Mexico - Employee Withholding": "32-450",
    "New Mexico - Employee Worker's Compensation Fee": "32-470",
    "New Mexico - Employer Unemployment": "32-459",
    "New Mexico - Employer Workers' Compensation Fee": "32-471",
    "New York - Employee Disability": "33-466",
    "New York - Employee Withholding": "33-450",
    "New York - Employer Unemployment": "33-459",
    "New York - Re-employment Service Fund": "33-461",
    "North Carolina - Employee Withholding": "34-450",
    "North Carolina - Employer Unemployment": "34-459",
    "North Dakota - Employee Withholding": "35-450",
    "North Dakota - Employer Unemployment": "35-459",
    "Ohio - Employee Withholding": "36-450",
    "Ohio - Employer Unemployment": "36-459",
    "Oklahoma - Employee Withholding": "37-450",
    "Oklahoma - Employer Unemployment": "37-459",
    "Oregon - Employee Withholding": "38-450",
    "Oregon - Employee Worker's Benefit Fund Assessment": "38-470",
    "Oregon - Employer Unemployment": "38-459",
    "Oregon - Employer Worker's Benefit Fund Assessment": "38-471",
    "Pennsylvania - Employee Unemployment": "39-458",
    "Pennsylvania - Employee Withholding": "39-450",
    "Pennsylvania - Employer Unemployment": "39-459",
    "Rhode Island - Employee Disability": "40-466",
    "Rhode Island - Employee Withholding": "40-450",
    "Rhode Island - Employer Job Development Assessment": "40-461",
    "Rhode Island - Employer Unemployment": "40-459",
    "South Carolina - Contingency Assessment": "41-463",
    "South Carolina - Employee Withholding": "41-450",
    "South Carolina - Employer Unemployment": "41-459",
    "South Dakota - Employer Investment Fee": "42-461",
    "South Dakota - Employer Unemployment": "42-459",
    "Tennessee - Employer Unemployment": "43-459",
    "Texas - Employer Obligation Assessment": "44-461",
    "Texas - Employer Unemployment": "44-459",
    "Texas - Employment & Training Assessment": "44-463",
    "U.S. Virgin Islands - Employer Unemployment": "78-459",
    "Utah - Employee Withholding": "45-450",
    "Utah - Employer Unemployment": "45-459",
    "Vermont - Employee Withholding": "46-450",
    "Vermont - Employer Unemployment": "46-459",
    "Virginia - Employee Withholding": "47-450",
    "Virginia - Employer Unemployment": "47-459",
    "Washington - Employer Labor and Industries": "48-471",
    "Washington - Employer Unemployment": "48-459",
    "Washington - Employment Administration Fund": "48-461",
    "West Virginia - Employee Withholding": "49-450",
    "West Virginia - Employer Unemployment": "49-459",
    "Wisconsin - Employee Withholding": "50-450",
    "Wisconsin - Employer Unemployment": "50-459",
    "Wyoming - Employer Unemployment": "51-459",
    "Wyoming - Employer Workers' Compensation Fee": "51-471",
    "Wyoming - Employment Support Fund": "51-461",
}

TAX_DESCRIPTIONS      = sorted(DESC_TO_CODE.keys())

_EXCLUDED_DESCRIPTIONS = {
    "Federal - Employee Medicare",
    "Federal - Employee Social Security  (OASDI)",
    "Federal - Employee Additional Medicare",
    "Federal - Employer Medicare",
    "Federal - Employer Social Security (OASDI)",
}

EMPLOYEE_DESCRIPTIONS = [d for d in TAX_DESCRIPTIONS if "employee" in d.lower() and d not in _EXCLUDED_DESCRIPTIONS]
EMPLOYER_DESCRIPTIONS = [d for d in TAX_DESCRIPTIONS if "employer" in d.lower() and d not in _EXCLUDED_DESCRIPTIONS]

# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Payroll Ops Adjustment Tool", layout="wide")
st.title("Payroll Ops Adjustment Tool")

# Hide +/- stepper buttons on all number inputs across the app
st.markdown("""
<style>
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
if "employee_taxes" not in st.session_state:
    st.session_state.employee_taxes = [{"name": "", "rate": 0.0, "limit": "No"}]
if "employer_taxes" not in st.session_state:
    st.session_state.employer_taxes = [{"name": "", "rate": 0.0, "limit": "No"}]
if "extra_employee_descs" not in st.session_state:
    st.session_state.extra_employee_descs = []
if "extra_employer_descs" not in st.session_state:
    st.session_state.extra_employer_descs = []


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
tab_calc, tab_fica, tab_ficad = st.tabs(["Calculator", "FICA Refund", "FICA Debit"])

# -----------------------------------------------------------------------
# TAB 1 — Calculator
# -----------------------------------------------------------------------
with tab_calc:
  # Initialize state early so SUI display works on first load
  if "state" not in st.session_state:
      st.session_state.state = ""
  left, right = st.columns([1, 1], gap="large")

# -----------------------------------------------------------------------
# LEFT — Inputs
# -----------------------------------------------------------------------
with left:
    # ---- Year & YTD ----
    st.subheader("Tax Year & YTD Wages")
    def _on_year_change():
        new_year  = st.session_state.calc_year
        cur_state = st.session_state.get("state", "")
        sui_wb    = SUI_WAGE_BASES.get(cur_state, {}).get(new_year)
        for i, tax in enumerate(st.session_state.get("employer_taxes", [])):
            if "unemployment" in tax.get("name", "").lower():
                if sui_wb:
                    tax["limit"]        = "Yes"
                    tax["limit_amount"] = float(sui_wb)
                    st.session_state[f"er_tlimit_{i}"]     = "Yes"
                    st.session_state[f"er_tlimit_amt_{i}"] = float(sui_wb)
                else:
                    tax["limit"]        = "No"
                    tax.pop("limit_amount", None)
                    st.session_state[f"er_tlimit_{i}"] = "No"
                    st.session_state.pop(f"er_tlimit_amt_{i}", None)

    year         = st.selectbox("Tax Year", [2026, 2025, 2024, 2023], key="calc_year", on_change=_on_year_change)
    ss_wage_base = SS_WAGE_BASES[year]
    st.caption(f"Social Security wage base for {year}: **${ss_wage_base:,}**")

    ytd_med = st.number_input("YTD Medicare Wages ($)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
    ytd_ss  = ytd_med

    st.divider()

    # ---- Mode ----
    st.subheader("Calculate")
    mode = st.radio("Mode", ["Net Pay (enter gross)", "Gross Up (enter desired net)"], horizontal=True)

    if "pay_amount" not in st.session_state:
        st.session_state.pay_amount = 0.0

    if mode.startswith("Net"):
        gross_input = st.number_input("Gross Pay ($)", min_value=0.0, value=st.session_state.pay_amount, step=50.0, format="%.2f")
        st.session_state.pay_amount = gross_input
        run_label   = "Calculate Net"
    else:
        desired_net = st.number_input("Desired Net Pay ($)", min_value=0.0, value=st.session_state.pay_amount, step=50.0, format="%.2f")
        st.session_state.pay_amount = desired_net
        run_label   = "Calculate Gross"

    calculate = st.button(run_label, type="primary", use_container_width=True)

    st.divider()

    _WRITEIN = "— Write in custom —"

    def _remove_tax(state_key, idx):
        prefix = "ee" if state_key == "employee_taxes" else "er"
        taxes  = st.session_state[state_key]
        taxes.pop(idx)
        # Wipe all widget keys for this list so stale cached values don't bleed
        # into the wrong row positions after the re-render
        for j in range(len(taxes) + 5):
            for sfx in ("tname", "trate", "tlimit", "tytd", "tlimit_amt", "custom_name", "custom_code"):
                st.session_state.pop(f"{prefix}_{sfx}_{j}", None)
        # Re-seed widget state from the now-correct data list
        for j, tax in enumerate(taxes):
            st.session_state[f"{prefix}_tname_{j}"]  = "— Write in custom —" if tax.get("custom_entry") else tax.get("name", "")
            st.session_state[f"{prefix}_trate_{j}"]  = float(tax.get("rate", 0.0))
            st.session_state[f"{prefix}_tlimit_{j}"] = tax.get("limit", "No")
            if tax.get("custom_entry"):
                st.session_state[f"{prefix}_custom_name_{j}"] = tax.get("custom_name", "")
                st.session_state[f"{prefix}_custom_code_{j}"] = tax.get("custom_code", "")
            if tax.get("limit") == "Yes":
                st.session_state[f"{prefix}_tytd_{j}"]       = float(tax.get("ytd_limit", 0.0))
                st.session_state[f"{prefix}_tlimit_amt_{j}"] = float(tax.get("limit_amount", 0.0))

    def _tax_rows(taxes, key_prefix, descriptions, allow_no_limit_flag=False, state_key=None):
        """Render a tax rate table section."""
        for i, tax in enumerate(taxes):
            _is_custom = tax.get("custom_entry", False)
            _dd_opts   = ["", _WRITEIN] + descriptions
            _dd_val    = _WRITEIN if _is_custom else tax.get("name", "")
            _dd_idx    = _dd_opts.index(_dd_val) if _dd_val in _dd_opts else 0
            _tname_key = f"{key_prefix}_tname_{i}"

            # When write-in is active, split c1 into dropdown + text input side by side
            _is_writein = st.session_state.get(_tname_key, _dd_val) == _WRITEIN
            if _is_writein:
                c1a, c1b, c2, c3, c4, c5 = st.columns([1.5, 1.5, 1.2, 1.2, 0.9, 0.4])
            else:
                c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 0.9, 0.4])
                c1a = c1

            with c1a:
                _tname_kwargs = {"index": _dd_idx} if _tname_key not in st.session_state else {}
                sel = st.selectbox(
                    "Tax Name",
                    options=_dd_opts,
                    key=_tname_key,
                    label_visibility="collapsed",
                    **_tname_kwargs,
                )

            if sel == _WRITEIN:
                taxes[i]["custom_entry"] = True
                with c1b:
                    custom_name = st.text_input(
                        "Custom name",
                        value=tax.get("custom_name", ""),
                        key=f"{key_prefix}_custom_name_{i}",
                        label_visibility="collapsed",
                        placeholder="Enter tax name...",
                    )
                taxes[i]["custom_name"] = custom_name
                taxes[i]["name"]        = custom_name
            else:
                taxes[i]["custom_entry"] = False
                taxes[i]["name"]         = sel
                taxes[i].pop("custom_name", None)

            with c2:
                if taxes[i].get("custom_entry", False):
                    # Clear stale code if user just switched to write-in from a real tax
                    if not _is_custom:
                        taxes[i]["custom_code"] = ""
                        st.session_state.pop(f"{key_prefix}_custom_code_{i}", None)
                    custom_code = st.text_input(
                        "Tax code",
                        value=taxes[i].get("custom_code", ""),
                        key=f"{key_prefix}_custom_code_{i}",
                        label_visibility="collapsed",
                        placeholder="Code",
                    )
                    taxes[i]["custom_code"] = custom_code
                    code = custom_code
                else:
                    code = DESC_TO_CODE.get(sel, "")
                    taxes[i]["custom_code"] = code
                    st.markdown(f'<div style="padding:8px 4px; font-size:1rem; font-weight:600; color:inherit;">{code or "—"}</div>', unsafe_allow_html=True)

            with c3:
                _trate_key = f"{key_prefix}_trate_{i}"
                _trate_kwargs = {"value": float(tax["rate"])} if _trate_key not in st.session_state else {}
                rate = st.number_input(
                    "Rate",
                    min_value=0.0, max_value=100.0,
                    step=0.1, format="%.2f",
                    key=_trate_key,
                    label_visibility="collapsed",
                    **_trate_kwargs,
                )
                taxes[i]["rate"] = rate

            with c4:
                _no_limit = allow_no_limit_flag and (sel == "Federal - Employee Withholding")
                if _no_limit:
                    st.session_state[f"{key_prefix}_tlimit_{i}"] = "No"
                limit = st.selectbox(
                    "Limit",
                    options=["No", "Yes"],
                    key=f"{key_prefix}_tlimit_{i}",
                    label_visibility="collapsed",
                    disabled=_no_limit,
                )
                taxes[i]["limit"] = limit

            with c5:
                st.button("✕", key=f"{key_prefix}_tremove_{i}",
                          on_click=_remove_tax, args=(state_key, i))

            if limit == "Yes":
                l1, l2 = st.columns([1, 1])
                with l1:
                    ytd_limit = st.number_input(
                        "YTD",
                        min_value=0.0,
                        value=float(tax.get("ytd_limit", 0.0)),
                        step=100.0, format="%.2f",
                        key=f"{key_prefix}_tytd_{i}",
                    )
                    taxes[i]["ytd_limit"] = ytd_limit
                with l2:
                    limit_amount = st.number_input(
                        "Limit",
                        min_value=0.0,
                        value=float(tax.get("limit_amount", 0.0)),
                        step=100.0, format="%.2f",
                        key=f"{key_prefix}_tlimit_amt_{i}",
                    )
                    taxes[i]["limit_amount"] = limit_amount

    def _build_rates(taxes):
        rates = []
        for t in taxes:
            if t.get("name"):
                code = t.get("custom_code", "") or DESC_TO_CODE.get(t["name"], "")
                if t.get("limit") == "Yes":
                    ytd  = t.get("ytd_limit", 0.0)
                    cap  = t.get("limit_amount", 0.0)
                    room = max(0.0, cap - ytd)
                    rates.append((t["name"], code, t["rate"], room, ytd))
                else:
                    rates.append((t["name"], code, t["rate"], None, None))
        return rates

    # ---- Build effective description lists (base + user-promoted) ----
    _eff_ee_descs = EMPLOYEE_DESCRIPTIONS + [d for d in st.session_state.extra_employee_descs if d not in EMPLOYEE_DESCRIPTIONS]
    _eff_er_descs = EMPLOYER_DESCRIPTIONS + [d for d in st.session_state.extra_employer_descs if d not in EMPLOYER_DESCRIPTIONS]

    # ---- Employee taxes ----
    st.subheader("Additional Tax Rates")
    st.caption("Employee withholdings")

    eh1, eh2, eh3, eh4, eh5 = st.columns([3, 1.2, 1.2, 0.9, 0.4])
    eh1.markdown("**Employee Tax Name**")
    eh2.markdown("**Tax Code**")
    eh3.markdown("**Rate (%)**")
    eh4.markdown("**Limit**")

    _tax_rows(st.session_state.employee_taxes, "ee", _eff_ee_descs, allow_no_limit_flag=True, state_key="employee_taxes")

    if st.button("+ Add Employee Tax", use_container_width=True, key="ee_add_tax"):
        st.session_state.employee_taxes.append({"name": "", "rate": 0.0, "limit": "No"})
        st.rerun()

    custom_rates = _build_rates(st.session_state.employee_taxes)

    st.divider()

    # ---- Employer taxes ----
    st.caption("Employer contributions")

    rh1, rh2, rh3, rh4, rh5 = st.columns([3, 1.2, 1.2, 0.9, 0.4])
    rh1.markdown("**Employer Tax Name**")
    rh2.markdown("**Tax Code**")
    rh3.markdown("**Rate (%)**")
    rh4.markdown("**Limit**")

    _tax_rows(st.session_state.employer_taxes, "er", _eff_er_descs, state_key="employer_taxes")

    if st.button("+ Add Employer Tax", use_container_width=True, key="er_add_tax"):
        st.session_state.employer_taxes.append({"name": "", "rate": 0.0, "limit": "No"})
        st.rerun()

    employer_rates = _build_rates(st.session_state.employer_taxes)


# -----------------------------------------------------------------------
# RIGHT — Results
# -----------------------------------------------------------------------
with right:
    st.subheader("ADJ Info")

    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        if "mid" not in st.session_state:
            st.session_state.mid = ""
        st.session_state.mid = st.text_input("MID", value=st.session_state.mid)
    with f2:
        if "cid" not in st.session_state:
            st.session_state.cid = ""
        st.session_state.cid = st.text_input("CID", value=st.session_state.cid)
    with f3:
        if "adj_date" not in st.session_state:
            from datetime import date
            _today = date.today()
            _days_until_friday = (4 - _today.weekday()) % 7
            if _days_until_friday == 0:
                _days_until_friday = 7
            from datetime import timedelta
            st.session_state.adj_date = _today + timedelta(days=_days_until_friday)
        st.session_state.adj_date = st.date_input("Adjustment Date", value=st.session_state.adj_date, format="MM/DD/YYYY")

    TICKET_TYPES = ["", "MDV", "MISC Fully Taxable"]
    if "ticket_type" not in st.session_state:
        st.session_state.ticket_type = ""

    STATES = [
        "", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming",
    ]
    if "state" not in st.session_state:
        st.session_state.state = ""

    _TICKET_NOTES = {
        "MDV":                "MDV refund - ",
        "MISC Fully Taxable": "Recording Wages - ",
    }

    def _on_ticket_type_change():
        preset = _TICKET_NOTES.get(st.session_state["_tt_select"], "")
        if preset:
            st.session_state.notes = preset

    tt_col, state_col = st.columns(2)
    with tt_col:
        sel_tt = st.selectbox(
            "Ticket Type",
            options=TICKET_TYPES,
            index=TICKET_TYPES.index(st.session_state.ticket_type),
            key="_tt_select",
            on_change=_on_ticket_type_change,
        )
        st.session_state.ticket_type = sel_tt
    with state_col:
        def _on_state_change():
            new_state = st.session_state.state
            if new_state == st.session_state.get("_last_applied_state"):
                return
            st.session_state._last_applied_state = new_state
            _cb_ee = EMPLOYEE_DESCRIPTIONS + [d for d in st.session_state.get("extra_employee_descs", []) if d not in EMPLOYEE_DESCRIPTIONS]
            _cb_er = EMPLOYER_DESCRIPTIONS + [d for d in st.session_state.get("extra_employer_descs", []) if d not in EMPLOYER_DESCRIPTIONS]
            new_ee = [{"name": d, "rate": 0.0, "limit": "No"} for d in _cb_ee if d.startswith(new_state + " - ")]
            # For employer unemployment taxes, apply saved SUI wage base as the limit
            _sui_year = st.session_state.get("calc_year", 2026)
            _sui_wb   = SUI_WAGE_BASES.get(new_state, {}).get(_sui_year)
            new_er_raw = [{"name": d, "rate": 0.0, "limit": "No"} for d in _cb_er if d.startswith(new_state + " - ")]
            new_er = []
            for t in new_er_raw:
                if "unemployment" in t["name"].lower() and _sui_wb:
                    t["limit"]        = "Yes"
                    t["limit_amount"] = float(_sui_wb)
                    t["ytd_limit"]    = 0.0
                new_er.append(t)
            if not new_ee:
                new_ee = [{"name": "", "rate": 0.0, "limit": "No"}]
            if not new_er:
                new_er = [{"name": "", "rate": 0.0, "limit": "No"}]
            # Clear stale widget keys beyond new list lengths
            for i in range(max(len(st.session_state.employee_taxes), len(new_ee)) + 5):
                for suffix in ("tname", "trate", "tlimit", "tytd", "tlimit_amt"):
                    st.session_state.pop(f"ee_{suffix}_{i}", None)
            for i in range(max(len(st.session_state.employer_taxes), len(new_er)) + 5):
                for suffix in ("tname", "trate", "tlimit", "tytd", "tlimit_amt"):
                    st.session_state.pop(f"er_{suffix}_{i}", None)
            for i, tax in enumerate(new_ee):
                st.session_state[f"ee_tname_{i}"] = tax["name"]
                st.session_state[f"ee_trate_{i}"] = tax["rate"]
                st.session_state[f"ee_tlimit_{i}"] = tax["limit"]
            for i, tax in enumerate(new_er):
                st.session_state[f"er_tname_{i}"] = tax["name"]
                st.session_state[f"er_trate_{i}"] = tax["rate"]
                st.session_state[f"er_tlimit_{i}"] = tax["limit"]
                if tax.get("limit") == "Yes":
                    st.session_state[f"er_tlimit_amt_{i}"] = float(tax.get("limit_amount", 0.0))
                    st.session_state[f"er_tytd_{i}"]       = float(tax.get("ytd_limit", 0.0))
            st.session_state.employee_taxes = new_ee
            st.session_state.employer_taxes = new_er

        st.selectbox("State", options=STATES, key="state", on_change=_on_state_change)
        _sui_display_wb = get_sui_wage_base(st.session_state.state, year)
        if _sui_display_wb:
            st.markdown(
                f'<p style="font-size:0.85rem; color: gray; margin-top:-8px;">SUI wage base ({st.session_state.state}, {year}): '
                f'<strong>${_sui_display_wb:,}</strong></p>',
                unsafe_allow_html=True,
            )

    st.subheader("Notes")
    if "notes" not in st.session_state:
        st.session_state.notes = ""
    st.session_state.notes = st.text_area(
        "Notes",
        value=st.session_state.notes,
        height=150,
        label_visibility="collapsed",
        placeholder="Add any notes here...",
    )

    st.divider()
    st.subheader("Results")

    if calculate:
        if mode.startswith("Net"):
            gross  = gross_input
            result = calc_taxes(gross, ytd_ss, ytd_med, ss_wage_base, custom_rates)
            st.metric("Net Pay", fmt(result["net"]))
        else:
            gross, result = gross_up(desired_net, ytd_ss, ytd_med, ss_wage_base, custom_rates)
            st.metric("Required Gross Pay", fmt(gross))

        st.session_state.last_gross          = gross
        st.session_state.last_result         = result
        st.session_state.last_ytd_med        = ytd_med
        st.session_state.last_employer_rates = employer_rates

        render_breakdown(gross, result, ss_wage_base, ytd_ss)
        st.divider()
        render_tax_table(gross, ytd_med, ss_wage_base, result, employer_rates)

        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tax",      fmt(result["total_tax"]))
        eff = (result["total_tax"] / gross * 100) if gross else 0
        c2.metric("Effective Rate", f"{eff:.2f}%")
        c3.metric("Net Pay",        fmt(result["net"]))

    elif "last_gross" in st.session_state:
        _ytd = st.session_state.get("last_ytd_med", ytd_med)
        render_breakdown(
            st.session_state.last_gross,
            st.session_state.last_result,
            ss_wage_base,
            ytd_ss,
        )
        st.divider()
        render_tax_table(st.session_state.last_gross, _ytd, ss_wage_base, st.session_state.last_result, st.session_state.get("last_employer_rates", []))
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Tax",      fmt(st.session_state.last_result["total_tax"]))
        eff = (st.session_state.last_result["total_tax"] / st.session_state.last_gross * 100) if st.session_state.last_gross else 0
        c2.metric("Effective Rate", f"{eff:.2f}%")
        c3.metric("Net Pay",        fmt(st.session_state.last_result["net"]))
    else:
        st.info("Configure inputs on the left and hit Calculate.")

    # ---- CSV Export ----
    if "last_gross" in st.session_state:
        st.divider()
        st.subheader("CSV Export")

        _calc_gross   = st.session_state.last_gross
        _calc_result  = st.session_state.last_result
        _calc_er      = st.session_state.get("last_employer_rates", [])
        _calc_date    = st.session_state.adj_date.strftime("%m/%d/%Y")
        _calc_mid     = st.session_state.mid.lstrip("M").lstrip("m")
        _calc_cid     = st.session_state.cid.lstrip("C").lstrip("c")
        _calc_notes   = " ".join(st.session_state.notes.splitlines()).strip()

        _calc_cols = [
            "account_type", "entry_type", "adjustment_date", "amount",
            "cid", "tax_code", "member_id", "taxable_amount", "subj_gross",
            "adjusted_gross", "adjusted_supl_gross", "gross_earnings_amount",
            "reference_type", "reference_id", "notes",
        ]

        def _fmt(v):
            return round(v, 2) if isinstance(v, (int, float)) else v

        def _calc_row(account_type, entry_type, amount, tax_code, member_id, taxable_amount, subj_gross, adj_gross, adj_supl, gross_earnings, ref_type, ref_id, notes):
            return {
                "account_type": account_type, "entry_type": entry_type,
                "adjustment_date": _calc_date, "amount": _fmt(amount),
                "cid": _calc_cid, "tax_code": tax_code, "member_id": member_id,
                "taxable_amount": _fmt(taxable_amount), "subj_gross": _fmt(subj_gross),
                "adjusted_gross": _fmt(adj_gross), "adjusted_supl_gross": _fmt(adj_supl),
                "gross_earnings_amount": _fmt(gross_earnings),
                "reference_type": ref_type, "reference_id": ref_id, "notes": notes,
            }

        _calc_rows = []

        def _cr(tax_code, amount, taxable, gross_earnings=0.0):
            # subj_gross   = Adj Gross column (always the full gross pay)
            # adjusted_gross = taxable_amount (Taxable on Adj column)
            # gross_earnings_amount = 0 normally; only populated for FUTA when fully over wage base
            return _calc_row("Clearing", "Credit", amount, tax_code, _calc_mid,
                             taxable, _calc_gross, taxable, 0.0, gross_earnings, "x", 1, _calc_notes)

        # Rows mirror Tax Detail exactly — same order, same conditions

        # Federal - Employee Withholding (00-400) — always shown in tax detail
        _fed_item = next((item for item in _calc_result.get("custom_items", []) if item[0] == "Federal - Employee Withholding"), None)
        _fed_amt  = (_fed_item[4] if len(_fed_item) >= 6 else _fed_item[3]) if _fed_item else 0.0
        _calc_rows.append(_cr("00-400", _fed_amt, _calc_gross))

        # Social Security - Employee (00-403) — always shown
        _calc_rows.append(_cr("00-403", _calc_result.get("ss_amount", 0), _calc_result.get("ss_taxable", 0)))

        # Social Security - Employer (00-404) — always shown
        _calc_rows.append(_cr("00-404", _calc_result.get("ss_amount", 0), _calc_result.get("ss_taxable", 0)))

        # Medicare - Employee (00-406) — always shown
        _calc_rows.append(_cr("00-406", _calc_result.get("med_amount", 0), _calc_gross))

        # Additional Medicare - Employee (00-901) — only when shown in tax detail
        if _calc_result.get("add_med_taxable", 0) > 0:
            _calc_rows.append(_cr("00-901", _calc_result["add_med_amount"], _calc_result["add_med_taxable"]))

        # Medicare - Employer (00-407) — always shown
        _calc_rows.append(_cr("00-407", _calc_result.get("med_amount", 0), _calc_gross))

        # FUTA (00-402) — always in CSV
        # When fully over wage base (taxable = 0): gross_earnings_amount = adj gross
        # When within wage base (taxable > 0): normal row
        _futa_taxable = _calc_result.get("futa_taxable", 0)
        _futa_amount  = _calc_result.get("futa_amount", 0)
        if _futa_taxable == 0:
            _calc_rows.append(_cr("00-402", _futa_amount, 0, gross_earnings=_calc_gross))
        else:
            _calc_rows.append(_cr("00-402", _futa_amount, _futa_taxable))

        # Employee custom taxes (one row per item in tax detail, excluding 00-400)
        for item in _calc_result.get("custom_items", []):
            if item[0] == "Federal - Employee Withholding":
                continue
            code    = item[1] if len(item) >= 6 else DESC_TO_CODE.get(item[0], "")
            taxable = item[3] if len(item) >= 6 else item[2]
            amt     = item[4] if len(item) >= 6 else (item[3] if len(item) >= 4 else item[2])
            _calc_rows.append(_cr(code, amt, taxable))

        # Employer custom taxes (one row per item in tax detail)
        for name, code, rate, limit_room, ytd_display in _calc_er:
            taxable = min(_calc_gross, limit_room) if limit_room is not None else _calc_gross
            amt     = round(taxable * rate / 100, 2)
            _calc_rows.append(_cr(code, amt, taxable))

        # Company / Debit — sum of all Clearing / Credit amounts
        _clearing_total = round(sum(r["amount"] for r in _calc_rows), 2)
        _calc_rows.append(_calc_row("Company", "Debit", _clearing_total, "", "", "", "", "", "", "", "", "", ""))

        import pandas as _pd_calc
        import io as _io_calc
        import csv as _csv_calc

        _calc_df = _pd_calc.DataFrame(_calc_rows, columns=_calc_cols)
        st.dataframe(_calc_df, use_container_width=True, hide_index=True)

        _calc_buf = _io_calc.StringIO()
        _calc_writer = _csv_calc.DictWriter(_calc_buf, fieldnames=_calc_cols)
        _calc_writer.writeheader()
        _calc_writer.writerows(_calc_rows)

        _calc_missing = []
        if not st.session_state.mid.strip():
            _calc_missing.append("MID")
        if not st.session_state.cid.strip():
            _calc_missing.append("CID")

        if _calc_missing:
            st.error(f"Please enter a {' and '.join(_calc_missing)} before downloading.")
        else:
            st.download_button(
                label="Download CSV",
                data=_calc_buf.getvalue(),
                file_name=f"{st.session_state.mid} {st.session_state.cid} {st.session_state.ticket_type or 'Calc'}.csv",
                mime="text/csv",
                use_container_width=True,
                key="calc_download_csv",
            )

        if st.session_state.get("ticket_type") == "MDV":
            st.divider()
            st.subheader("CS Tools Adjustment Summary")

            st.caption("Paste the CS Tools link to make the header clickable")
            st.text_input("CS Tools Link", placeholder="Paste link here...", key="calc_cs_link", label_visibility="visible")
            st.text_input("Debit Date", placeholder="e.g. 01/15/2025", key="calc_debit_date", label_visibility="visible")

            st.divider()

            _calc_debit_date = st.session_state.get("calc_debit_date", "").strip() or "XXXXX"
            _calc_cs_url     = st.session_state.get("calc_cs_link", "").strip()
            _calc_here_link  = (
                f'<a href="{_calc_cs_url}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">here</a>'
                if _calc_cs_url else 'here'
            )
            _calc_summary_html = (
                f'<div style="font-size:0.9rem; line-height:1.8;">'
                f'<p style="margin:0 0 8px 0; line-height:1.4;">'
                f'The adjustment has been completed and can be viewed {_calc_here_link}. '
                f'The employer will be debited ${_clearing_total:,.2f} on {_calc_debit_date} '
                f'and the admin needs to pay the employee ${_calc_result.get("net", 0):,.2f} as a non taxable payment.'
                f'</p>'
                f'</div>'
            )
            st.markdown(_calc_summary_html, unsafe_allow_html=True)

            def _brow(label, amount, bold=False):
                amt_str = f"<b>{amount}</b>" if bold else amount
                lbl_str = f"<b>{label}</b>"  if bold else label
                return (f'<tr style="border-bottom:1px solid #f0f0f0;">'
                        f'<td style="padding:7px 4px;">{lbl_str}</td>'
                        f'<td style="text-align:right; padding:7px 8px; font-variant-numeric:tabular-nums; white-space:nowrap;">{amt_str}</td>'
                        f'</tr>')

            _bdown_html = (
                '<table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:1rem;">'
                '<thead><tr style="border-bottom:2px solid #ccc;">'
                '<th style="text-align:left; padding:6px 4px; font-weight:600;">Item</th>'
                '<th style="text-align:right; padding:6px 8px; font-weight:600;">Amount</th>'
                '</tr></thead><tbody>'
            )
            _bdown_html += _brow("Gross Pay", fmt(_calc_gross))
            _bdown_html += _brow("&minus; Social Security", fmt(-_calc_result.get("ss_amount", 0)))
            _bdown_html += _brow("&minus; Medicare",        fmt(-_calc_result.get("med_amount", 0)))
            _bdown_html += _brow("= Net Pay",               fmt(_calc_result.get("net", 0)), bold=True)
            _bdown_html += "</tbody></table>"
            st.markdown(_bdown_html, unsafe_allow_html=True)

            st.markdown(
                '<p style="font-size:0.9rem; margin-top:12px;">'
                'The SOP for refunding benefit deductions can be found '
                '<a href="https://justworks.atlassian.net/wiki/spaces/CX/pages/474644752/Refunding+Benefits+Deductions" '
                'target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">here</a>'
                ' for your reference.</p>'
                '<p style="font-size:0.9rem; margin-top:4px;">'
                'Visit our team\'s page '
                '<a href="https://justworks.atlassian.net/wiki/spaces/PAY/pages/1951466586/Payroll+Operations+Team+-+PTU" '
                'target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">here</a>'
                '.</p>',
                unsafe_allow_html=True,
            )

        elif st.session_state.get("ticket_type") == "MISC Fully Taxable":
            st.divider()
            st.subheader("CS Tools Adjustment Summary")

            st.caption("Paste the CS Tools link to make the header clickable")
            st.text_input("CS Tools Link", placeholder="Paste link here...", key="calc_cs_link", label_visibility="visible")
            st.text_input("Debit Date", placeholder="e.g. 01/15/2025", key="calc_debit_date", label_visibility="visible")

            st.divider()

            _misc_debit_date = st.session_state.get("calc_debit_date", "").strip() or "XXXXX"
            _misc_cs_url     = st.session_state.get("calc_cs_link", "").strip()
            _misc_adj_header = (
                f'<a href="{_misc_cs_url}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">ADJ in CS Tools</a>'
                if _misc_cs_url else '<strong>ADJ in CS Tools</strong>'
            )
            _misc_summary_html = (
                f'<div style="font-size:0.9rem; line-height:1.8;">'
                f'<p style="margin:0 0 8px 0; line-height:1.4;">The adjustment has been completed and can be viewed below:</p>'
                f'<p style="margin:0 0 8px 0; line-height:1.4;">'
                f'{_misc_adj_header}<br>'
                f'Employer Debit: ${_clearing_total:,.2f} on {_misc_debit_date}'
                f'</p>'
                f'</div>'
            )
            st.markdown(_misc_summary_html, unsafe_allow_html=True)

            st.markdown(
                '<p style="font-size:0.9rem; margin-top:12px;">'
                'Visit our team\'s page '
                '<a href="https://justworks.atlassian.net/wiki/spaces/PAY/pages/1951466586/Payroll+Operations+Team+-+PTU" '
                'target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">here</a>'
                '.</p>',
                unsafe_allow_html=True,
            )

# -----------------------------------------------------------------------
# TAB 2 — FICA Refund
# -----------------------------------------------------------------------
with tab_fica:
    import io as _io
    import csv as _csv
    from datetime import date as _date, timedelta as _timedelta

    _QUARTER_ENDS = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}

    def _quarter_end_date(year, qnum):
        month, day = _QUARTER_ENDS[qnum]
        d = _date(year, month, day)
        if d.weekday() == 5:
            d -= _timedelta(days=1)
        elif d.weekday() == 6:
            d -= _timedelta(days=2)
        return d

    # Year selector
    if "fica_selected_year" not in st.session_state:
        st.session_state.fica_selected_year = 2026
    if "fica_year_version" not in st.session_state:
        st.session_state.fica_year_version = 0

    _years = [2026, 2025, 2024, 2023]

    def _on_year_change():
        new_year = st.session_state.fica_year_select
        st.session_state.fica_selected_year = new_year
        st.session_state.fica_year_version += 1
        new_v = st.session_state.fica_year_version
        if "fica_quarters" in st.session_state:
            for q in st.session_state.fica_quarters:
                new_date = _quarter_end_date(new_year, q["qnum"])
                q["adj_date"] = new_date
                st.session_state[f"fica_adj_date_{q['qnum']}_v{new_v}"] = new_date

    # Global fields
    if "fica_member_id" not in st.session_state:
        st.session_state.fica_member_id = ""
    if "fica_company_id" not in st.session_state:
        st.session_state.fica_company_id = ""
    if "fica_notes" not in st.session_state:
        st.session_state.fica_notes = ""

    _mid_col, _cid_col, _yr_col = st.columns([1, 1, 1])
    with _mid_col:
        st.session_state.fica_member_id = st.text_input("Member ID", value=st.session_state.fica_member_id, max_chars=20, key="fica_member_id_input")
    with _cid_col:
        st.session_state.fica_company_id = st.text_input("Company ID", value=st.session_state.fica_company_id, max_chars=20, key="fica_company_id_input")
    with _yr_col:
        st.selectbox("Tax Year", _years, index=_years.index(st.session_state.fica_selected_year),
                     key="fica_year_select", on_change=_on_year_change)

    st.divider()

    # Initialize quarters list
    if "fica_quarters" not in st.session_state:
        _yr = st.session_state.fica_selected_year
        st.session_state.fica_quarters = [
            {"qnum": n, "ss_wages": 0.0, "ss_tax": 0.0, "med_wages": 0.0, "med_tax": 0.0, "futa_wages": 0.0, "futa_tax": 0.0, "adj_date": _quarter_end_date(_yr, n)}
            for n in [1, 2, 3, 4]
        ]

    def remove_quarter(idx):
        st.session_state.fica_quarters.pop(idx)

    for i, q in enumerate(st.session_state.fica_quarters):
        qn = q["qnum"]
        with st.expander(f"Q{qn} — {q['adj_date'].strftime('%m/%d/%Y')}", expanded=(i == 0)):
            ss_col, med_col, futa_col = st.columns(3)
            with ss_col:
                st.caption("**Social Security**")
                q["ss_wages"] = st.number_input("SS Wages ($)", min_value=0.0, value=q["ss_wages"], step=0.01, format="%.2f", key=f"fica_ss_wages_{qn}")
                q["ss_tax"]   = st.number_input("SS Tax ($)",   min_value=0.0, value=q["ss_tax"],   step=0.01, format="%.2f", key=f"fica_ss_tax_{qn}")
            with med_col:
                st.caption("**Medicare**")
                q["med_wages"] = st.number_input("Medicare Wages ($)", min_value=0.0, value=q["med_wages"], step=0.01, format="%.2f", key=f"fica_med_wages_{qn}")
                q["med_tax"]   = st.number_input("Medicare Tax ($)",   min_value=0.0, value=q["med_tax"],   step=0.01, format="%.2f", key=f"fica_med_tax_{qn}")
            with futa_col:
                st.caption("**FUTA**")
                q["futa_wages"] = st.number_input("FUTA Wages ($)", min_value=0.0, value=q["futa_wages"], step=0.01, format="%.2f", key=f"fica_futa_wages_{qn}")
                q["futa_tax"]   = st.number_input("FUTA Tax ($)",   min_value=0.0, value=q["futa_tax"],   step=0.01, format="%.2f", key=f"fica_futa_tax_{qn}")

            _dk = f"fica_adj_date_{qn}_v{st.session_state.fica_year_version}"
            _di_kwargs = {} if _dk in st.session_state else {"value": q["adj_date"]}
            q["adj_date"] = st.date_input("Adjustment Date", format="MM/DD/YYYY", key=_dk, **_di_kwargs)

            if len(st.session_state.fica_quarters) > 1:
                st.button(f"Remove Q{qn}", key=f"fica_remove_{qn}", on_click=remove_quarter, args=(i,))

    # Tax rate validation
    _fica_alerts = []
    for q in st.session_state.fica_quarters:
        qn = q["qnum"]
        ss_expected   = round(q["ss_wages"]   * 0.062,  2)
        med_expected  = round(q["med_wages"]  * 0.0145, 2)
        futa_expected = round(q["futa_wages"] * 0.006,  2)
        if abs(q["ss_tax"] - ss_expected) > 0.10:
            _fica_alerts.append(f"Q{qn}: SS Tax is ${q['ss_tax']:.2f} but expected ${ss_expected:.2f} (6.2% of ${q['ss_wages']:,.2f})")
        if abs(q["med_tax"] - med_expected) > 0.10:
            _fica_alerts.append(f"Q{qn}: Medicare Tax is ${q['med_tax']:.2f} but expected ${med_expected:.2f} (1.45% of ${q['med_wages']:,.2f})")
        if q["futa_wages"] > 0 or q["futa_tax"] > 0:
            if abs(q["futa_tax"] - futa_expected) > 0.10:
                _fica_alerts.append(f"Q{qn}: FUTA Tax is ${q['futa_tax']:.2f} but expected ${futa_expected:.2f} (0.6% of ${q['futa_wages']:,.2f})")
    if _fica_alerts:
        _alerts_html = "".join(
            f'<p style="margin:4px 0; font-size:0.9rem; color:#b45309;">&#9888; {a}</p>'
            for a in _fica_alerts
        )
        st.markdown(
            f'<div style="background:#fffbeb; border-left:3px solid #b45309; padding:10px 14px; border-radius:4px; margin-bottom:8px;">'
            f'<p style="margin:0 0 6px 0; font-size:0.85rem; font-weight:600; color:#b45309;">Review the following values before downloading:</p>'
            f'{_alerts_html}</div>',
            unsafe_allow_html=True,
        )

    if st.button("+ Add Quarter", use_container_width=True, key="fica_add_quarter"):
        _existing = {q["qnum"] for q in st.session_state.fica_quarters}
        _next = next((n for n in [1, 2, 3, 4] if n not in _existing), None)
        if _next is not None:
            st.session_state.fica_quarters.append({
                "qnum": _next,
                "ss_wages": 0.0, "ss_tax": 0.0,
                "med_wages": 0.0, "med_tax": 0.0,
                "futa_wages": 0.0, "futa_tax": 0.0,
                "adj_date": _quarter_end_date(st.session_state.fica_selected_year, _next),
            })
            st.session_state.fica_quarters.sort(key=lambda q: q["qnum"])
            st.rerun()

    st.divider()
    st.subheader("Notes")
    st.session_state.fica_notes = st.text_area("Notes", value=st.session_state.fica_notes, height=80, label_visibility="collapsed", placeholder="Add any notes here...", key="fica_notes_input")

    st.divider()

    # Build all rows across all quarters
    _cols = [
        "account_type", "entry_type", "adjustment_date", "amount",
        "cid", "tax_code", "member_id", "taxable_amount", "subj_gross",
        "adjusted_gross", "adjusted_supl_gross", "gross_earnings_amount",
        "reference_type", "reference_id", "notes",
    ]

    def build_quarter_rows(q, cid, mid, notes):
        adj_date_str = q["adj_date"].strftime("%m/%d/%Y")
        ss_wages   = q["ss_wages"]
        ss_tax     = q["ss_tax"]
        med_wages  = q["med_wages"]
        med_tax    = q["med_tax"]
        futa_wages = q["futa_wages"]
        futa_tax   = q["futa_tax"]

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

    _cid   = st.session_state.fica_company_id.lstrip("C").lstrip("c")
    _mid   = st.session_state.fica_member_id.lstrip("M").lstrip("m")
    _notes = " ".join(st.session_state.fica_notes.splitlines()).strip()

    _all_rows = []
    for q in st.session_state.fica_quarters:
        _all_rows.extend(build_quarter_rows(q, _cid, _mid, _notes))

    st.subheader("Preview")
    st.dataframe(pd.DataFrame(_all_rows, columns=_cols), use_container_width=True)

    buf = _io.StringIO()
    _writer = _csv.DictWriter(buf, fieldnames=_cols)
    _writer.writeheader()
    _writer.writerows(_all_rows)
    _csv_data = buf.getvalue()

    _missing = []
    if not st.session_state.fica_member_id.strip():
        _missing.append("Member ID")
    if not st.session_state.fica_company_id.strip():
        _missing.append("Company ID")

    if _missing:
        st.error(f"Please enter a {' and '.join(_missing)} before downloading.")
    else:
        _downloaded = st.download_button(
            label="Download CSV",
            data=_csv_data,
            file_name=f"{st.session_state.fica_member_id} {st.session_state.fica_company_id} FICA FUTA Refund.csv",
            mime="text/csv",
            use_container_width=True,
            key="fica_download_csv",
        )
        if _downloaded:
            st.session_state.fica_refund_csv_downloaded = True

    _fica_active_quarters = [
        q for q in st.session_state.fica_quarters
        if round(q["ss_tax"] + q["med_tax"], 2) > 0 or round(q["ss_tax"] + q["med_tax"] + q["futa_tax"], 2) > 0
    ]

    if _fica_active_quarters:
        st.divider()
        st.subheader("CS Tools Adjustment Summary")

        st.caption("Paste a CS Tools link for each quarter to make the header clickable")
        for q in _fica_active_quarters:
            st.text_input(f"Q{q['qnum']} CS Tools Link", placeholder="Paste link here...", key=f"fica_q{q['qnum']}_link", label_visibility="visible")
        st.text_input("Credit Date", placeholder="e.g. 01/15/2025", key="fica_credit_date", label_visibility="visible")

        st.divider()

        _fica_credit_date = st.session_state.get("fica_credit_date", "").strip() or "XXXXX"
        _fica_summary_html = '<div style="font-size:0.9rem; line-height:1.8;">'
        if len(_fica_active_quarters) == 1:
            _fica_summary_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustment has been completed and can be viewed below:</p>'
        elif len(_fica_active_quarters) >= 2:
            _fica_summary_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustments have been completed and can be viewed below:</p>'
        for q in _fica_active_quarters:
            qn          = q["qnum"]
            member_amt  = round(q["ss_tax"] + q["med_tax"], 2)
            company_amt = round(q["ss_tax"] + q["med_tax"] + q["futa_tax"], 2)
            url         = st.session_state.get(f"fica_q{qn}_link", "").strip()
            date_val    = _fica_credit_date
            header      = (f'<a href="{url}" target="_blank" style="color:#2563eb; font-weight:600; text-decoration:none;">Q{qn} ADJ in CS Tools</a>'
                           if url else f'<strong>Q{qn} ADJ in CS Tools</strong>')
            _fica_summary_html += (
                f'<p style="margin:0 0 8px 0; line-height:1.4;">'
                f'{header}<br>'
                f'Employee Credit: ${member_amt:,.2f} on {date_val}<br>'
                f'Employer Credit: ${company_amt:,.2f} on {date_val}'
                f'</p>'
            )
        if st.session_state.fica_selected_year < _date.today().year:
            _fica_summary_html += '<p style="margin:0; line-height:1.4;">The W-2c has been generated and can be viewed in the member documents center.</p>'
        _fica_summary_html += '</div>'

        st.markdown(_fica_summary_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------
# TAB 3 — FICA Debit
# -----------------------------------------------------------------------
with tab_ficad:
    # Year selector
    if "ficad_selected_year" not in st.session_state:
        st.session_state.ficad_selected_year = 2026
    if "ficad_year_version" not in st.session_state:
        st.session_state.ficad_year_version = 0

    def _on_ficad_year_change():
        new_year = st.session_state.ficad_year_select
        st.session_state.ficad_selected_year = new_year
        st.session_state.ficad_year_version += 1
        new_v = st.session_state.ficad_year_version
        if "ficad_quarters" in st.session_state:
            for q in st.session_state.ficad_quarters:
                new_date = _quarter_end_date(new_year, q["qnum"])
                q["adj_date"] = new_date
                st.session_state[f"ficad_adj_date_{q['qnum']}_v{new_v}"] = new_date

    # Global fields
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
        st.selectbox("Tax Year", _years, index=_years.index(st.session_state.ficad_selected_year),
                     key="ficad_year_select", on_change=_on_ficad_year_change)
    with _dm_col:
        st.session_state.ficad_debit_member = st.selectbox("Debit Member", ["Yes", "No"], index=["Yes", "No"].index(st.session_state.ficad_debit_member), key="ficad_debit_member_select")
    with _fo_col:
        st.session_state.ficad_fica_only = st.selectbox("FICA only", ["No", "Yes"],
            index=["No", "Yes"].index(st.session_state.ficad_fica_only),
            key="ficad_fica_only_select")

    st.divider()

    # Initialize quarters list
    if "ficad_quarters" not in st.session_state:
        _yr = st.session_state.ficad_selected_year
        st.session_state.ficad_quarters = [
            {"qnum": n, "gross_wages": 0.0, "ss_wages": 0.0, "ss_tax": 0.0, "med_wages": 0.0, "med_tax": 0.0, "futa_wages": 0.0, "futa_tax": 0.0, "adj_date": _quarter_end_date(_yr, n)}
            for n in [1, 2, 3, 4]
        ]

    def remove_ficad_quarter(idx):
        st.session_state.ficad_quarters.pop(idx)

    _FICAD_WAGE_BASES = {
        yr: {"ss": SS_WAGE_BASES[yr], "futa": 7_000}
        for yr in SS_WAGE_BASES
    }
    # Read directly from the selectbox key — it is always the authoritative current value
    # since the selectbox renders above this line. Fall back to ficad_selected_year on
    # first render before the key exists.
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
            _prev_over         = max(0.0, _ytd_gross         - ADD_MEDICARE_THRESH)
            _curr_over         = max(0.0, _ytd_gross_after   - ADD_MEDICARE_THRESH)
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

            _ytd_gross          += q["gross_wages"]
            _ytd_ss_wages       += q["ss_wages"]
            _ytd_ss_tax         += q["ss_tax"]
            _ytd_med_wages      += q["med_wages"]
            _ytd_med_tax        += q["med_tax"]
            _ytd_add_med_wages  += q["add_med_wages"]
            _ytd_add_med_tax    += q["add_med_tax"]
            _ytd_futa_wages     += q["futa_wages"]
            _ytd_futa_tax       += q["futa_tax"]

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
                "ss_wages": 0.0, "ss_tax": 0.0,
                "med_wages": 0.0, "med_tax": 0.0,
                "futa_wages": 0.0, "futa_tax": 0.0,
                "adj_date": _quarter_end_date(st.session_state.ficad_selected_year, _next),
            })
            st.session_state.ficad_quarters.sort(key=lambda q: q["qnum"])
            st.rerun()

    st.divider()
    st.subheader("Notes")
    st.session_state.ficad_notes = st.text_area("Notes", value=st.session_state.ficad_notes, height=80, label_visibility="collapsed", placeholder="Add any notes here...", key="ficad_notes_input")

    st.divider()

    # Build all rows across all quarters
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
            # No member debit — fold member amount into company row
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
    st.dataframe(pd.DataFrame(_ficad_rows, columns=_cols), use_container_width=True)

    _ficad_buf = _io.StringIO()
    _ficad_writer = _csv.DictWriter(_ficad_buf, fieldnames=_cols)
    _ficad_writer.writeheader()
    _ficad_writer.writerows(_ficad_rows)
    _ficad_csv = _ficad_buf.getvalue()

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
            data=_ficad_csv,
            file_name=f"{st.session_state.ficad_member_id} {st.session_state.ficad_company_id} FICA Debit.csv",
            mime="text/csv",
            use_container_width=True,
            key="ficad_download_csv",
        )

    _ficad_debit_active_quarters = [
        q for q in st.session_state.ficad_quarters
        if round(q["ss_tax"] + q["med_tax"], 2) > 0
    ]
    if _ficad_debit_active_quarters:
        st.divider()
        st.subheader("CS Tools Adjustment Summary")
        st.caption("Paste a CS Tools link for each quarter to make the header clickable")
        for q in _ficad_debit_active_quarters:
            st.text_input(f"Q{q['qnum']} CS Tools Link", placeholder="Paste link here...", key=f"ficad_q{q['qnum']}_link", label_visibility="visible")
        st.text_input("Credit Date", placeholder="e.g. 01/15/2025", key="ficad_credit_date", label_visibility="visible")

        st.divider()

        _ficad_debit_credit_date = st.session_state.get("ficad_credit_date", "").strip() or "XXXXX"
        _ficad_debit_fica_only   = st.session_state.ficad_fica_only == "Yes"
        _ficad_debit_html = '<div style="font-size:0.9rem; line-height:1.8;">'
        if len(_ficad_debit_active_quarters) == 1:
            _ficad_debit_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustment has been completed and can be viewed below:</p>'
        elif len(_ficad_debit_active_quarters) >= 2:
            _ficad_debit_html += '<p style="margin:0 0 8px 0; line-height:1.4;">The adjustments have been completed and can be viewed below:</p>'
        for q in _ficad_debit_active_quarters:
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
        if st.session_state.ficad_selected_year < _date.today().year:
            _ficad_debit_html += '<p style="margin:0; line-height:1.4;">The W-2c has been generated and can be viewed in the member documents center.</p>'
        _ficad_debit_html += '</div>'

        st.markdown(_ficad_debit_html, unsafe_allow_html=True)

