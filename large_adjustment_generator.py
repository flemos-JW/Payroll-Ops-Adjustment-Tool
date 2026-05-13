import io
import csv
import pandas as pd
import streamlit as st
from components import (
    inject_dashboard_css, kpi_card_html, render_section_divider,
    render_dashboard_header, render_auth_screen, render_app_sidebar,
    inject_global_css, page_config,
)

page_config("Large Adjustment Generator", "")


# ---------------------------------------------------------------------------
# SUI wage bases
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

SS_RATE             = 0.062
MEDICARE_RATE       = 0.0145
ADD_MEDICARE_RATE   = 0.009
ADD_MEDICARE_THRESH = 200_000

# ---------------------------------------------------------------------------
# Calculation functions
# ---------------------------------------------------------------------------
def calc_taxes(gross, ytd_ss, ytd_med, ss_wage_base, custom_rates):
    ss_room     = max(0.0, ss_wage_base - ytd_ss)
    ss_taxable  = min(gross, ss_room)
    ss_amount   = round(ss_taxable * SS_RATE, 2)

    med_amount  = round(gross * MEDICARE_RATE, 2)

    ytd_after       = ytd_med + gross
    prev_over       = max(0.0, ytd_med   - ADD_MEDICARE_THRESH)
    curr_over       = max(0.0, ytd_after - ADD_MEDICARE_THRESH)
    add_med_taxable = max(0.0, curr_over - prev_over)
    add_med_amount  = round(add_med_taxable * ADD_MEDICARE_RATE, 2)

    futa_room    = max(0.0, 7000.0 - ytd_med)
    futa_taxable = min(gross, futa_room)
    futa_amount  = round(futa_taxable * 0.006, 2)

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

def fmt(n):
    return f"${n:,.2f}"


def _client_friendly_tax_name(name):
    """Convert internal tax-line names into client-facing descriptions.
    Strips internal prefixes and translates ambiguous labels."""
    if not name:
        return ""
    s = str(name).strip()
    if s.startswith("Federal · "):
        s = s[len("Federal · "):]
    mapping = {
        "Federal - Employee Withholding":               "Federal Income Tax Withholding",
        "Federal - Employee Medicare":                  "Medicare",
        "Federal - Employee Additional Medicare":       "Additional Medicare",
        "Federal - Employee Social Security  (OASDI)":  "Social Security",
        "Federal - Employer Medicare":                  "Medicare (Employer)",
        "Federal - Employer Social Security (OASDI)":   "Social Security (Employer)",
        "Federal - Employer Unemployment":              "Federal Unemployment (FUTA)",
    }
    if s in mapping:
        return mapping[s]
    # "{State} - Employee Withholding" → "{State} State Income Tax Withholding"
    if s.endswith(" - Employee Withholding"):
        state = s[: -len(" - Employee Withholding")]
        return f"{state} State Income Tax Withholding"
    return s


def _html_to_pdf_bytes(html_content: str) -> bytes:
    """Render HTML to a PDF document using headless Chromium via Playwright.
    Returns the PDF as bytes, ready to hand to st.download_button."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "Playwright is required for PDF export. Install with:\n"
            "  python3 -m pip install playwright\n"
            "  python3 -m playwright install chromium"
        ) from e

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_content(html_content, wait_until="domcontentloaded")
            pdf_bytes = page.pdf(
                format="Letter",
                margin={"top": "0.55in", "bottom": "0.55in",
                        "left": "0.55in", "right": "0.55in"},
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            browser.close()
    return pdf_bytes


def _build_client_report_html(results, detail_list, name_by_mid, cid, adj_date, year, include_futa=True):
    """Render a self-contained, print-friendly HTML report for client delivery.
    Tax codes are intentionally omitted — only human descriptions are shown."""
    import datetime as _dt
    import html as _html

    # Helpers (module fmt is $X,XXX.XX)
    def _safe_float(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    # Aggregate summary metrics (employer side includes ER SS + ER Medicare)
    total_gross = sum(_safe_float(r.get("Gross Pay", 0))           for r in results)
    total_net   = sum(_safe_float(r.get("Net Pay", 0))             for r in results)
    ee_tax      = sum(_safe_float(r.get("Total Employee Tax", 0))  for r in results)
    er_ss_sum   = sum(_safe_float(r.get("SS Employee", 0))         for r in results)
    er_med_sum  = sum(_safe_float(r.get("Medicare Employee", 0))   for r in results)
    er_oth_sum  = sum(_safe_float(r.get("Employer Taxes", 0))      for r in results)
    futa_sum    = sum(_safe_float(r.get("FUTA", 0))                for r in results) if include_futa else 0.0
    er_tax      = er_ss_sum + er_med_sum + er_oth_sum + futa_sum
    total_debit = ee_tax + er_tax
    num_emp     = len(results)

    detail_by_mid = {d["mid"]: d for d in detail_list}

    # Per-employee sections
    emp_html_parts = []
    for r in results:
        mid = str(r.get("MID", "")).strip()
        d   = detail_by_mid.get(mid)
        if not d:
            continue

        name      = name_by_mid.get(mid, "")
        state     = r.get("State", "") or ""
        gross     = _safe_float(r.get("Gross Pay", 0))
        net       = _safe_float(r.get("Net Pay", 0))
        e_ee_tax  = _safe_float(r.get("Total Employee Tax", 0))
        e_ss      = _safe_float(r.get("SS Employee", 0))
        e_med     = _safe_float(r.get("Medicare Employee", 0))
        e_futa    = _safe_float(r.get("FUTA", 0)) if include_futa else 0.0
        e_er_oth  = _safe_float(r.get("Employer Taxes", 0))
        e_er_tax  = e_ss + e_med + e_futa + e_er_oth
        e_debit   = e_ee_tax + e_er_tax

        res      = d["result"]
        er_rates = d["er_rates"]
        adj      = d.get("adjustment")

        # Tax-line rows
        lines = []  # (side, description, taxable, amount)
        for item in res.get("custom_items", []):
            _nm, _cd, _rt, _tx, _am, _ytd = item
            lines.append(("Employee", _client_friendly_tax_name(_nm),
                          _safe_float(_tx), _safe_float(_am)))
        lines.append(("Employee", "Social Security",
                      _safe_float(res.get("ss_taxable", 0)),
                      _safe_float(res.get("ss_amount", 0))))
        lines.append(("Employee", "Medicare", gross, _safe_float(res.get("med_amount", 0))))
        if _safe_float(res.get("add_med_amount", 0)) > 0:
            lines.append(("Employee", "Additional Medicare",
                          _safe_float(res.get("add_med_taxable", 0)),
                          _safe_float(res.get("add_med_amount", 0))))
        lines.append(("Employer", "Social Security",
                      _safe_float(res.get("ss_taxable", 0)),
                      _safe_float(res.get("ss_amount", 0))))
        lines.append(("Employer", "Medicare", gross, _safe_float(res.get("med_amount", 0))))
        if include_futa:
            lines.append(("Employer", "Federal Unemployment (FUTA)",
                          _safe_float(res.get("futa_taxable", 0)),
                          _safe_float(res.get("futa_amount", 0))))
        for _nm, _cd, _rt, _lr, _ytd in er_rates:
            _taxable = min(gross, _lr) if _lr is not None else gross
            _amt     = round(_taxable * _rt / 100, 2)
            lines.append(("Employer", _client_friendly_tax_name(_nm), _taxable, _amt))

        rows_html = ""
        for side, desc, txable, amt in lines:
            cls = "side-ee" if side == "Employee" else "side-er"
            rows_html += (
                f'<tr><td><span class="{cls}">{side}</span></td>'
                f'<td>{_html.escape(desc)}</td>'
                f'<td class="right">{fmt(txable)}</td>'
                f'<td class="right">{fmt(amt)}</td></tr>\n'
            )
        rows_html += (
            f'<tr class="subtotal"><td colspan="3">Total Company Debit</td>'
            f'<td class="right">{fmt(e_debit)}</td></tr>'
        )

        # Adjustment explainer
        adjustment_html = ""
        if adj and adj.get("applied"):
            diff = _safe_float(adj.get("diff", 0))
            diff_abs = fmt(abs(diff))
            diff_prefix = "+" if diff > 0 else "−"
            state_for_msg = state or "the employee's state"
            _split_details = adj.get("split", [])
            if len(_split_details) >= 2:
                _fed_detail = next((d for d in _split_details if "federal" in d.get("location", "")), {})
                _st_detail  = next((d for d in _split_details if d.get("location") == "state_450"), {})
                reason = (
                    f"The variance was split <b>70% to Federal Withholding</b> ({fmt(abs(_safe_float(_fed_detail.get('share', 0))))}) "
                    f"and <b>30% to State Withholding</b> ({fmt(abs(_safe_float(_st_detail.get('share', 0))))})."
                )
            elif len(_split_details) == 1:
                _d = _split_details[0]
                if "federal" in _d.get("location", ""):
                    reason = (
                        f"{_html.escape(state_for_msg)} has no state withholding code, "
                        f"so 100% of the variance was applied to Federal Withholding."
                    )
                else:
                    reason = (
                        f"The variance was applied to the state withholding line."
                    )
            else:
                reason = ""
            adjustment_html = f"""
            <div class="adjustment">
              <div class="adjustment-title">Withholding Adjustment Applied</div>
              <div class="adjustment-body">
                The calculated total withholding of <b>{fmt(_safe_float(adj.get('calculated_total', 0)))}</b>
                differed from the amount actually withheld (<b>{fmt(_safe_float(adj.get('target_withheld', 0)))}</b>)
                by <b style="color:{'#047857' if diff > 0 else '#be123c'};">{diff_prefix}{diff_abs}</b>.
                {reason}
              </div>
            </div>
            """

        name_block = (
            f'<div class="employee-name">{_html.escape(name)}</div>'
            f'<div class="employee-mid">MID: {_html.escape(mid)}</div>'
            if name else
            f'<div class="employee-name">MID: {_html.escape(mid)}</div>'
        )

        emp_html_parts.append(f"""
        <section class="employee">
          <header class="employee-header">
            <div>{name_block}</div>
            <div class="employee-state">{_html.escape(state) if state else "—"}</div>
          </header>

          <div class="emp-totals">
            <div><div class="label">Gross Pay</div><div class="value">{fmt(gross)}</div></div>
            <div><div class="label">Net Pay</div><div class="value">{fmt(net)}</div></div>
            <div><div class="label">Employee Tax</div><div class="value">{fmt(e_ee_tax)}</div></div>
            <div><div class="label">Employer Cost</div><div class="value">{fmt(e_er_tax)}</div></div>
            <div><div class="label">Total Debit</div><div class="value">{fmt(e_debit)}</div></div>
          </div>

          <table class="taxes">
            <thead>
              <tr>
                <th>Side</th>
                <th>Tax</th>
                <th class="right">Taxable Wages</th>
                <th class="right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>

          {adjustment_html}
        </section>
        """)

    employee_sections = "".join(emp_html_parts)
    timestamp         = _dt.datetime.now().strftime("%B %d, %Y · %I:%M %p")
    cid_safe          = _html.escape(cid) if cid else "—"
    adj_date_safe     = _html.escape(str(adj_date)) if adj_date else "—"
    year_safe         = _html.escape(str(year)) if year else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>W-2C Adjustment Report · {cid_safe}</title>
  <style>
    @page {{ margin: 0.6in; }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #1e293b; background: #fff; line-height: 1.55;
      max-width: 900px; margin: 0 auto; padding: 24px;
    }}
    .doc-header {{ border-bottom: 3px solid #1e40af; padding-bottom: 18px; margin-bottom: 24px; }}
    .doc-header h1 {{ margin: 0; font-size: 26px; color: #1e40af; letter-spacing: 0.01em; }}
    .doc-meta {{ color: #64748b; font-size: 13px; margin-top: 10px; }}
    .doc-meta strong {{ color: #334155; }}

    .summary {{
      background: linear-gradient(135deg, #f1f5f9, #eff6ff);
      border: 1px solid #cbd5e1;
      border-radius: 8px; padding: 18px 22px; margin: 20px 0 28px 0;
    }}
    .summary-grid {{
      display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px;
    }}
    .summary-grid .metric {{ text-align: center; }}
    .summary-grid .label {{
      color: #64748b; font-size: 10px; text-transform: uppercase;
      letter-spacing: 0.1em; font-weight: 700;
    }}
    .summary-grid .value {{
      font-size: 18px; font-weight: 700; color: #1e40af; margin-top: 4px;
      font-variant-numeric: tabular-nums;
    }}

    h2.section-title {{ color: #1e293b; font-size: 17px; margin: 28px 0 10px 0; }}

    section.employee {{
      background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
      padding: 18px 22px; margin: 16px 0; page-break-inside: avoid;
    }}
    .employee-header {{
      display: flex; justify-content: space-between; align-items: baseline;
      border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 14px;
    }}
    .employee-name {{ font-size: 17px; font-weight: 700; color: #0f172a; }}
    .employee-mid {{ color: #64748b; font-size: 12px; margin-top: 2px; }}
    .employee-state {{
      background: #dbeafe; color: #1e40af;
      padding: 3px 12px; border-radius: 12px;
      font-size: 12px; font-weight: 700;
    }}

    .emp-totals {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 14px; }}
    .emp-totals .label {{
      color: #64748b; font-size: 9px; text-transform: uppercase;
      font-weight: 700; letter-spacing: 0.08em;
    }}
    .emp-totals .value {{
      font-size: 14px; font-weight: 700; color: #0f172a;
      font-variant-numeric: tabular-nums;
    }}

    table.taxes {{ width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 12px 0 4px 0; }}
    table.taxes th {{
      background: #f8fafc; text-align: left; padding: 8px 12px;
      border-bottom: 2px solid #cbd5e1; color: #475569;
      font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.05em;
    }}
    table.taxes th.right, table.taxes td.right {{
      text-align: right; font-variant-numeric: tabular-nums;
    }}
    table.taxes td {{ padding: 7px 12px; border-bottom: 1px solid #f1f5f9; }}
    .side-ee {{ color: #be185d; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .side-er {{ color: #ca8a04; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; }}
    table.taxes tr.subtotal td {{
      font-weight: 700; background: #f8fafc; color: #0f172a;
      border-top: 2px solid #cbd5e1; border-bottom: none;
    }}

    .adjustment {{
      background: #fffbeb; border-left: 4px solid #f59e0b;
      border-radius: 4px; padding: 12px 16px; margin: 14px 0 4px 0;
    }}
    .adjustment-title {{
      color: #92400e; font-weight: 700; font-size: 11px;
      text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
    }}
    .adjustment-body {{ color: #422006; font-size: 13px; line-height: 1.6; }}

    .doc-footer {{
      margin-top: 36px; padding-top: 14px;
      border-top: 1px solid #e2e8f0;
      color: #94a3b8; font-size: 11px; text-align: center;
    }}

    @media print {{
      body {{ max-width: 100%; padding: 0; }}
      section.employee {{ page-break-inside: avoid; }}
      .doc-header, .summary {{ page-break-after: avoid; }}
    }}
  </style>
</head>
<body>

  <div class="doc-header">
    <h1>W-2C Adjustment Report</h1>
    <div class="doc-meta">
      <strong>Company:</strong> {cid_safe}
      &nbsp; · &nbsp; <strong>Adjustment Date:</strong> {adj_date_safe}
      &nbsp; · &nbsp; <strong>Tax Year:</strong> {year_safe}
    </div>
  </div>

  <div class="summary">
    <div class="summary-grid">
      <div class="metric"><div class="label">Employees</div><div class="value">{num_emp}</div></div>
      <div class="metric"><div class="label">Total Gross</div><div class="value">{fmt(total_gross)}</div></div>
      <div class="metric"><div class="label">Total Net</div><div class="value">{fmt(total_net)}</div></div>
      <div class="metric"><div class="label">Employee Tax</div><div class="value">{fmt(ee_tax)}</div></div>
      <div class="metric"><div class="label">Employer Cost</div><div class="value">{fmt(er_tax)}</div></div>
    </div>
    <div style="text-align:center; margin-top:12px; color:#475569; font-size:13px;">
      <b>Total Company Debit:</b>
      <span style="color:#1e40af; font-size:18px; font-weight:700; font-variant-numeric:tabular-nums;">
        {fmt(total_debit)}
      </span>
    </div>
  </div>

  <h2 class="section-title">Per-Employee Breakdown</h2>
  {employee_sections}

  <div class="doc-footer">
    Report generated {timestamp} · Confidential payroll document
  </div>

</body>
</html>"""

# ---------------------------------------------------------------------------
# Tax code data
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
    "New York - Employee PFL": "33-468",
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

STATE_ABBREV = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "PR": "Puerto Rico", "VI": "Virgin Islands",
}

STATE_CENTROIDS = {
    "Alabama":              (32.806671, -86.791130),
    "Alaska":               (61.370716, -152.404419),
    "Arizona":              (33.729759, -111.431221),
    "Arkansas":             (34.969704, -92.373123),
    "California":           (36.116203, -119.681564),
    "Colorado":             (39.059811, -105.311104),
    "Connecticut":          (41.597782, -72.755371),
    "Delaware":             (39.318523, -75.507141),
    "District of Columbia": (38.897438, -77.026817),
    "Florida":              (27.766279, -81.686783),
    "Georgia":              (33.040619, -83.643074),
    "Hawaii":               (21.094318, -157.498337),
    "Idaho":                (44.240459, -114.478828),
    "Illinois":             (40.349457, -88.986137),
    "Indiana":              (39.849426, -86.258278),
    "Iowa":                 (42.011539, -93.210526),
    "Kansas":               (38.526600, -96.726486),
    "Kentucky":             (37.668140, -84.670067),
    "Louisiana":            (31.169546, -91.867805),
    "Maine":                (44.693947, -69.381927),
    "Maryland":             (39.063946, -76.802101),
    "Massachusetts":        (42.230171, -71.530106),
    "Michigan":             (43.326618, -84.536095),
    "Minnesota":            (45.694454, -93.900192),
    "Mississippi":          (32.741646, -89.678696),
    "Missouri":             (38.456085, -92.288368),
    "Montana":              (46.921925, -110.454353),
    "Nebraska":             (41.125370, -98.268082),
    "Nevada":               (38.313515, -117.055374),
    "New Hampshire":        (43.452492, -71.563896),
    "New Jersey":           (40.298904, -74.521011),
    "New Mexico":           (34.840515, -106.248482),
    "New York":             (42.165726, -74.948051),
    "North Carolina":       (35.630066, -79.806419),
    "North Dakota":         (47.528912, -99.784012),
    "Ohio":                 (40.388783, -82.764915),
    "Oklahoma":             (35.565342, -96.928917),
    "Oregon":               (44.572021, -122.070938),
    "Pennsylvania":         (40.590752, -77.209755),
    "Puerto Rico":          (18.220833,  -66.590149),
    "Rhode Island":         (41.680893, -71.511780),
    "South Carolina":       (33.856892, -80.945007),
    "South Dakota":         (44.299782, -99.438828),
    "Tennessee":            (35.747845, -86.692345),
    "Texas":                (31.054487, -97.563461),
    "Utah":                 (40.150032, -111.862434),
    "Vermont":              (44.045876, -72.710686),
    "Virgin Islands":       (18.335765, -64.896335),
    "Virginia":             (37.769337, -78.169968),
    "Washington":           (47.400902, -121.490494),
    "West Virginia":        (38.491226, -80.954453),
    "Wisconsin":            (44.268543, -89.616508),
    "Wyoming":              (42.755966, -107.302490),
}

HARDCODED_RATES = {
    "California - Employee Disability": {2024: 1.1, 2025: 1.2, 2026: 1.3},
}

# State supplemental withholding rates (%) — applied to -450 codes when "Supplemental Rates" enabled
# States with no income tax (AK, FL, NV, NH, SD, TN, TX, WY) excluded.
# Vermont: 30% of federal supplemental (22%) = 6.6% of gross
# Wisconsin: graduated brackets (see WISCONSIN_SUPPLEMENTAL_BRACKETS)
STATE_SUPPLEMENTAL_RATES = {
    "Alabama":              {2025: 5.0,    2026: 5.0},
    "Arizona":              {2025: 2.5,    2026: 2.5},
    "Arkansas":             {2025: 3.9,    2026: 3.9},
    "California":           {2025: 6.6,    2026: 6.6},
    "Colorado":             {2025: 4.4,    2026: 4.4},
    "Connecticut":          {2025: 6.99,   2026: 6.99},
    "Delaware":             {2025: 5.0,    2026: 5.0},
    "District of Columbia": {2025: 10.75,  2026: 10.75},
    "Georgia":              {2025: 5.39,   2026: 5.19},
    "Hawaii":               {2025: 7.9,    2026: 7.9},
    "Idaho":                {2025: 5.695,  2026: 5.3},
    "Illinois":             {2025: 4.95,   2026: 4.95},
    "Indiana":              {2025: 3.0,    2026: 2.95},
    "Iowa":                 {2025: 3.8,    2026: 3.8},
    "Kansas":               {2025: 5.0,    2026: 5.0},
    "Kentucky":             {2025: 4.0,    2026: 3.5},
    "Louisiana":            {2025: 3.09,   2026: 3.09},
    "Maine":                {2025: 5.0,    2026: 5.0},
    "Maryland":             {2025: 0.0,    2026: 6.5},
    "Massachusetts":        {2025: 5.0,    2026: 5.0},
    "Michigan":             {2025: 4.25,   2026: 4.25},
    "Minnesota":            {2025: 6.25,   2026: 6.25},
    "Mississippi":          {2025: 4.4,    2026: 4.0},
    "Missouri":             {2025: 4.7,    2026: 4.7},
    "Montana":              {2025: 5.0,    2026: 5.0},
    "Nebraska":             {2025: 5.0,    2026: 3.5},
    "New Jersey":           {2025: 11.8,   2026: 11.8},
    "New Mexico":           {2025: 5.9,    2026: 5.9},
    "New York":             {2025: 11.7,   2026: 11.7},
    "North Carolina":       {2025: 4.35,   2026: 4.09},
    "North Dakota":         {2025: 1.5,    2026: 1.5},
    "Ohio":                 {2025: 3.5,    2026: 2.75},
    "Oklahoma":             {2025: 4.75,   2026: 4.5},
    "Oregon":               {2025: 8.0,    2026: 8.0},
    "Pennsylvania":         {2025: 3.07,   2026: 3.07},
    "Rhode Island":         {2025: 5.99,   2026: 5.99},
    "South Carolina":       {2025: 6.2,    2026: 6.0},
    "Utah":                 {2025: 4.55,   2026: 4.5},
    "Vermont":              {2025: 6.6,    2026: 6.6},
    "Virginia":             {2025: 5.75,   2026: 5.75},
    "West Virginia":        {2025: 4.82,   2026: 4.82},
    "Wisconsin":            {2025: None,   2026: None},
}

# Wisconsin: graduated supplemental brackets based on gross amount
WISCONSIN_SUPPLEMENTAL_BRACKETS = [
    (12_760.00, 3.54),
    (25_520.00, 4.65),
    (280_950.00, 5.30),
    (float("inf"), 7.65),
]

# States requiring user verification of supplemental rate (by year)
SUPPLEMENTAL_RATE_WARNINGS = {
    "Maryland": {2025: "Maryland has no standard supplemental rate for 2025. Verify the correct rate and enter it manually."},
}

TAX_DESCRIPTIONS = sorted(DESC_TO_CODE.keys())

_EXCLUDED_DESCRIPTIONS = {
    "Federal - Employee Medicare",
    "Federal - Employee Social Security  (OASDI)",
    "Federal - Employee Additional Medicare",
    "Federal - Employer Medicare",
    "Federal - Employer Social Security (OASDI)",
}

EMPLOYEE_DESCRIPTIONS = [d for d in TAX_DESCRIPTIONS if "employee" in d.lower() and d not in _EXCLUDED_DESCRIPTIONS]
EMPLOYER_DESCRIPTIONS = [d for d in TAX_DESCRIPTIONS if "employer" in d.lower() and d not in _EXCLUDED_DESCRIPTIONS]

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

TICKET_TYPES = ["", "MDV", "MISC Fully Taxable"]

_TICKET_NOTES = {
    "MDV":                "MDV refund - ",
    "MISC Fully Taxable": "Recording Wages - ",
}

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
render_auth_screen("Large Adjustment Generator", "PayOps2026")

if "_clear_count" not in st.session_state:
    st.session_state._clear_count = 0

def _clear_all():
    new_count = st.session_state._clear_count + 1
    st.session_state.clear()
    st.session_state.authenticated = True
    st.session_state._clear_count = new_count
    st.rerun()

render_app_sidebar("Large Adj Generator", "v3.0", "#00e5ff",
                   quick_actions=[{"label": "Clear Data", "callback": _clear_all,
                                   "key": "lag_clear", "type": "primary"}])

inject_global_css("lag")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_pasted_table(text, expected_cols):
    text = text.strip()
    if not text:
        return None
    for sep in ("\t", ","):
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=0, dtype=str)
            df = df.dropna(how="all")
            if df.shape[1] >= len(expected_cols):
                df = df.iloc[:, :len(expected_cols)]
                df.columns = expected_cols
                df = df.apply(lambda s: s.str.strip() if s.dtype == object else s)
                return df
        except Exception:
            continue
    return None

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

_WRITEIN = "— Write in custom —"

def _remove_tax(state_key, idx, key_prefix):
    taxes = st.session_state[state_key]
    taxes.pop(idx)
    for j in range(len(taxes) + 5):
        for sfx in ("tname", "trate", "tlimit", "tytd", "tlimit_amt", "custom_name", "custom_code"):
            st.session_state.pop(f"{key_prefix}_{sfx}_{j}", None)
    for j, tax in enumerate(taxes):
        st.session_state[f"{key_prefix}_tname_{j}"]  = "— Write in custom —" if tax.get("custom_entry") else tax.get("name", "")
        st.session_state[f"{key_prefix}_trate_{j}"]  = float(tax.get("rate", 0.0))
        st.session_state[f"{key_prefix}_tlimit_{j}"] = tax.get("limit", "No")
        if tax.get("custom_entry"):
            st.session_state[f"{key_prefix}_custom_name_{j}"] = tax.get("custom_name", "")
            st.session_state[f"{key_prefix}_custom_code_{j}"] = tax.get("custom_code", "")
        if tax.get("limit") == "Yes":
            st.session_state[f"{key_prefix}_tytd_{j}"]       = float(tax.get("ytd_limit", 0.0))
            st.session_state[f"{key_prefix}_tlimit_amt_{j}"] = float(tax.get("limit_amount", 0.0))

def _tax_rows(taxes, key_prefix, descriptions, allow_no_limit_flag=False, state_key=None):
    for i, tax in enumerate(taxes):
        _is_custom  = tax.get("custom_entry", False)
        _dd_opts    = ["", _WRITEIN] + descriptions
        _dd_val     = _WRITEIN if _is_custom else tax.get("name", "")
        _dd_idx     = _dd_opts.index(_dd_val) if _dd_val in _dd_opts else 0
        _tname_key  = f"{key_prefix}_tname_{i}"

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
            else:
                code = DESC_TO_CODE.get(sel, "")
                taxes[i]["custom_code"] = code
                st.markdown(f'<div style="padding:8px 4px; font-size:1rem; font-weight:600; color:inherit;">{code or "—"}</div>', unsafe_allow_html=True)

        with c3:
            _trate_key    = f"{key_prefix}_trate_{i}"
            _trate_kwargs = {"value": float(tax["rate"])} if _trate_key not in st.session_state else {}
            rate = st.number_input(
                "Rate",
                min_value=0.0, max_value=100.0,
                step=0.0001, format="%.4f",
                key=_trate_key,
                label_visibility="collapsed",
                **_trate_kwargs,
            )
            taxes[i]["rate"] = rate

        with c4:
            _no_limit   = allow_no_limit_flag and (sel == "Federal - Employee Withholding")
            _tlimit_key = f"{key_prefix}_tlimit_{i}"
            if _no_limit:
                st.session_state[_tlimit_key] = "No"
            _tlimit_opts = ["No", "Yes"]
            _tlimit_kwargs = {} if _tlimit_key in st.session_state else {"index": _tlimit_opts.index(tax.get("limit", "No"))}
            limit = st.selectbox(
                "Limit",
                options=_tlimit_opts,
                key=_tlimit_key,
                label_visibility="collapsed",
                disabled=_no_limit,
                **_tlimit_kwargs,
            )
            taxes[i]["limit"] = limit

        with c5:
            st.button("✕", key=f"{key_prefix}_tremove_{i}",
                      on_click=_remove_tax, args=(state_key, i, key_prefix))

        if limit == "Yes":
            l1, l2 = st.columns([1, 1])
            _tytd_key   = f"{key_prefix}_tytd_{i}"
            _tlimit_key = f"{key_prefix}_tlimit_amt_{i}"
            with l1:
                _tytd_kwargs = {"value": float(tax.get("ytd_limit", 0.0))} if _tytd_key not in st.session_state else {}
                ytd_limit = st.number_input(
                    "YTD",
                    min_value=0.0, step=100.0, format="%.2f",
                    key=_tytd_key,
                    **_tytd_kwargs,
                )
                taxes[i]["ytd_limit"] = ytd_limit
            with l2:
                _tlimit_kwargs = {"value": float(tax.get("limit_amount", 0.0))} if _tlimit_key not in st.session_state else {}
                limit_amount = st.number_input(
                    "Limit",
                    min_value=0.0, step=100.0, format="%.2f",
                    key=_tlimit_key,
                    **_tlimit_kwargs,
                )
                taxes[i]["limit_amount"] = limit_amount

# ---------------------------------------------------------------------------
# Layout: tabs — Settings | Employee Data | Data Dump
# ---------------------------------------------------------------------------
tab_settings, tab_employees, tab_dump, tab_addl, tab_custom, tab_results, tab_viz = st.tabs(
    ["Settings", "Employee Data", "Data Dump", "Additional Taxes", "Custom Data", "Results", "Dashboard"]
)

with tab_settings:
    render_section_divider("lag", "SETTINGS", "#00e5ff")

    year_col, mode_col, eetax_col, supfit_col, split_col, incomeonly_col, futa_col = st.columns(7)
    with year_col:
        year         = st.selectbox("Tax Year", [2026, 2025, 2024, 2023], key="lag_year")
        ss_wage_base = SS_WAGE_BASES[year]
        st.caption(f"SS wage base: **${ss_wage_base:,}**")

    with mode_col:
        mode = st.radio("Mode", ["Net Pay", "Gross Up"], key="lag_mode")

    with eetax_col:
        include_er_taxes = st.selectbox("Employer Taxes", ["Yes", "No"], key="lag_include_er_taxes")

    with supfit_col:
        supplemental_fit = st.selectbox("Supplemental Rates", ["No", "Yes"], key="lag_supplemental_fit")
        st.caption("Applies supplemental FIT + state rates")

    with split_col:
        split_csv = st.selectbox("Split CSV", ["No", "Yes"], key="lag_split_csv")
        st.caption("Caps each CSV under $10K employer debit")

    with incomeonly_col:
        only_income = st.selectbox("Only Income Taxes", ["No", "Yes"], key="lag_only_income")
        st.caption("Skips non -450 state taxes (CA keeps all)")

    with futa_col:
        futa_on = st.selectbox("FUTA", ["Yes", "No"], key="lag_include_futa")
        st.caption("Excludes 00-402 when No")

    from datetime import date, timedelta
    _today = date.today()
    _days_until_friday = (4 - _today.weekday()) % 7 or 7
    _default_date = _today + timedelta(days=_days_until_friday)

    d1, d2 = st.columns(2)
    with d1:
        adj_date = st.date_input(
            "Adjustment Date",
            value=st.session_state.get("lag_adj_date", _default_date),
            format="MM/DD/YYYY",
            key=f"lag_adj_date_{st.session_state._clear_count}",
        )
    with d2:
        if "lag_cid" not in st.session_state:
            st.session_state.lag_cid = ""
        st.session_state.lag_cid = st.text_input(
            "CID",
            value=st.session_state.lag_cid,
            key=f"lag_cid_{st.session_state._clear_count}",
            placeholder="e.g. C001",
        )

    if "lag_notes" not in st.session_state:
        st.session_state.lag_notes = ""
    st.session_state.lag_notes = st.text_area(
        "Notes",
        value=st.session_state.lag_notes,
        height=80,
        placeholder="Add any notes here...",
        key=f"lag_notes_{st.session_state._clear_count}",
        label_visibility="collapsed" if st.session_state.lag_notes else "visible",
    )

    st.divider()
    render_section_divider("lag", "PER-EMPLOYEE TAXES", "#8338ec")
    st.caption("Taxes are pre-loaded from the employee's state. Add or adjust as needed per employee.")

    _raw_table_key = f"lag_employee_table_{st.session_state._clear_count}"
    _raw_table_val = st.session_state.get(_raw_table_key, "")
    _emp_preview   = parse_pasted_table(_raw_table_val, ["mid", "pay_amount", "state"])

    if _emp_preview is None or _emp_preview.empty:
        st.caption("Paste employee data on the Employee Data tab first to configure per-employee taxes.")
    else:
        _mids = _emp_preview["mid"].dropna().unique().tolist()
        for _mid in _mids:
            _safe      = "".join(c if c.isalnum() else "_" for c in _mid)
            _ee_key    = f"lag_pe_{_safe}_ee_taxes"
            _er_key    = f"lag_pe_{_safe}_er_taxes"
            _state_key = f"lag_pe_{_safe}_applied_state"

            # Resolve state for this employee (expand abbreviation if needed)
            _emp_row     = _emp_preview[_emp_preview["mid"] == _mid].iloc[0]
            _emp_state_raw = str(_emp_row.get("state", "")).strip()
            _emp_state     = STATE_ABBREV.get(_emp_state_raw.upper(), _emp_state_raw)

            # Additional taxes uploaded via the Additional Taxes tab
            _addl_by_mid = st.session_state.get("lag_addl_by_mid", {})
            _addl_list   = _addl_by_mid.get(_mid, [])
            _addl_sig    = "|".join(f"{e['name']}::{e['code']}" for e in _addl_list)

            # Auto-prefill when state, year, employer-taxes toggle, Supplemental FIT toggle, Only Income Taxes toggle, or additional taxes change
            _include_er       = st.session_state.get("lag_include_er_taxes", "Yes") == "Yes"
            _supplemental_fit = st.session_state.get("lag_supplemental_fit", "No") == "Yes"
            _only_income      = st.session_state.get("lag_only_income", "No") == "Yes"
            _applied_key = f"{_emp_state}|er={_include_er}|sfit={_supplemental_fit}|oi={_only_income}|yr={year}|addl={_addl_sig}"
            if (_emp_state or _addl_list or _supplemental_fit) and st.session_state.get(_state_key) != _applied_key:
                # Only Income Taxes: keep only state withholding (code ends in -450) — CA is always loaded in full
                _state_ee_descs = [d for d in EMPLOYEE_DESCRIPTIONS if d.startswith(_emp_state + " - ")]
                if _only_income and _emp_state != "California":
                    _state_ee_descs = [d for d in _state_ee_descs if DESC_TO_CODE.get(d, "").endswith("-450")]
                _new_ee = [
                    {"name": d, "rate": HARDCODED_RATES.get(d, {}).get(year, 0.0), "limit": "No"}
                    for d in _state_ee_descs
                ]
                # Supplemental Rates — 22% Federal Withholding + state supplemental rate on -450 codes
                if _supplemental_fit:
                    _new_ee.append({"name": "Federal - Employee Withholding", "rate": 22.0, "limit": "No"})
                    _supl_year_rates = STATE_SUPPLEMENTAL_RATES.get(_emp_state, {})
                    _supl_rate = _supl_year_rates.get(year, _supl_year_rates.get(2026, _supl_year_rates.get(2025)))
                    if _supl_rate is None and _emp_state == "Wisconsin":
                        # Wisconsin graduated brackets — resolve from employee gross
                        _emp_row_wi = _emp_preview[_emp_preview["mid"] == _mid]
                        _emp_gross_wi = float(_emp_row_wi.iloc[0]["pay_amount"]) if not _emp_row_wi.empty else 0.0
                        _supl_rate = 3.54
                        for _bracket_limit, _bracket_rate in WISCONSIN_SUPPLEMENTAL_BRACKETS:
                            if _emp_gross_wi <= _bracket_limit:
                                _supl_rate = _bracket_rate
                                break
                    if _supl_rate:
                        for _te in _new_ee:
                            _te_code = DESC_TO_CODE.get(_te.get("name", ""), _te.get("custom_code", ""))
                            if _te_code.endswith("-450"):
                                _te["rate"] = _supl_rate
                                break
                # Append CSV-uploaded additional taxes as write-in entries
                for _e in _addl_list:
                    _new_ee.append({
                        "name":         _e["name"],
                        "custom_entry": True,
                        "custom_name":  _e["name"],
                        "custom_code":  _e["code"],
                        "rate":         0.0,
                        "limit":        "No",
                    })
                _sui_wb = SUI_WAGE_BASES.get(_emp_state, {}).get(year)
                if _include_er:
                    _new_er = []
                    for _t in [{"name": d, "rate": 0.0, "limit": "No"} for d in EMPLOYER_DESCRIPTIONS if d.startswith(_emp_state + " - ")]:
                        if "unemployment" in _t["name"].lower() and _sui_wb:
                            _t["limit"]        = "Yes"
                            _t["limit_amount"] = float(_sui_wb)
                            _t["ytd_limit"]    = 0.0
                        _new_er.append(_t)
                    if not _new_er:
                        _new_er = [{"name": "", "rate": 0.0, "limit": "No"}]
                else:
                    _new_er = []
                if not _new_ee:
                    _new_ee = [{"name": "", "rate": 0.0, "limit": "No"}]
                # Clear the year-prefixed widget keys so _tax_rows renders fresh from the data
                for _j in range(max(20, len(_new_ee) + 5)):
                    for _sfx in ("tname", "trate", "tlimit", "tytd", "tlimit_amt", "custom_name", "custom_code"):
                        st.session_state.pop(f"lag_pe_{_safe}_ee_{year}_{_sfx}_{_j}", None)
                        st.session_state.pop(f"lag_pe_{_safe}_er_{year}_{_sfx}_{_j}", None)
                st.session_state[_ee_key]    = _new_ee
                st.session_state[_er_key]    = _new_er
                st.session_state[_state_key] = _applied_key
            else:
                if _ee_key not in st.session_state:
                    st.session_state[_ee_key] = [{"name": "", "rate": 0.0, "limit": "No"}]
                if _er_key not in st.session_state:
                    st.session_state[_er_key] = [{"name": "", "rate": 0.0, "limit": "No"}]

            _ee_prefix = f"lag_pe_{_safe}_ee_{year}"
            _er_prefix = f"lag_pe_{_safe}_er_{year}"
            _mid_name   = st.session_state.get("lag_name_by_mid", {}).get(_mid, "")
            _label      = f"MID: {_mid}"
            if _mid_name:
                _label += f" · {_mid_name}"
            if _emp_state:
                _label += f" — {_emp_state}"
            with st.expander(_label):
                # Supplemental rate warnings for specific states
                if _supplemental_fit and _emp_state in SUPPLEMENTAL_RATE_WARNINGS:
                    _warn_msg = SUPPLEMENTAL_RATE_WARNINGS[_emp_state].get(year)
                    if _warn_msg:
                        st.warning(_warn_msg)
                if _supplemental_fit and _emp_state == "California":
                    st.info("CA supplemental: 6.6% (default). Use 10.23% for stock options/bonuses if applicable.")
                if _supplemental_fit and _emp_state == "Wisconsin":
                    st.info("WI supplemental: graduated rate applied based on employee gross amount.")
                # Summary metrics for this employee
                _ytd_lookup   = st.session_state.get("lag_ytd_lookup", {})
                _ytd_med_disp = _ytd_lookup.get(_mid, None)
                try:
                    _pay_amt_disp = float(str(_emp_row.get("pay_amount", "0")).replace(",", "").replace("$", ""))
                except (ValueError, TypeError):
                    _pay_amt_disp = 0.0
                _ee_rates_disp = _build_rates(st.session_state.get(_ee_key, []))
                _ytd_ss_disp   = _ytd_med_disp if _ytd_med_disp is not None else 0.0
                _calc_disp     = calc_taxes(_pay_amt_disp, _ytd_ss_disp, _ytd_ss_disp, ss_wage_base, _ee_rates_disp)
                _m1, _m2 = st.columns(2)
                _m1.metric(
                    "YTD Medicare Wages",
                    fmt(_ytd_med_disp) if _ytd_med_disp is not None else "Not loaded",
                )
                _m2.metric("Total Employee Taxes", fmt(_calc_disp["total_tax"]))
                st.divider()
                st.caption("Employee withholdings")
                _peh1, _peh2, _peh3, _peh4, _ = st.columns([3, 1.2, 1.2, 0.9, 0.4])
                _peh1.markdown("**Employee Tax Name**")
                _peh2.markdown("**Tax Code**")
                _peh3.markdown("**Rate (%)**")
                _peh4.markdown("**Limit**")
                _tax_rows(st.session_state[_ee_key], _ee_prefix, EMPLOYEE_DESCRIPTIONS, allow_no_limit_flag=True, state_key=_ee_key)
                if st.button("+ Add Employee Tax", use_container_width=True, key=f"lag_pe_{_safe}_ee_add_{year}"):
                    st.session_state[_ee_key].append({"name": "", "rate": 0.0, "limit": "No"})
                    st.rerun()

                st.divider()
                st.caption("Employer contributions")
                _per1, _per2, _per3, _per4, _ = st.columns([3, 1.2, 1.2, 0.9, 0.4])
                _per1.markdown("**Employer Tax Name**")
                _per2.markdown("**Tax Code**")
                _per3.markdown("**Rate (%)**")
                _per4.markdown("**Limit**")
                _tax_rows(st.session_state[_er_key], _er_prefix, EMPLOYER_DESCRIPTIONS, state_key=_er_key)
                if st.button("+ Add Employer Tax", use_container_width=True, key=f"lag_pe_{_safe}_er_add_{year}"):
                    st.session_state[_er_key].append({"name": "", "rate": 0.0, "limit": "No"})
                    st.rerun()

with tab_employees:
    render_section_divider("lag", "EMPLOYEE DATA", "#06ffa5")
    st.caption("Paste a table with columns: **MID**, **Amount**, **State**. YTD Medicare wages are pulled from the Data Dump tab.")

    raw_table = st.text_area(
        "Employee Table",
        height=300,
        label_visibility="collapsed",
        placeholder="MID\tAmount\tState\nM12345\t5000.00\tNew York\nM67890\t3200.00\tCalifornia",
        key=f"lag_employee_table_{st.session_state._clear_count}",
    )


# ---------------------------------------------------------------------------
# Data Dump tab
# ---------------------------------------------------------------------------
with tab_dump:
    render_section_divider("lag", "DATA DUMP — YTD MEDICARE WAGES", "#00e5ff")
    st.caption("Upload a CSV export. **MEMBER_ID** is used as the MID and **TOTAL_GROSS_AMOUNT** is used as YTD Medicare Wages.")

    uploaded = st.file_uploader("Upload CSV", type="csv", key=f"lag_dump_upload_{st.session_state._clear_count}")

    if uploaded is not None:
        _file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.get("lag_dump_file_id") != _file_id:
            try:
                dump_df = pd.read_csv(uploaded, dtype=str)
                dump_df.columns = [c.strip() for c in dump_df.columns]
                dump_df = dump_df.apply(lambda s: s.str.strip() if s.dtype == object else s)

                missing = [c for c in ("MEMBER_ID", "TOTAL_GROSS_AMOUNT") if c not in dump_df.columns]
                if missing:
                    st.error(f"Missing required column(s): {', '.join(missing)}")
                else:
                    lookup = {}
                    for _, row in dump_df.iterrows():
                        m = str(row["MEMBER_ID"]).strip()
                        if not m:
                            continue
                        try:
                            v = float(str(row["TOTAL_GROSS_AMOUNT"]).replace(",", "").replace("$", ""))
                        except ValueError:
                            v = 0.0
                        # Duplicate MEMBER_ID rows get their amounts summed
                        lookup[m] = lookup.get(m, 0.0) + v
                    st.session_state.lag_ytd_lookup   = lookup
                    st.session_state.lag_dump_file_id = _file_id
                    st.rerun()

            except Exception as e:
                st.error(f"Could not parse CSV: {e}")

    if "lag_ytd_lookup" in st.session_state:
        st.success(f"YTD lookup active — {len(st.session_state.lag_ytd_lookup)} members loaded.")

# ---------------------------------------------------------------------------
# Additional Taxes tab
# ---------------------------------------------------------------------------
with tab_addl:
    render_section_divider("lag", "ADDITIONAL TAXES", "#ffbe0b")
    st.caption(
        "Paste a table with columns **MID**, **Tax Name**, **Tax Code**. Each row is added as a "
        "write-in custom entry in the Employee Withholdings section for the matching MID."
    )

    _addl_key = f"lag_addl_paste_{st.session_state._clear_count}"
    _addl_raw = st.text_area(
        "Additional Taxes Table",
        height=240,
        label_visibility="collapsed",
        placeholder="MID\tTax Name\tTax Code\nM12345\tLocal OPT\t060050030-533\nM67890\tCustom Assessment\t22-461",
        key=_addl_key,
    )

    _addl_df = parse_pasted_table(_addl_raw, ["mid", "tax_name", "tax_code"])
    _addl_by_mid_parsed = {}
    if _addl_df is not None and not _addl_df.empty:
        _seen_codes = {}  # mid -> set of tax codes already added (to dedupe repeat code entries)
        for _, _r in _addl_df.iterrows():
            _m    = str(_r["mid"]).strip()
            _name = str(_r["tax_name"]).strip()
            _code = str(_r["tax_code"]).strip()
            if not _m or not _name:
                continue
            # Skip duplicate (MID, tax code) entries
            _codes_for_mid = _seen_codes.setdefault(_m, set())
            if _code in _codes_for_mid:
                continue
            _codes_for_mid.add(_code)
            _addl_by_mid_parsed.setdefault(_m, []).append({"name": _name, "code": _code})

    if _addl_by_mid_parsed:
        st.session_state.lag_addl_by_mid = _addl_by_mid_parsed
        _total = sum(len(v) for v in _addl_by_mid_parsed.values())
        st.success(f"Additional taxes loaded — {_total} row(s) across {len(_addl_by_mid_parsed)} member(s).")
        with st.expander("Preview loaded rows"):
            _preview = [
                {"MID": m, "Tax Name": e["name"], "Tax Code": e["code"]}
                for m, entries in _addl_by_mid_parsed.items() for e in entries
            ]
            st.dataframe(pd.DataFrame(_preview), use_container_width=True, hide_index=True)
    else:
        st.session_state.pop("lag_addl_by_mid", None)
        if _addl_raw.strip():
            st.warning("Could not parse the pasted table. Expected headers: MID, Tax Name, Tax Code.")

# ---------------------------------------------------------------------------
# Custom Data tab
# ---------------------------------------------------------------------------
with tab_custom:
    render_section_divider("lag", "ACTUAL TAX WITHHELD", "#ff006e")
    st.caption(
        "Paste a table with columns **MID**, **Tax Withheld**. During calculation, the difference "
        "between the employee's calculated total tax and the actual withheld amount is split "
        "**70% to Federal Withholding (00-400)** and **30% to State Withholding (-450)**. "
        "If the employee has no state withholding code, 100% goes to Federal."
    )

    _custom_key = f"lag_custom_data_{st.session_state._clear_count}"
    _custom_raw = st.text_area(
        "Custom Data Table",
        height=240,
        label_visibility="collapsed",
        placeholder="MID\tTax Withheld\nM12345\t1250.00\nM67890\t875.50",
        key=_custom_key,
    )

    _tax_withheld_parsed = {}
    _custom_df = parse_pasted_table(_custom_raw, ["mid", "tax_withheld"])
    if _custom_df is not None and not _custom_df.empty:
        for _, _r in _custom_df.iterrows():
            _m = str(_r["mid"]).strip()
            try:
                _v = float(str(_r["tax_withheld"]).replace(",", "").replace("$", ""))
            except (ValueError, TypeError):
                continue
            if _m:
                # Duplicate MID rows get their withheld amounts summed
                _tax_withheld_parsed[_m] = _tax_withheld_parsed.get(_m, 0.0) + _v

    if _tax_withheld_parsed:
        st.session_state.lag_tax_withheld_by_mid = _tax_withheld_parsed
        st.success(f"{len(_tax_withheld_parsed)} employee withholding override(s) ready to apply.")
        _preview_df = pd.DataFrame(
            [{"MID": m, "Tax Withheld": fmt(v)} for m, v in _tax_withheld_parsed.items()]
        )
        st.dataframe(_preview_df, use_container_width=True, hide_index=True)
    else:
        st.session_state.pop("lag_tax_withheld_by_mid", None)
        if _custom_raw.strip():
            st.warning("Could not parse the pasted table. Expected headers: MID, Tax Withheld.")

    st.divider()
    render_section_divider("lag", "EMPLOYEE NAMES", "#8a9bb0")
    st.caption(
        "Optional. Paste a table with columns **MID**, **Last_Name**, **First_Name**. "
        "Names are used for display only (Settings expander labels and the Dashboard) — they do not affect "
        "any calculations or the CSV export."
    )

    _names_key = f"lag_names_{st.session_state._clear_count}"
    _names_raw = st.text_area(
        "Employee Names Table",
        height=220,
        label_visibility="collapsed",
        placeholder="MID\tLast_Name\tFirst_Name\nM12345\tDoe\tJohn\nM67890\tSmith\tJane",
        key=_names_key,
    )

    _name_by_mid_parsed = {}
    _names_df = parse_pasted_table(_names_raw, ["mid", "last_name", "first_name"])
    if _names_df is not None and not _names_df.empty:
        for _, _r in _names_df.iterrows():
            _m     = str(_r["mid"]).strip()
            _last  = str(_r["last_name"]).strip()
            _first = str(_r["first_name"]).strip()
            if not _m:
                continue
            _full = " ".join(p for p in (_first, _last) if p).strip()
            if _full and _m not in _name_by_mid_parsed:
                # First occurrence wins — duplicate MID rows are ignored
                _name_by_mid_parsed[_m] = _full

    if _name_by_mid_parsed:
        st.session_state.lag_name_by_mid = _name_by_mid_parsed
        st.success(f"{len(_name_by_mid_parsed)} employee name(s) ready for display.")
        _name_preview_df = pd.DataFrame(
            [{"MID": m, "Name": n} for m, n in _name_by_mid_parsed.items()]
        )
        st.dataframe(_name_preview_df, use_container_width=True, hide_index=True)
    else:
        st.session_state.pop("lag_name_by_mid", None)
        if _names_raw.strip():
            st.warning("Could not parse the pasted names table. Expected headers: MID, Last_Name, First_Name.")

# ---------------------------------------------------------------------------
# Dashboard tab
# ---------------------------------------------------------------------------
with tab_viz:
    inject_dashboard_css("viz")
    render_dashboard_header("viz", "⚡ ADJUSTMENT COMMAND CENTER", "LIVE PAYROLL ANALYTICS · TAX OPERATIONS INTELLIGENCE")

    _viz_results = st.session_state.get("lag_results", [])

    if not _viz_results:
        st.info("Generate results on the **Employee Data** tab — the dashboard activates when data is live.")
    else:
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            _plotly_ok = True
        except ImportError:
            _plotly_ok = False
            st.error("This dashboard needs Plotly. Install with: `pip install plotly`")

        if _plotly_ok:
            viz_df = pd.DataFrame(_viz_results)
            for _c in ["Gross Pay", "Net Pay", "YTD Medicare Wages", "SS Employee",
                       "Medicare Employee", "Add. Medicare Employee", "FUTA",
                       "Additional EE Taxes", "Total Employee Tax", "Employer Taxes"]:
                viz_df[_c] = pd.to_numeric(viz_df[_c], errors="coerce").fillna(0.0)

            # ---- Helpers (defined early so all sections can share) ----
            _PALETTE   = ['#00e5ff', '#ff006e', '#8338ec', '#ffbe0b', '#fb5607', '#06ffa5', '#3a86ff', '#2ec4b6']
            _EE_COLORS = ['#ff006e', '#8338ec', '#fb5607', '#ffbe0b']
            _ER_COLORS = ['#00e5ff', '#3a86ff', '#06ffa5', '#2ec4b6']

            def _viz_layout(title=None, height=400):
                cfg = dict(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#c5d1e0', family='system-ui, -apple-system, sans-serif'),
                    margin=dict(l=10, r=10, t=50 if title else 20, b=40),
                    height=height,
                    xaxis=dict(gridcolor='#1e2442', zerolinecolor='#2a3356', color='#8a9bb0'),
                    yaxis=dict(gridcolor='#1e2442', zerolinecolor='#2a3356', color='#8a9bb0'),
                    legend=dict(bgcolor='rgba(10,15,30,0.6)', bordercolor='#2a3356', borderwidth=1, font=dict(color='#c5d1e0')),
                    hoverlabel=dict(bgcolor='#0a0e27', bordercolor='#00e5ff', font=dict(color='#c5d1e0')),
                )
                if title:
                    cfg["title"] = dict(text=title, font=dict(color='#00e5ff', size=14, family='system-ui'))
                return cfg

            _kpi_card = kpi_card_html

            # ---- Aggregate totals — employer side includes ER SS + ER Medicare ----
            _total_gross  = float(viz_df["Gross Pay"].sum())
            _total_net    = float(viz_df["Net Pay"].sum())
            _ee_tax       = float(viz_df["Total Employee Tax"].sum())
            _er_ss_sum    = float(viz_df["SS Employee"].sum())         # ER SS mirrors EE amount (6.2%)
            _er_med_sum   = float(viz_df["Medicare Employee"].sum())   # ER Medicare mirrors EE amount (1.45%)
            _er_other_sum = float(viz_df["Employer Taxes"].sum())
            _futa_sum     = float(viz_df["FUTA"].sum())
            _er_tax       = _er_ss_sum + _er_med_sum + _er_other_sum + _futa_sum
            _total_debit  = _ee_tax + _er_tax
            _eff_rate     = (_ee_tax / _total_gross * 100) if _total_gross > 0 else 0.0
            _num_states   = viz_df["State"].replace("", pd.NA).dropna().nunique()

            # ---- KPI row ----
            _k1, _k2, _k3, _k4, _k5 = st.columns(5)
            _k1.markdown(_kpi_card("Employees",     f"{len(viz_df):,}", "#00e5ff", f"{_num_states} state(s)"),       unsafe_allow_html=True)
            _k2.markdown(_kpi_card("Total Gross",   fmt(_total_gross),  "#06ffa5", "payroll out"),                   unsafe_allow_html=True)
            _k3.markdown(_kpi_card("Total Net",     fmt(_total_net),    "#8338ec", f"{_eff_rate:.2f}% EE withheld"), unsafe_allow_html=True)
            _k4.markdown(_kpi_card("Employer Cost", fmt(_er_tax),       "#ffbe0b", "SS + Med + FUTA + Other"),       unsafe_allow_html=True)
            _k5.markdown(_kpi_card("Total Debit",   fmt(_total_debit),  "#ff006e", "EE tax + ER tax"),               unsafe_allow_html=True)

            # ---- Employee Deep Dive (client-facing drill-down) ----
            render_section_divider("viz", "🔍 EMPLOYEE DEEP DIVE · CLIENT BREAKDOWN", "#00e5ff")

            _viz_detail  = st.session_state.get("lag_detail", [])
            _mid_options = [_r["MID"] for _r in _viz_results]
            _name_by_mid = st.session_state.get("lag_name_by_mid", {})

            def _mid_label(m, _nbm=_name_by_mid):
                _n = _nbm.get(m, "")
                return f"{m} · {_n}" if _n else m

            # Click handler (populated lower down) can set _viz_mid_override; apply before selectbox renders
            _override_mid = st.session_state.pop("_viz_mid_override", None)
            if _override_mid and _override_mid in _mid_options:
                st.session_state["viz_selected_mid"] = _override_mid
            if st.session_state.get("viz_selected_mid") not in _mid_options:
                st.session_state["viz_selected_mid"] = _mid_options[0]

            _sel_mid = st.selectbox(
                "Select an employee (or click a bar in the chart below)",
                options=_mid_options,
                format_func=_mid_label,
                key="viz_selected_mid",
            )

            _sel_row    = next((r for r in _viz_results if r["MID"] == _sel_mid), None)
            _sel_detail = next((d for d in _viz_detail  if d["mid"] == _sel_mid), None)

            if _sel_row and _sel_detail:
                _g       = float(_sel_row["Gross Pay"])
                _n       = float(_sel_row["Net Pay"])
                _ee_t    = float(_sel_row["Total Employee Tax"])
                _ss_a    = float(_sel_row["SS Employee"])
                _med_a   = float(_sel_row["Medicare Employee"])
                _futa_a  = float(_sel_row["FUTA"])
                _er_oth  = float(_sel_row["Employer Taxes"])
                _er_t    = _ss_a + _med_a + _futa_a + _er_oth   # full employer obligation
                _debit_t = _ee_t + _er_t
                _eff_emp = (_ee_t / _g * 100) if _g > 0 else 0.0
                _emp_st  = _sel_row.get("State", "") or "Unknown"

                _sel_name = _name_by_mid.get(_sel_mid, "")
                _name_html = (
                    f'<div style="color:#ffffff; font-size:0.95rem; font-weight:600; margin-top:2px;">{_sel_name}</div>'
                    if _sel_name else ""
                )
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(10,15,30,0.95), rgba(22,33,62,0.95));
                            padding: 14px 22px; border-radius: 10px; margin: 12px 0;
                            border: 1px solid rgba(0,229,255,0.25);
                            display: flex; justify-content: space-between; align-items: center;
                            box-shadow: 0 0 20px rgba(0,229,255,0.1);">
                    <div>
                        <div style="color:#00e5ff; font-size:1.25rem; font-weight:700; letter-spacing:0.04em;
                                    text-shadow: 0 0 12px rgba(0,229,255,0.3);">MID · {_sel_mid}</div>
                        {_name_html}
                        <div style="color:#8a9bb0; font-size:0.85rem; letter-spacing:0.08em; margin-top:2px;">{_emp_st}</div>
                    </div>
                    <div style="color:#c5d1e0; font-size:0.88rem; text-align:right;">
                        <div style="letter-spacing:0.06em;">Effective withholding</div>
                        <div style="color:#ff006e; font-weight:700; font-size:1.15rem;
                                    text-shadow: 0 0 10px rgba(255,0,110,0.3);">{_eff_emp:.2f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                _e1, _e2, _e3, _e4, _e5 = st.columns(5)
                _e1.markdown(_kpi_card("Gross Pay",     fmt(_g),       "#06ffa5", "before deductions"),    unsafe_allow_html=True)
                _e2.markdown(_kpi_card("Net Pay",       fmt(_n),       "#8338ec", "to employee"),          unsafe_allow_html=True)
                _e3.markdown(_kpi_card("Employee Tax",  fmt(_ee_t),    "#ff006e", "withheld from gross"),  unsafe_allow_html=True)
                _e4.markdown(_kpi_card("Employer Cost", fmt(_er_t),    "#ffbe0b", "SS + Med + FUTA + Other"), unsafe_allow_html=True)
                _e5.markdown(_kpi_card("Total Debit",   fmt(_debit_t), "#00e5ff", "company clearing"),     unsafe_allow_html=True)

                # ---- Withholding adjustment explainer ----
                _adj = _sel_detail.get("adjustment")
                if _adj and _adj.get("applied"):
                    _diff_val = float(_adj["diff"])
                    _diff_color = "#06ffa5" if _diff_val > 0 else "#ff006e"
                    _diff_sign  = "+" if _diff_val > 0 else "−"
                    _abs_diff   = fmt(abs(_diff_val))
                    _loc = _adj.get("location")
                    if _loc == "state_450":
                        _reason = f"The <b>{_emp_st}</b> state withholding line (<code style='color:#c5d1e0'>{_adj['tax_code']}</code>) was the closest match, so the variance was absorbed there."
                    elif _loc == "federal_00_400":
                        _reason = f"<b>{_emp_st}</b> has no state withholding tax code, so the variance was routed to the Federal Withholding line (<code style='color:#c5d1e0'>00-400</code>) that Supplemental Rates added."
                    else:
                        _reason = "No existing withholding line was present, so a new Federal Withholding entry (<code style='color:#c5d1e0'>00-400</code>) was created to absorb the variance."
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, rgba(255,190,11,0.08), rgba(255,0,110,0.06));
                                padding: 14px 20px; border-radius: 10px; margin: 14px 0;
                                border-left: 3px solid #ffbe0b;
                                box-shadow: 0 0 15px rgba(255,190,11,0.1);">
                        <div style="color:#ffbe0b; font-size:0.72rem; letter-spacing:0.16em; font-weight:700; margin-bottom:10px;">
                            ⚖️  WITHHOLDING ADJUSTMENT APPLIED
                        </div>
                        <div style="display: flex; gap: 28px; flex-wrap: wrap; align-items: flex-end; color: #c5d1e0;">
                            <div>
                                <div style="color:#8a9bb0; font-size:0.68rem; letter-spacing:0.1em; font-weight:600;">CALCULATED</div>
                                <div style="font-weight:600; font-size:1.05rem; font-variant-numeric:tabular-nums;">{fmt(_adj['calculated_total'])}</div>
                            </div>
                            <div style="color:#4a5a7a; padding-bottom:4px;">→</div>
                            <div>
                                <div style="color:#8a9bb0; font-size:0.68rem; letter-spacing:0.1em; font-weight:600;">ACTUAL WITHHELD</div>
                                <div style="font-weight:600; font-size:1.05rem; font-variant-numeric:tabular-nums;">{fmt(_adj['target_withheld'])}</div>
                            </div>
                            <div>
                                <div style="color:#8a9bb0; font-size:0.68rem; letter-spacing:0.1em; font-weight:600;">VARIANCE</div>
                                <div style="color:{_diff_color}; font-weight:700; font-size:1.1rem; font-variant-numeric:tabular-nums;
                                            text-shadow: 0 0 10px {_diff_color}55;">{_diff_sign}{_abs_diff}</div>
                            </div>
                        </div>
                        <div style="color:#c5d1e0; font-size:0.88rem; margin-top:12px; line-height:1.55;">
                            Applied to <b>{_adj['tax_name']}</b> (<code style='color:#c5d1e0'>{_adj['tax_code']}</code>):
                            <span style='font-variant-numeric:tabular-nums;'>{fmt(_adj['prev_amount'])}</span>
                            <span style="color:#4a5a7a;"> → </span>
                            <b style='font-variant-numeric:tabular-nums; color:#00e5ff;'>{fmt(_adj['new_amount'])}</b>.
                            <br>{_reason}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif _adj and not _adj.get("applied"):
                    st.markdown(f"""
                    <div style="background: rgba(6,255,165,0.06); padding: 10px 16px; border-radius: 8px;
                                margin: 14px 0; border-left: 3px solid #06ffa5;">
                        <div style="color:#06ffa5; font-size:0.75rem; letter-spacing:0.12em; font-weight:700;">
                            ✓ CALCULATED TOTAL MATCHED ACTUAL WITHHELD
                        </div>
                        <div style="color:#8a9bb0; font-size:0.82rem; margin-top:4px;">
                            Both values equal <b style='color:#c5d1e0;'>{fmt(_adj['calculated_total'])}</b> — no adjustment was needed.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="color:#6b7a94; font-size:0.78rem; margin: 10px 0; letter-spacing:0.04em;">
                        No Custom Data entry for this MID — amounts below are straight calculation output.
                    </div>
                    """, unsafe_allow_html=True)

                # Build line items
                _res = _sel_detail["result"]
                _er_rates_line = _sel_detail["er_rates"]
                _lines = []
                for _item in _res.get("custom_items", []):
                    _nm, _cd, _rt, _tx, _am, _ytd = _item
                    _lines.append({"Side":"Employee","Tax Name":_nm,"Tax Code":_cd,
                                   "Rate":f"{_rt:.4f}%","Taxable":float(_tx),"Amount":float(_am)})
                _lines.append({"Side":"Employee","Tax Name":"Federal · Social Security","Tax Code":"00-403",
                               "Rate":"6.2000%","Taxable":float(_res["ss_taxable"]),"Amount":float(_res["ss_amount"])})
                _lines.append({"Side":"Employee","Tax Name":"Federal · Medicare","Tax Code":"00-406",
                               "Rate":"1.4500%","Taxable":float(_g),"Amount":float(_res["med_amount"])})
                if float(_res.get("add_med_amount", 0)) > 0:
                    _lines.append({"Side":"Employee","Tax Name":"Federal · Additional Medicare","Tax Code":"00-901",
                                   "Rate":"0.9000%","Taxable":float(_res["add_med_taxable"]),"Amount":float(_res["add_med_amount"])})
                _lines.append({"Side":"Employer","Tax Name":"Federal · Social Security","Tax Code":"00-404",
                               "Rate":"6.2000%","Taxable":float(_res["ss_taxable"]),"Amount":float(_res["ss_amount"])})
                _lines.append({"Side":"Employer","Tax Name":"Federal · Medicare","Tax Code":"00-407",
                               "Rate":"1.4500%","Taxable":float(_g),"Amount":float(_res["med_amount"])})
                if st.session_state.get("lag_include_futa", "Yes") == "Yes":
                    _lines.append({"Side":"Employer","Tax Name":"Federal · FUTA","Tax Code":"00-402",
                                   "Rate":"0.6000%","Taxable":float(_res["futa_taxable"]),"Amount":float(_res["futa_amount"])})
                for _nm, _cd, _rt, _lr, _ytd in _er_rates_line:
                    _txable = min(_g, _lr) if _lr is not None else _g
                    _amt    = round(_txable * _rt / 100, 2)
                    _lines.append({"Side":"Employer","Tax Name":_nm,"Tax Code":_cd,
                                   "Rate":f"{_rt:.4f}%","Taxable":float(_txable),"Amount":float(_amt)})

                _lines_df = pd.DataFrame(_lines)

                _t_col, _p_col = st.columns([3, 2])
                with _t_col:
                    st.markdown("""
                    <div style="color:#8a9bb0; font-size:0.75rem; letter-spacing:0.14em; font-weight:700;
                                margin: 8px 0 6px 0;">📋 TAX LINE ITEMS · EMPLOYEE & EMPLOYER</div>
                    """, unsafe_allow_html=True)
                    _disp_df = _lines_df.copy()
                    _disp_df["Taxable"] = _disp_df["Taxable"].apply(lambda x: fmt(float(x)))
                    _disp_df["Amount"]  = _disp_df["Amount"].apply(lambda x: fmt(float(x)))
                    st.dataframe(_disp_df, use_container_width=True, hide_index=True, height=400)

                with _p_col:
                    _pos_lines = _lines_df[_lines_df["Amount"] > 0].copy()
                    if not _pos_lines.empty:
                        fig_emp = px.sunburst(
                            _pos_lines, path=["Side", "Tax Name"], values="Amount",
                            color="Side",
                            color_discrete_map={"Employee": "#ff006e", "Employer": "#ffbe0b"},
                        )
                        fig_emp.update_traces(
                            hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>",
                            insidetextfont=dict(color='white', size=11),
                            marker=dict(line=dict(color='#0a0e27', width=1.5)),
                        )
                        fig_emp.update_layout(**_viz_layout(title=f"💠  {_sel_mid} · TAX COMPOSITION", height=400))
                        fig_emp.add_annotation(
                            text=f"<b>{fmt(_debit_t)}</b><br><span style='font-size:9px;color:#8a9bb0;'>total debit</span>",
                            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color='#00e5ff'),
                        )
                        st.plotly_chart(fig_emp, use_container_width=True)

            # ---- Row 2: Geographic heatmap + Tax composition donut ----
            _NAME_TO_ABBREV = {v: k for k, v in STATE_ABBREV.items()}

            # Per-state aggregates — employer side includes ER SS + ER Medicare (mirrors EE amounts)
            _state_rows = []
            for _r in _viz_results:
                _st   = _r["State"] or "Unknown"
                _r_ss = float(_r["SS Employee"])
                _r_md = float(_r["Medicare Employee"])
                _ee   = float(_r["Total Employee Tax"])
                _er   = _r_ss + _r_md + float(_r["FUTA"]) + float(_r["Employer Taxes"])
                _state_rows.append({
                    "state":       _st,
                    "gross":       float(_r["Gross Pay"]),
                    "count":       1,
                    "ee_tax":      _ee,
                    "er_cost":     _er,
                    "total_debit": _ee + _er,
                })
            _state_agg = (pd.DataFrame(_state_rows)
                            .groupby("state", as_index=False)
                            .agg(gross=("gross", "sum"), count=("count", "sum"),
                                 ee_tax=("ee_tax", "sum"), er_cost=("er_cost", "sum"),
                                 total_debit=("total_debit", "sum")))
            _state_agg["abbrev"] = _state_agg["state"].map(_NAME_TO_ABBREV)
            _state_agg_m = _state_agg.dropna(subset=["abbrev"])

            _c_map, _c_donut = st.columns([2, 1])
            with _c_map:
                if not _state_agg_m.empty:
                    _map_metrics = {
                        "Total Debit":   ("total_debit", "Total Debit",   True),
                        "Employees":     ("count",       "Employee Count", False),
                        "Gross Pay":     ("gross",       "Gross Pay",     True),
                        "Employer Cost": ("er_cost",     "Employer Cost", True),
                        "Employee Tax":  ("ee_tax",      "Employee Tax",  True),
                    }
                    _metric_label = st.radio(
                        "Map metric",
                        list(_map_metrics.keys()),
                        horizontal=True,
                        key="viz_map_metric",
                        label_visibility="collapsed",
                    )
                    _metric_col, _metric_title, _is_currency = _map_metrics[_metric_label]

                    # Rich hover: show every metric for every state
                    _custom = list(zip(
                        _state_agg_m["count"].astype(int),
                        _state_agg_m["gross"].astype(float),
                        _state_agg_m["ee_tax"].astype(float),
                        _state_agg_m["er_cost"].astype(float),
                        _state_agg_m["total_debit"].astype(float),
                    ))
                    _hover = (
                        "<b>%{location}</b>"
                        "<br>━━━━━━━━━━━━━"
                        "<br>Employees: <b>%{customdata[0]}</b>"
                        "<br>Gross Pay: $%{customdata[1]:,.2f}"
                        "<br>Employee Tax: $%{customdata[2]:,.2f}"
                        "<br>Employer Cost: $%{customdata[3]:,.2f}"
                        "<br><b>Total Debit: $%{customdata[4]:,.2f}</b>"
                        "<extra></extra>"
                    )

                    fig_map = go.Figure()
                    fig_map.add_trace(go.Choropleth(
                        locations=_state_agg_m["abbrev"],
                        z=_state_agg_m[_metric_col],
                        locationmode='USA-states',
                        customdata=_custom,
                        colorscale=[[0, '#111a35'], [0.35, '#3a86ff'], [0.7, '#8338ec'], [1, '#00e5ff']],
                        marker_line_color='#0a0e27', marker_line_width=0.5,
                        colorbar=dict(
                            title=dict(text=_metric_title, font=dict(color='#8a9bb0')),
                            tickfont=dict(color='#8a9bb0'), thickness=10, len=0.75,
                            bgcolor='rgba(0,0,0,0)',
                            tickprefix=("$" if _is_currency else ""),
                            tickformat=",.0f",
                        ),
                        hovertemplate=_hover,
                    ))

                    # Employee-count bubbles overlaid at state centroids
                    _centroid_rows = [
                        {"state": s, "lat": lat, "lon": lon}
                        for s, (lat, lon) in STATE_CENTROIDS.items()
                    ]
                    _bub_df = _state_agg_m.merge(pd.DataFrame(_centroid_rows), on="state", how="inner")
                    if not _bub_df.empty:
                        _max_c = max(1, int(_bub_df["count"].max()))
                        _sizes = [14 + (int(c) / _max_c) * 34 for c in _bub_df["count"]]
                        fig_map.add_trace(go.Scattergeo(
                            lon=_bub_df["lon"], lat=_bub_df["lat"],
                            text=_bub_df["count"].astype(int).astype(str),
                            mode="markers+text",
                            marker=dict(
                                size=_sizes,
                                color='rgba(255, 0, 110, 0.75)',
                                line=dict(color='rgba(255, 255, 255, 0.7)', width=1.5),
                            ),
                            textfont=dict(color='white', size=10, family='system-ui'),
                            customdata=_bub_df["state"],
                            hovertemplate="<b>%{customdata}</b><br>%{text} employee(s)<extra></extra>",
                            showlegend=False,
                            name="Employees",
                        ))

                    fig_map.update_geos(
                        scope='usa', bgcolor='rgba(0,0,0,0)',
                        lakecolor='#0a0e27', landcolor='#111a35',
                        subunitcolor='#1e2442', showlakes=True,
                    )
                    fig_map.update_layout(**_viz_layout(
                        title=f"🗺️  {_metric_title.upper()} · BUBBLE SIZE = EMPLOYEE COUNT",
                        height=460,
                    ))
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.info("No mappable state data.")

            with _c_donut:
                _tax_totals = [
                    ("EE · Social Security", float(viz_df["SS Employee"].sum()),          _EE_COLORS[0]),
                    ("EE · Medicare",        float(viz_df["Medicare Employee"].sum()),    _EE_COLORS[1]),
                    ("EE · Add. Medicare",   float(viz_df["Add. Medicare Employee"].sum()), _EE_COLORS[2]),
                    ("EE · Additional",      float(viz_df["Additional EE Taxes"].sum()),  _EE_COLORS[3]),
                    ("ER · Social Security", _er_ss_sum,                                  _ER_COLORS[0]),
                    ("ER · Medicare",        _er_med_sum,                                 _ER_COLORS[1]),
                    ("ER · FUTA",            _futa_sum,                                   _ER_COLORS[2]),
                    ("ER · Other",           _er_other_sum,                               _ER_COLORS[3]),
                ]
                _labels = [k for k, v, _c in _tax_totals if v > 0]
                _values = [v for _k, v, _c in _tax_totals if v > 0]
                _colors = [c for _k, v, c in _tax_totals if v > 0]
                if _values:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=_labels, values=_values, hole=0.62,
                        marker=dict(colors=_colors, line=dict(color='#0a0e27', width=2)),
                        textinfo='percent', textfont=dict(color='white', size=11),
                        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
                    )])
                    _donut_layout = _viz_layout(title="💎  TAX COMPOSITION", height=420)
                    _donut_layout["showlegend"] = True
                    _donut_layout["legend"] = dict(
                        orientation='v', yanchor='middle', y=0.5,
                        xanchor='left', x=1.05, font=dict(size=10, color='#c5d1e0'),
                        bgcolor='rgba(10,15,30,0.6)', bordercolor='#2a3356', borderwidth=1,
                    )
                    fig_donut.update_layout(**_donut_layout)
                    fig_donut.add_annotation(text=f"<b>{fmt(sum(_values))}</b>", x=0.5, y=0.5,
                                             font=dict(size=15, color='#00e5ff'), showarrow=False)
                    st.plotly_chart(fig_donut, use_container_width=True)

            # ---- Row 3: Per-employee stacked bar (click a bar to drill into that MID) ----
            _bar_rows = []
            for _r in _viz_results:
                _r_ss  = float(_r["SS Employee"])
                _r_med = float(_r["Medicare Employee"])
                for _tname, _amt in [
                    ("EE · Social Security", _r_ss),
                    ("EE · Medicare",        _r_med),
                    ("EE · Add. Medicare",   float(_r["Add. Medicare Employee"])),
                    ("EE · Additional",      float(_r["Additional EE Taxes"])),
                    ("ER · Social Security", _r_ss),
                    ("ER · Medicare",        _r_med),
                    ("ER · FUTA",            float(_r["FUTA"])),
                    ("ER · Other",           float(_r["Employer Taxes"])),
                ]:
                    _bar_rows.append({"MID": _r["MID"], "Tax Type": _tname, "Amount": _amt})
            _bar_df = pd.DataFrame(_bar_rows)
            _order = _bar_df.groupby("MID")["Amount"].sum().sort_values(ascending=False).index.tolist()

            _bar_color_map = {
                "EE · Social Security": _EE_COLORS[0], "EE · Medicare":      _EE_COLORS[1],
                "EE · Add. Medicare":   _EE_COLORS[2], "EE · Additional":    _EE_COLORS[3],
                "ER · Social Security": _ER_COLORS[0], "ER · Medicare":      _ER_COLORS[1],
                "ER · FUTA":            _ER_COLORS[2], "ER · Other":         _ER_COLORS[3],
            }

            fig_bar = px.bar(
                _bar_df, x="MID", y="Amount", color="Tax Type",
                category_orders={"MID": _order,
                                 "Tax Type": list(_bar_color_map.keys())},
                color_discrete_map=_bar_color_map,
            )
            fig_bar.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.2f}<extra></extra>",
                                  marker=dict(line=dict(color='#0a0e27', width=0.5)))
            fig_bar.update_layout(**_viz_layout(title="📊  TAX BREAKDOWN BY EMPLOYEE · CLICK A BAR TO DRILL DOWN", height=460), barmode='stack')
            fig_bar.update_xaxes(
                tickangle=-45,
                tickvals=_order,
                ticktext=[_mid_label(m) for m in _order],
            )
            fig_bar.update_yaxes(tickprefix="$", tickformat=",.0f")

            # Click handler: capture selected point and drive the deep-dive selectbox
            try:
                _bar_event = st.plotly_chart(
                    fig_bar, use_container_width=True,
                    on_select="rerun", selection_mode="points",
                    key="viz_bar_click_chart",
                )
                _points = None
                if _bar_event is not None:
                    _sel_obj = getattr(_bar_event, "selection", None)
                    if _sel_obj is None and isinstance(_bar_event, dict):
                        _sel_obj = _bar_event.get("selection")
                    if _sel_obj is not None:
                        _points = getattr(_sel_obj, "points", None)
                        if _points is None and isinstance(_sel_obj, dict):
                            _points = _sel_obj.get("points")
                if _points:
                    _p0 = _points[0]
                    _clicked_mid = _p0.get("x") if isinstance(_p0, dict) else getattr(_p0, "x", None)
                    if _clicked_mid and _clicked_mid in _mid_options and _clicked_mid != _sel_mid:
                        st.session_state["_viz_mid_override"] = _clicked_mid
                        st.rerun()
            except TypeError:
                st.plotly_chart(fig_bar, use_container_width=True)

            # ---- State Tax Export (CSV only, no preview) ----
            render_section_divider("viz", "🏛️ STATE TAX EXPORT · CSV", "#8338ec")

            st.markdown("""
            <div style="color:#8a9bb0; font-size:0.85rem; line-height:1.6; margin:6px 0 14px 0;">
                One row per <b>employee</b>, sorted by state. Each row carries the state-level
                total (repeats across all rows for that state) and a blank <code>Amendment Title</code>
                column — fill that in Excel for each state, then upload to the State Amendments tool.
                Federal and local taxes are excluded from the state total.
            </div>
            """, unsafe_allow_html=True)

            _st_name_by_mid   = st.session_state.get("lag_name_by_mid", {})
            _st_detail_by_mid = {d["mid"]: d for d in st.session_state.get("lag_detail", [])}

            def _with_m_prefix(mid_str):
                """Ensure the MID has a leading uppercase 'M'."""
                s = str(mid_str).strip()
                if not s:
                    return s
                if s[0] in ("M", "m"):
                    return "M" + s[1:]
                return "M" + s

            # Aggregate per-state: list of (mid, name) + summed state tax
            _state_summary = {}
            for _r in _viz_results:
                _mid_raw = str(_r.get("MID", "")).strip()
                _mid     = _with_m_prefix(_mid_raw)
                _state   = _r.get("State", "") or "Unknown"
                _name    = _st_name_by_mid.get(_mid_raw, "")
                _d       = _st_detail_by_mid.get(_mid_raw)
                if not _d:
                    continue
                _res      = _d["result"]
                _er_rates = _d["er_rates"]
                _g        = float(_r.get("Gross Pay", 0))

                _bucket = _state_summary.setdefault(_state, {"employees": [], "total": 0.0})
                _bucket["employees"].append((_mid, _name))

                # Only taxes whose name starts with this state qualify —
                # excludes Federal AND any local/city taxes (e.g. "Denver, …")
                _state_prefix = f"{_state} "
                for _it in _res.get("custom_items", []):
                    _nm, _cd, _rt, _tx, _am, _ytd = _it
                    if str(_nm).startswith(_state_prefix):
                        _bucket["total"] += float(_am)
                for _nm, _cd, _rt, _lr, _ytd in _er_rates:
                    if str(_nm).startswith(_state_prefix):
                        _txable = min(_g, _lr) if _lr is not None else _g
                        _bucket["total"] += round(_txable * _rt / 100, 2)

            # Build CSV rows — one row per employee. State / Total State Tax /
            # Amendment Title repeat across rows for the same state. Amendment
            # Title is left blank; user fills it in Excel before upload.
            _state_rows      = []
            _total_employees = 0
            for _state in sorted(_state_summary.keys()):
                _data        = _state_summary[_state]
                _sorted_emps = sorted(_data["employees"])   # sort by (mid, name)
                _state_total = round(_data["total"], 2)
                _total_employees += len(_sorted_emps)
                for _mid, _nm in _sorted_emps:
                    _state_rows.append({
                        "State":           _state,
                        "Employee Name":   _nm,
                        "MID":             _mid,
                        "Total State Tax": _state_total,
                        "Amendment Title": "",   # user fills this in Excel
                    })

            if _state_rows:
                _st_cols = ["State", "Employee Name", "MID",
                            "Total State Tax", "Amendment Title"]
                _st_buf  = io.StringIO()
                _st_w    = csv.DictWriter(_st_buf, fieldnames=_st_cols,
                                          quoting=csv.QUOTE_MINIMAL)
                _st_w.writeheader()
                _st_w.writerows(_state_rows)

                _st_cid       = st.session_state.get("lag_cid", "").strip() or "Report"
                _st_state_cnt = len(_state_summary)
                _st_grand     = sum(round(v["total"], 2) for v in _state_summary.values())
                st.download_button(
                    label=f"⬇  Download State Tax CSV  "
                          f"({_total_employees} row(s) · {_st_state_cnt} state(s) · "
                          f"{fmt(_st_grand)} total)",
                    data=_st_buf.getvalue(),
                    file_name=f"{_st_cid} State Tax Summary.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="lag_download_state_tax_csv",
                )
            else:
                st.caption("No employees in the current results — nothing to export.")

            # ---- Client Report (PDF) ----
            render_section_divider("viz", "📄 CLIENT REPORT · PDF", "#06ffa5")

            st.markdown("""
            <div style="color:#8a9bb0; font-size:0.85rem; line-height:1.6; margin:6px 0 14px 0;">
                A polished, client-facing PDF with per-employee breakdowns and plain-English
                explanations of every withholding adjustment. Tax codes are omitted — only
                human descriptions are shown. Click <b>Build</b> to render the PDF, then
                <b>Download</b> to save it.
            </div>
            """, unsafe_allow_html=True)

            # Invalidate any cached PDF when the underlying results change, so
            # a new Generate Results run forces a rebuild before download.
            _client_report_sig = (
                len(_viz_results),
                round(sum(float(r.get("Gross Pay", 0))          for r in _viz_results), 2),
                round(sum(float(r.get("Net Pay", 0))            for r in _viz_results), 2),
                round(sum(float(r.get("Total Employee Tax", 0)) for r in _viz_results), 2),
            )
            if st.session_state.get("_lag_client_pdf_sig") != _client_report_sig:
                st.session_state.pop("_lag_client_pdf",       None)
                st.session_state.pop("_lag_client_pdf_name", None)
                st.session_state._lag_client_pdf_sig = _client_report_sig

            if st.button("📄  Build Client Report (PDF)",
                         type="primary", use_container_width=True,
                         key="lag_build_client_report_pdf"):
                with st.spinner("Rendering PDF — this takes a few seconds on first run…"):
                    try:
                        _report_cid         = st.session_state.get("lag_cid", "").strip() or "Report"
                        _report_adjdate_obj = adj_date   # from Settings tab scope
                        _report_adjdate     = (_report_adjdate_obj.strftime("%B %d, %Y")
                                               if hasattr(_report_adjdate_obj, "strftime") else "")
                        _report_year        = st.session_state.get("lag_year", "")
                        _report_include_futa = st.session_state.get("lag_include_futa", "Yes") == "Yes"

                        _report_html = _build_client_report_html(
                            results=_viz_results,
                            detail_list=st.session_state.get("lag_detail", []),
                            name_by_mid=st.session_state.get("lag_name_by_mid", {}),
                            cid=_report_cid,
                            adj_date=_report_adjdate,
                            year=_report_year,
                            include_futa=_report_include_futa,
                        )
                        _pdf_bytes = _html_to_pdf_bytes(_report_html)
                        st.session_state._lag_client_pdf      = _pdf_bytes
                        st.session_state._lag_client_pdf_name = f"{_report_cid} W2C Report.pdf"
                        st.rerun()
                    except Exception as _pdf_err:
                        st.error(f"PDF generation failed: {_pdf_err}")

            if "_lag_client_pdf" in st.session_state:
                st.download_button(
                    label="⬇  Download Client Report (PDF)",
                    data=st.session_state._lag_client_pdf,
                    file_name=st.session_state.get("_lag_client_pdf_name", "W2C Report.pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                    key="lag_download_client_report_pdf",
                )


# ---------------------------------------------------------------------------
# Results tab
# ---------------------------------------------------------------------------
with tab_results:
    run_all = st.button("Generate Results", type="primary", use_container_width=True, key="lag_run")

    render_section_divider("lag", "RESULTS", "#06ffa5")

    _pay_label = "Desired Net Pay" if mode == "Gross Up" else "Gross Pay"

    emp_df = parse_pasted_table(raw_table, ["mid", "pay_amount", "state"])
    
    if not run_all and "lag_results" not in st.session_state:
        st.info("Configure settings, paste employee data, and click **Generate Results**.")
    elif run_all or "lag_results" in st.session_state:
        if run_all:
            if emp_df is None or emp_df.empty:
                st.warning("No valid employee data found. Check the pasted table format.")
                st.stop()
    
            rows   = []
            detail = []
            errors = []
            _ytd_lookup          = st.session_state.get("lag_ytd_lookup", {})
            _shared_cid          = st.session_state.get("lag_cid", "")
            _notes_joined        = " ".join(st.session_state.lag_notes.splitlines()).strip()
            _adj_date_str        = adj_date.strftime("%m/%d/%Y")
            _tax_withheld_by_mid = st.session_state.get("lag_tax_withheld_by_mid", {})
    
            # Aggregate employee rows by MID — duplicate MIDs get their pay amounts summed;
            # the first-seen state is kept (state shouldn't change between rows for the same MID).
            # State is normalized: abbreviations like "CA" are expanded to full names ("California")
            # so downstream views (dashboard map, per-state aggregates) can match on full name.
            _emp_by_mid = {}
            for _, row in emp_df.iterrows():
                _m = str(row["mid"]).strip()
                if not _m:
                    continue
                _st_raw = str(row.get("state", "")).strip()
                _st     = STATE_ABBREV.get(_st_raw.upper(), _st_raw) if _st_raw else _st_raw
                try:
                    _pay = float(str(row["pay_amount"]).replace(",", "").replace("$", ""))
                except ValueError:
                    errors.append(f"Row {_m}: could not parse amount.")
                    continue
                if _m in _emp_by_mid:
                    _emp_by_mid[_m]["pay_amount"] += _pay
                else:
                    _emp_by_mid[_m] = {"state": _st, "pay_amount": _pay}
    
            for mid, _emp_data in _emp_by_mid.items():
                emp_state  = _emp_data["state"]
                pay_amount = _emp_data["pay_amount"]
    
                ytd_med = _ytd_lookup.get(mid, 0.0)
                if mid not in _ytd_lookup:
                    errors.append(f"MID {mid}: not found in Data Dump — using $0.00 YTD Medicare wages.")
    
                ytd_ss = ytd_med
    
                # Build per-employee rates
                _safe_mid         = "".join(c if c.isalnum() else "_" for c in mid)
                combined_ee_rates = _build_rates(st.session_state.get(f"lag_pe_{_safe_mid}_ee_taxes", []))
                combined_er_rates = _build_rates(st.session_state.get(f"lag_pe_{_safe_mid}_er_taxes", []))
    
                if mode == "Gross Up":
                    gross, result = gross_up(pay_amount, ytd_ss, ytd_med, ss_wage_base, combined_ee_rates)
                else:
                    gross  = pay_amount
                    result = calc_taxes(gross, ytd_ss, ytd_med, ss_wage_base, combined_ee_rates)
    
                # FUTA toggle — when disabled, zero out so downstream views / CSV drop 00-402
                _include_futa_calc = st.session_state.get("lag_include_futa", "Yes") == "Yes"
                if not _include_futa_calc:
                    result["futa_amount"]  = 0.0
                    result["futa_taxable"] = 0.0
    
                # Custom Data override — 70/30 split: 70% to Federal (00-400), 30% to State (-450)
                _target_withheld = _tax_withheld_by_mid.get(mid)
                _adjustment_info = None
                if _target_withheld is not None:
                    _calc_before = float(result["total_tax"])
                    _diff        = round(float(_target_withheld) - _calc_before, 2)
                    if _diff != 0:
                        _new_items = list(result["custom_items"])
                        _fed_share   = round(_diff * 0.70, 2)
                        _state_share = round(_diff - _fed_share, 2)

                        # Find state -450 index and federal 00-400 index
                        _state_idx = None
                        _fed_idx   = None
                        for _i, _it in enumerate(_new_items):
                            _nm, _cd, _rt, _tx, _am, _ytd = _it
                            if _cd and _cd.endswith("-450") and _state_idx is None:
                                _state_idx = _i
                            if _cd == "00-400" and _fed_idx is None:
                                _fed_idx = _i

                        _applied_details = []

                        # Apply 30% to state -450 (if exists)
                        if _state_idx is not None and _state_share != 0:
                            _nm, _cd, _rt, _tx, _am, _ytd = _new_items[_state_idx]
                            _new_amt = round(_am + _state_share, 2)
                            _new_items[_state_idx] = (_nm, _cd, _rt, _tx, _new_amt, _ytd)
                            _applied_details.append({"location": "state_450", "tax_name": _nm, "tax_code": _cd,
                                                     "prev_amount": float(_am), "new_amount": _new_amt, "share": _state_share})
                        elif _state_idx is None:
                            _fed_share = _diff

                        # Apply 70% (or full diff if no state) to federal 00-400
                        if _fed_idx is not None:
                            _nm, _cd, _rt, _tx, _am, _ytd = _new_items[_fed_idx]
                            _new_amt = round(_am + _fed_share, 2)
                            _new_items[_fed_idx] = (_nm, _cd, _rt, _tx, _new_amt, _ytd)
                            _applied_details.append({"location": "federal_00_400", "tax_name": _nm, "tax_code": _cd,
                                                     "prev_amount": float(_am), "new_amount": _new_amt, "share": _fed_share})
                        else:
                            _new_items.append(
                                ("Federal - Employee Withholding", "00-400", 0.0, gross, round(_fed_share, 2), None)
                            )
                            _applied_details.append({"location": "new_federal_00_400", "tax_name": "Federal - Employee Withholding",
                                                     "tax_code": "00-400", "prev_amount": 0.0, "new_amount": round(_fed_share, 2), "share": _fed_share})

                        result["custom_items"] = _new_items
                        result["total_tax"] = round(
                            result["ss_amount"] + result["med_amount"] + result["add_med_amount"]
                            + sum(_it[4] for _it in _new_items), 2
                        )
                        result["net"] = round(gross - result["total_tax"], 2)
                        _primary = _applied_details[0] if _applied_details else {}
                        _adjustment_info = {
                            "applied":          True,
                            "calculated_total": _calc_before,
                            "target_withheld":  float(_target_withheld),
                            "diff":             _diff,
                            "split":            _applied_details,
                            **_primary,
                        }
                    else:
                        _adjustment_info = {
                            "applied":          False,
                            "calculated_total": _calc_before,
                            "target_withheld":  float(_target_withheld),
                            "diff":             0.0,
                        }
    
                er_total = 0.0
                for name, code, rate, limit_room, ytd_display in combined_er_rates:
                    taxable   = min(gross, limit_room) if limit_room is not None else gross
                    er_total += round(taxable * rate / 100, 2)
    
                custom_ee_total = sum(item[4] for item in result["custom_items"])
    
                out_row = {
                    "MID":                    mid,
                    "CID":                    _shared_cid,
                    "State":                  emp_state,
                    "Gross Pay":              gross,
                    "Net Pay":                result["net"],
                    "YTD Medicare Wages":     ytd_med,
                    "SS Employee":            result["ss_amount"],
                    "Medicare Employee":      result["med_amount"],
                    "Add. Medicare Employee": result["add_med_amount"],
                    "FUTA":                   result["futa_amount"],
                    "Additional EE Taxes":    custom_ee_total,
                    "Total Employee Tax":     result["total_tax"],
                    "Employer Taxes":         er_total,
                    "Adj Date":               adj_date.strftime("%m/%d/%Y"),
                    "Notes":                  st.session_state.lag_notes,
                    "Tax Year":               year,
                }
                rows.append(out_row)
    
                detail.append({
                    "mid":        mid,
                    "cid":        _shared_cid,
                    "gross":      gross,
                    "result":     result,
                    "er_rates":   combined_er_rates,
                    "notes":      _notes_joined,
                    "adj_date":   _adj_date_str,
                    "adjustment": _adjustment_info,
                })
    
            if errors:
                for e in errors:
                    st.warning(e)
    
            st.session_state.lag_results = rows
            st.session_state.lag_detail  = detail
    
        rows = st.session_state.get("lag_results", [])
        if not rows:
            st.info("No results to display.")
        else:
            results_df = pd.DataFrame(rows)
    
            # Summary metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Employees", len(results_df))
            m2.metric("Total Gross", fmt(results_df["Gross Pay"].sum()))
            m3.metric("Total Net",   fmt(results_df["Net Pay"].sum()))
            m4.metric("Total EE Tax", fmt(results_df["Total Employee Tax"].sum()))
    
            st.divider()
    
            # Display table with currency formatting
            display_df = results_df.copy()
            for col in ["Gross Pay", "Net Pay", "YTD Medicare Wages", "SS Employee", "Medicare Employee",
                        "Add. Medicare Employee", "FUTA", "Additional EE Taxes",
                        "Total Employee Tax", "Employer Taxes"]:
                display_df[col] = display_df[col].apply(lambda x: fmt(float(x)))
    
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
            st.divider()
    
            # Per-employee breakdown expanders
            with st.expander("Per-Employee Breakdown"):
                for row in rows:
                    st.markdown(f"**{row['MID']}** ({row['State']}) — Gross: {fmt(row['Gross Pay'])} | Net: {fmt(row['Net Pay'])} | YTD Med: {fmt(row['YTD Medicare Wages'])}")
                    cols = st.columns(4)
                    cols[0].metric("SS", fmt(row["SS Employee"]))
                    cols[1].metric("Medicare", fmt(row["Medicare Employee"]))
                    cols[2].metric("Add. Medicare", fmt(row["Add. Medicare Employee"]))
                    cols[3].metric("FUTA", fmt(row["FUTA"]))
                    st.divider()
    
            # CSV Export — per-tax rows in adjustment format (matches Gross Up Calculator)
            render_section_divider("lag", "CSV EXPORT", "#2563eb")
    
            _csv_cols = [
                "account_type", "entry_type", "adjustment_date", "amount",
                "cid", "tax_code", "member_id", "taxable_amount", "subj_gross",
                "adjusted_gross", "adjusted_supl_gross", "gross_earnings_amount",
                "reference_type", "reference_id", "notes",
            ]
    
            def _fmt_num(v):
                return round(v, 2) if isinstance(v, (int, float)) else v
    
            csv_rows   = []
            csv_groups = []   # one entry per employee: {"mid", "debit", "rows"} — used for Split CSV
            for d in st.session_state.get("lag_detail", []):
                _g        = d["gross"]
                _res      = d["result"]
                _er       = d["er_rates"]
                _mid_out  = d["mid"].lstrip("M").lstrip("m")
                _cid_out  = d["cid"].lstrip("C").lstrip("c")
                _notes_out = d["notes"]
                _date_out  = d["adj_date"]
    
                def _mk_row(account_type, entry_type, amount, tax_code, member_id,
                            taxable, subj_gross, adj_gross, adj_supl, gross_earnings,
                            ref_type, ref_id,
                            _date_out=_date_out, _cid_out=_cid_out, _notes_out=_notes_out):
                    return {
                        "account_type": account_type, "entry_type": entry_type,
                        "adjustment_date": _date_out, "amount": _fmt_num(amount),
                        "cid": _cid_out, "tax_code": tax_code, "member_id": member_id,
                        "taxable_amount": _fmt_num(taxable), "subj_gross": _fmt_num(subj_gross),
                        "adjusted_gross": _fmt_num(adj_gross), "adjusted_supl_gross": _fmt_num(adj_supl),
                        "gross_earnings_amount": _fmt_num(gross_earnings),
                        "reference_type": ref_type, "reference_id": ref_id, "notes": _notes_out,
                    }
    
                def _cr(tax_code, amount, taxable, gross_earnings=0.0,
                        _g=_g, _mid_out=_mid_out):
                    return _mk_row("Clearing", "Credit", amount, tax_code, _mid_out,
                                   taxable, _g, taxable, 0.0, gross_earnings, "x", 1)
    
                _emp_rows = []
    
                # Federal Withholding (00-400) — always included
                _fed_item = next((it for it in _res.get("custom_items", []) if it[0] == "Federal - Employee Withholding"), None)
                _fed_amt  = 0.0
                if _fed_item:
                    _fed_amt = _fed_item[4] if len(_fed_item) >= 6 else _fed_item[3]
                _emp_rows.append(_cr("00-400", _fed_amt, _g))
    
                # SS Employee / Employer (00-403 / 00-404)
                _emp_rows.append(_cr("00-403", _res.get("ss_amount", 0), _res.get("ss_taxable", 0)))
                _emp_rows.append(_cr("00-404", _res.get("ss_amount", 0), _res.get("ss_taxable", 0)))
    
                # Medicare Employee (00-406)
                _emp_rows.append(_cr("00-406", _res.get("med_amount", 0), _g))
    
                # Additional Medicare (00-901) — only when taxable > 0
                if _res.get("add_med_taxable", 0) > 0:
                    _emp_rows.append(_cr("00-901", _res["add_med_amount"], _res["add_med_taxable"]))
    
                # Medicare Employer (00-407)
                _emp_rows.append(_cr("00-407", _res.get("med_amount", 0), _g))
    
                # FUTA (00-402) — skipped entirely when the FUTA toggle is No;
                # otherwise, when fully over wage base, use gross_earnings_amount
                _include_futa_csv = st.session_state.get("lag_include_futa", "Yes") == "Yes"
                if _include_futa_csv:
                    _futa_taxable = _res.get("futa_taxable", 0)
                    _futa_amount  = _res.get("futa_amount", 0)
                    if _futa_taxable == 0:
                        _emp_rows.append(_cr("00-402", _futa_amount, 0, gross_earnings=_g))
                    else:
                        _emp_rows.append(_cr("00-402", _futa_amount, _futa_taxable))
    
                # Employee custom taxes (excluding Federal Withholding, already emitted)
                for item in _res.get("custom_items", []):
                    if item[0] == "Federal - Employee Withholding":
                        continue
                    _code    = item[1] if len(item) >= 6 else DESC_TO_CODE.get(item[0], "")
                    _taxable = item[3] if len(item) >= 6 else item[2]
                    _amt     = item[4] if len(item) >= 6 else (item[3] if len(item) >= 4 else item[2])
                    _emp_rows.append(_cr(_code, _amt, _taxable))
    
                # Employer custom taxes
                for _name, _code, _rate, _limit_room, _ytd_display in _er:
                    _taxable = min(_g, _limit_room) if _limit_room is not None else _g
                    _amt     = round(_taxable * _rate / 100, 2)
                    _emp_rows.append(_cr(_code, _amt, _taxable))
    
                # Per-employee clearing total — used for partitioning and the final debit roll-up.
                # The Company/Debit line itself is now a single consolidated row at the end of each CSV.
                _clearing_total = round(sum(r["amount"] for r in _emp_rows), 2)
    
                csv_rows.extend(_emp_rows)
                csv_groups.append({"mid": d["mid"], "debit": _clearing_total, "rows": list(_emp_rows)})
    
            if csv_rows:
                _split_mode = st.session_state.get("lag_split_csv", "No") == "Yes"
                _cid_base   = st.session_state.get("lag_cid", "").strip()
    
                def _make_debit_row(clearing_rows):
                    """Single consolidated Company/Debit row summing every Clearing/Credit amount in the CSV."""
                    _amounts = [r.get("amount", 0) for r in clearing_rows]
                    _sum     = round(sum(a for a in _amounts if isinstance(a, (int, float))), 2)
                    _first   = clearing_rows[0] if clearing_rows else {}
                    return {
                        "account_type":          "Company",
                        "entry_type":            "Debit",
                        "adjustment_date":       _first.get("adjustment_date", ""),
                        "amount":                _sum,
                        "cid":                   _first.get("cid", ""),
                        "tax_code":              "",
                        "member_id":             "",
                        "taxable_amount":        "",
                        "subj_gross":            "",
                        "adjusted_gross":        "",
                        "adjusted_supl_gross":   "",
                        "gross_earnings_amount": "",
                        "reference_type":        "",
                        "reference_id":          "",
                        "notes":                 _first.get("notes", ""),
                    }
    
                if _split_mode:
                    # Partition employees so each CSV's total company debit stays under $10,000
                    SPLIT_LIMIT = 10000.0
                    partitions  = []
                    _cur_rows, _cur_sum = [], 0.0
                    for _g in csv_groups:
                        if _cur_rows and (_cur_sum + _g["debit"]) >= SPLIT_LIMIT:
                            partitions.append({"rows": _cur_rows, "sum": _cur_sum})
                            _cur_rows, _cur_sum = [], 0.0
                        _cur_rows.extend(_g["rows"])
                        _cur_sum += _g["debit"]
                    if _cur_rows:
                        partitions.append({"rows": _cur_rows, "sum": _cur_sum})
    
                    st.caption(
                        f"Split into **{len(partitions)}** CSV(s), each capped under $10,000 in company debit."
                    )
    
                    for _i, _part in enumerate(partitions, start=1):
                        _part_rows = _part["rows"] + [_make_debit_row(_part["rows"])]
    
                        st.markdown(
                            f"**Part {_i} · Company Debit Total: {fmt(_part['sum'])}**"
                        )
                        st.dataframe(
                            pd.DataFrame(_part_rows, columns=_csv_cols),
                            use_container_width=True, hide_index=True,
                        )
    
                        _buf = io.StringIO()
                        _w   = csv.DictWriter(_buf, fieldnames=_csv_cols)
                        _w.writeheader()
                        _w.writerows(_part_rows)
    
                        st.download_button(
                            label=f"Download CSV · Part {_i}",
                            data=_buf.getvalue(),
                            file_name=f"{_cid_base} PTU Part {_i}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"lag_download_csv_part_{_i}",
                        )
                else:
                    csv_rows_with_debit = csv_rows + [_make_debit_row(csv_rows)]
    
                    st.dataframe(pd.DataFrame(csv_rows_with_debit, columns=_csv_cols),
                                 use_container_width=True, hide_index=True)
    
                    csv_buf = io.StringIO()
                    csv_writer = csv.DictWriter(csv_buf, fieldnames=_csv_cols)
                    csv_writer.writeheader()
                    csv_writer.writerows(csv_rows_with_debit)
    
                    filename = f"{_cid_base} PTU.csv"
                    st.download_button(
                        label="Download CSV",
                        data=csv_buf.getvalue(),
                        file_name=filename,
                        mime="text/csv",
                        use_container_width=True,
                        key="lag_download_csv",
                    )
