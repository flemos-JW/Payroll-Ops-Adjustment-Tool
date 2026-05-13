"""
Generate a professional PDF user guide for the Large Adjustment Generator tool.
Uses Playwright for screenshots and fpdf2 for PDF assembly.

Usage: python3 generate_lag_guide.py
Output: LAG_User_Guide.pdf
"""

import os
import time
import tempfile
from pathlib import Path
from fpdf import FPDF
from playwright.sync_api import sync_playwright

TOOL_URL = "http://localhost:8505"
PASSWORD = "PayOps2026"
OUTPUT_PDF = Path(__file__).parent / "LAG_User_Guide.pdf"
SCREENSHOT_DIR = Path(tempfile.mkdtemp(prefix="lag_guide_"))

TAB_NAMES = [
    "Settings",
    "Employee Data",
    "Data Dump",
    "Additional Taxes",
    "Custom Data",
    "Results",
    "Dashboard",
]


def capture_screenshots():
    """Capture screenshots of each tab using Playwright."""
    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(TOOL_URL, wait_until="networkidle")
        time.sleep(3)

        # Authenticate
        pw_input = page.locator('input[type="password"]')
        if pw_input.count() > 0:
            pw_input.first.fill(PASSWORD)
            sign_in = page.locator('button:has-text("Sign In")')
            if sign_in.count() > 0:
                sign_in.first.click()
            else:
                page.keyboard.press("Enter")
            time.sleep(5)
            page.wait_for_load_state("networkidle")
            time.sleep(3)

        # Full page screenshot (landing)
        landing = SCREENSHOT_DIR / "00_landing.png"
        page.screenshot(path=str(landing), full_page=False)
        shots["landing"] = str(landing)

        # Click each tab and screenshot
        for i, tab_name in enumerate(TAB_NAMES):
            try:
                tab_btn = page.locator(f'button[role="tab"]:has-text("{tab_name}")')
                if tab_btn.count() > 0:
                    tab_btn.first.click()
                    time.sleep(2)
                    path = SCREENSHOT_DIR / f"{i+1:02d}_{tab_name.lower().replace(' ', '_')}.png"
                    page.screenshot(path=str(path), full_page=False)
                    shots[tab_name] = str(path)
            except Exception as e:
                print(f"  Warning: Could not capture {tab_name}: {e}")

        browser.close()
    return shots


class GuidePDF(FPDF):
    """Custom PDF with headers/footers for the guide."""

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, "Large Adjustment Generator - User Guide", align="L")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(10, 14, 39)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 229, 255)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 40, 80)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, text)
        self.ln(3)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, f"  -  {text}")
        self.ln(1)

    def add_screenshot(self, path, caption=""):
        if not os.path.exists(path):
            return
        available_h = 297 - self.get_y() - 25
        img_w = 180
        img_h = 100
        if img_h > available_h:
            self.add_page()
        x = (210 - img_w) / 2
        self.image(path, x=x, w=img_w)
        if caption:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, caption, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)


def build_pdf(shots):
    """Assemble the PDF guide."""
    pdf = GuidePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Cover Page ---
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "Large Adjustment Generator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 2.1 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "landing" in shots:
        pdf.add_screenshot(shots["landing"])

    # --- Content (continuous flow) ---
    pdf.add_page()
    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The Large Adjustment Generator (LAG) is an enterprise payroll tax calculation "
        "and reporting tool built for the Payroll Operations team. It computes federal, "
        "state, and local tax adjustments for one or more employees, supports gross-up "
        "calculations, and generates compliance-ready CSV exports for upload to the "
        "payroll system."
    )
    pdf.ln(2)
    pdf.section_title("Key Capabilities")
    capabilities = [
        "Calculate federal taxes: Social Security (6.2%), Medicare (1.45%), Additional Medicare (0.9%), FUTA (0.6%)",
        "Calculate state withholding and employer unemployment (SUI) for all 50 states + DC, PR, VI",
        "Supplemental state withholding rates (year-aware, auto-applied to -450 codes)",
        "Gross-up mode: solve for the gross pay that yields a specific net amount",
        "YTD wage base tracking to correctly cap Social Security and SUI contributions",
        "Custom tax reconciliation with 70/30 split (70% federal, 30% state)",
        "Split CSV mode: partition exports so each file stays under $10,000 employer debit",
        "Interactive dashboard with geographic heatmap, tax composition charts, and drill-down",
        "Client-facing PDF report generation with plain-English tax explanations",
        "Batch processing for multiple employees across multiple states simultaneously",
    ]
    for cap in capabilities:
        pdf.bullet(cap)

    pdf.ln(4)
    pdf.section_title("Supported Modes")
    pdf.body_text(
        "Net Pay Mode: You enter the gross pay amount. The tool calculates all taxes and "
        "reports the resulting net pay.\n\n"
        "Gross Up Mode: You enter the desired net pay amount. The tool uses binary search "
        "to find the gross pay that, after all taxes are deducted, yields exactly that net amount."
    )

    pdf.chapter_title("2. Getting Started")
    pdf.section_title("Accessing the Tool")
    pdf.body_text(
        "The Large Adjustment Generator runs on port 8505. Navigate to "
        "http://localhost:8505 in your browser."
    )
    pdf.section_title("Authentication")
    pdf.body_text(
        "Enter the team password when prompted. The password is shared among "
        "the Payroll Operations team. After authentication, you will see the "
        "main interface with 7 tabs."
    )
    pdf.section_title("Recommended Workflow")
    steps = [
        "1. Configure settings (tax year, mode, employer taxes, toggles)",
        "2. Upload YTD Medicare wages via Data Dump tab (optional but recommended)",
        "3. Add any additional/custom taxes via Additional Taxes tab (optional)",
        "4. Paste employee data (MID, Amount, State) in Employee Data tab",
        "5. Upload actual tax withheld via Custom Data tab (optional, for reconciliation)",
        "6. Review/adjust per-employee tax rates in Settings tab",
        "7. Generate results in the Results tab",
        "8. Download CSV export from Results tab",
        "9. Review dashboard analytics and generate client PDF (Dashboard tab)",
    ]
    for step in steps:
        pdf.body_text(step)

    pdf.chapter_title("3. Settings Tab")
    if "Settings" in shots:
        pdf.add_screenshot(shots["Settings"], "Settings tab - main configuration panel")
    pdf.section_title("Core Settings")
    settings_items = [
        ("Tax Year", "Select 2023-2026. Determines Social Security wage base: 2023=$160,200 | 2024=$168,600 | 2025=$176,100 | 2026=$184,500"),
        ("Mode", "\"Net Pay\" (input is gross) or \"Gross Up\" (input is desired net pay)"),
        ("Employer Taxes", "Yes/No. When Yes, includes employer SS, Medicare, FUTA, and SUI in calculations and CSV"),
        ("Supplemental Rates", "When Yes, auto-applies state-specific supplemental withholding rates to -450 tax codes"),
        ("Split CSV", "When Yes, partitions CSV exports so each file's employer debit stays under $10,000"),
        ("Only Income Taxes", "When Yes, filters employee taxes to state withholding codes (-450) only. California always included regardless"),
        ("FUTA", "Yes/No. Controls whether FUTA (code 00-402) appears in calculations and CSV export"),
        ("Adjustment Date", "Date stamp for the CSV. Defaults to next Friday"),
        ("CID", "Company identifier included in all CSV rows"),
        ("Notes", "Free-form text included in CSV reference field"),
    ]
    for name, desc in settings_items:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, desc)
        pdf.ln(2)

    pdf.section_title("Per-Employee Tax Configuration")
    pdf.body_text(
        "After entering employee data, each employee gets an expandable section in the "
        "Settings tab. This section shows:\n\n"
        "Employee Withholdings: State-specific taxes auto-populated based on the employee's "
        "state. Supplemental rates are auto-applied when the toggle is on. You can adjust "
        "rates, add new tax rows, or remove rows.\n\n"
        "Employer Contributions: Corresponding employer taxes (SUI, etc.) with wage base "
        "limits auto-calculated from the SUI_WAGE_BASES table for the selected year.\n\n"
        "Tax rows auto-refresh when you change: state, year, employer tax toggle, "
        "supplemental rates toggle, income-only filter, or additional taxes."
    )

    pdf.chapter_title("4. Employee Data Tab")
    if "Employee Data" in shots:
        pdf.add_screenshot(shots["Employee Data"], "Employee Data tab - paste employee information")
    pdf.section_title("Input Format")
    pdf.body_text(
        "Paste a tab-separated or comma-separated table with 3 columns:\n\n"
        "MID | Amount | State\n\n"
        "Example:\n"
        "M12345    5000.00    California\n"
        "M67890    3200.00    NY\n"
        "M11111    8500.00    TX"
    )
    pdf.section_title("Automatic Processing")
    processing_items = [
        "State abbreviations automatically expanded (NY -> New York, CA -> California, etc.)",
        "Duplicate MIDs are aggregated: amounts are summed, first-seen state is retained",
        "Currency formatting ($, commas) handled automatically",
        "Tab or comma separators both accepted",
    ]
    for item in processing_items:
        pdf.bullet(item)

    pdf.chapter_title("5. Data Dump Tab (YTD Medicare Wages)")
    if "Data Dump" in shots:
        pdf.add_screenshot(shots["Data Dump"], "Data Dump tab - upload YTD wage data")
    pdf.body_text(
        "Upload a CSV file containing year-to-date Medicare wages for employees. "
        "This data is critical for correctly capping Social Security contributions "
        "when an employee is near or above the annual wage base."
    )
    pdf.section_title("Required CSV Format")
    pdf.body_text(
        "The CSV must contain these columns:\n"
        "- MEMBER_ID: Employee identifier (matched to MID)\n"
        "- TOTAL_GROSS_AMOUNT: Year-to-date gross wages\n\n"
        "Additional columns are ignored. Duplicate MIDs are summed. "
        "Currency formatting ($, commas) is handled automatically."
    )
    pdf.section_title("Why This Matters")
    pdf.body_text(
        "Without YTD data, the tool assumes $0 year-to-date wages. This means "
        "Social Security tax will be calculated on the full adjustment amount even "
        "if the employee has already exceeded the annual wage base ($184,500 for 2026). "
        "Always upload YTD data for accurate results."
    )

    pdf.chapter_title("6. Additional Taxes Tab")
    if "Additional Taxes" in shots:
        pdf.add_screenshot(shots["Additional Taxes"], "Additional Taxes tab - custom per-employee taxes")
    pdf.body_text(
        "Add custom or non-standard taxes that are not in the built-in state/federal "
        "tax library. These are injected into the per-employee tax configuration in "
        "the Settings tab."
    )
    pdf.section_title("Input Format")
    pdf.body_text(
        "Paste a table with 3 columns:\n"
        "MID | Tax Name | Tax Code\n\n"
        "Example:\n"
        "M12345    Aurora OPT    060050030-533\n"
        "M67890    Denver OPT    060310140-533"
    )
    pdf.section_title("Behavior")
    behavior_items = [
        "Taxes appear as additional rows in the Settings tab per-employee section",
        "Duplicate (MID, tax code) pairs are skipped to prevent double-counting",
        "Rate defaults to 0% - you must set the rate in the Settings tab",
        "Common use cases: local occupational privilege taxes, city taxes, special assessments",
    ]
    for item in behavior_items:
        pdf.bullet(item)

    pdf.chapter_title("7. Custom Data Tab (Reconciliation)")
    if "Custom Data" in shots:
        pdf.add_screenshot(shots["Custom Data"], "Custom Data tab - actual withholding & employee names")
    pdf.section_title("Actual Tax Withheld (Reconciliation)")
    pdf.body_text(
        "Enter the actual total tax withheld for employees when you need to reconcile "
        "calculated vs. actual amounts. The tool computes the variance and applies it "
        "using a 70/30 split between federal and state taxes."
    )
    pdf.body_text(
        "Input format (2 columns):\n"
        "MID | Tax Withheld\n\n"
        "70/30 Reconciliation Logic:\n"
        "1. Calculates diff = actual_withheld - calculated_total\n"
        "2. Splits 70% of the variance to Federal Withholding (00-400)\n"
        "3. Splits 30% of the variance to State Withholding (-450 code)\n"
        "4. If no state -450 code exists, 100% goes to Federal (00-400)\n"
        "5. Creates tax lines as needed if they don't already exist"
    )
    pdf.section_title("Employee Names (Optional)")
    pdf.body_text(
        "Paste a table with 3 columns:\n"
        "MID | Last_Name | First_Name\n\n"
        "Names are displayed in Settings tab expanders, dashboard dropdowns, and "
        "client PDF reports. They do not affect calculations or CSV export."
    )

    pdf.chapter_title("8. Results Tab")
    if "Results" in shots:
        pdf.add_screenshot(shots["Results"], "Results tab - generate and export")
    pdf.section_title("Generating Results")
    pdf.body_text(
        "Click the \"Generate Results\" button to run tax calculations for all employees. "
        "The tool validates that employee data is present, then computes all federal, "
        "state, and custom taxes based on your settings."
    )
    pdf.section_title("Results Display")
    results_items = [
        "Summary metrics: employee count, total gross, total net, total employee tax",
        "Per-employee results table with currency formatting",
        "Expandable breakdown per employee: SS, Medicare, Additional Medicare, FUTA details",
    ]
    for item in results_items:
        pdf.bullet(item)
    pdf.section_title("CSV Export")
    pdf.body_text(
        "The CSV export section generates a compliance-ready file for payroll system upload."
    )
    csv_items = [
        "One Clearing/Credit row per tax per employee (employee and employer taxes)",
        "One consolidated Company/Debit row summing all credits",
        "15 columns: account_type, entry_type, adjustment_date, amount, cid, tax_code, member_id, taxable_amount, subj_gross, adjusted_gross, adjusted_supl_gross, gross_earnings_amount, reference_type, reference_id, notes",
        "BOM included for Excel compatibility",
        "Split CSV mode: multiple files, each under $10,000 employer debit",
    ]
    for item in csv_items:
        pdf.bullet(item)

    pdf.chapter_title("9. Dashboard Tab")
    if "Dashboard" in shots:
        pdf.add_screenshot(shots["Dashboard"], "Dashboard tab - interactive analytics")
    pdf.section_title("KPI Row")
    pdf.body_text(
        "Top-level metrics at a glance:\n"
        "- Employees: count + number of states\n"
        "- Total Gross: total payroll outflow\n"
        "- Total Net: net pay + effective withholding rate\n"
        "- Employer Cost: SS + Medicare + FUTA + other employer taxes\n"
        "- Total Debit: combined employee + employer tax amount"
    )
    pdf.section_title("Employee Deep Dive")
    pdf.body_text(
        "Select an employee from the dropdown (or click a bar in the chart) to see:\n"
        "- Individual KPI cards (gross, net, EE tax, ER cost, total debit)\n"
        "- Tax line items table (all employee + employer taxes with rates and amounts)\n"
        "- Withholding adjustment explainer (if Custom Data reconciliation was applied)\n"
        "- Tax composition pie/donut charts"
    )
    pdf.section_title("Geographic Heatmap")
    pdf.body_text(
        "US map showing employee distribution by state. Bubble size indicates "
        "employee count. Click to drill into state-specific tax composition."
    )
    pdf.section_title("Client Report PDF")
    pdf.body_text(
        "Generate a professional client-facing PDF with:\n"
        "- Summary metrics (no tax codes - plain English)\n"
        "- Per-employee sections with tax tables\n"
        "- Withholding adjustment explanations\n"
        "- Professional formatting with page breaks"
    )
    pdf.section_title("State Tax Export")
    pdf.body_text(
        "Download a separate CSV aggregating taxes by state for reconciliation purposes. "
        "This export can be fed directly into the State Amendments tool (port 8508)."
    )

    pdf.chapter_title("10. Supplemental Rates")
    pdf.body_text(
        "When the Supplemental Rates toggle is enabled in Settings, the tool "
        "automatically applies state-specific supplemental withholding rates to "
        "the -450 (state income tax) code for each employee. Rates are year-aware "
        "and update when you change the Tax Year."
    )
    pdf.section_title("How It Works")
    pdf.body_text(
        "1. Toggle 'Supplemental Rates' to Yes in the Settings tab.\n"
        "2. The tool looks up the employee's state and selected tax year.\n"
        "3. The appropriate supplemental rate is pre-filled for the -450 code.\n"
        "4. You can still override the rate manually per employee."
    )
    pdf.section_title("Special State Handling")
    special_states = [
        ("California", "Default rate: 6.6%. Note: stock option income uses 10.23% - adjust manually if applicable."),
        ("Vermont", "Rate is 30% of federal supplemental (22%), calculated as 6.6%."),
        ("Wisconsin", "Graduated brackets based on gross amount: 3.5% (0-14,320), 4.4% (14,320-28,640), 5.3% (28,640-315,310), 6.53% (315,310-693,860), 7.65% (693,860+)."),
        ("Maryland", "Rate is 0% for 2025 (check manually). Rate is 6.5% for 2026."),
    ]
    for state, desc in special_states:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 5, state, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 4.5, desc)
        pdf.ln(2)
    pdf.section_title("Rate Changes 2025 to 2026")
    pdf.body_text(
        "Several states changed their supplemental withholding rates for 2026. "
        "Key changes include:"
    )
    rate_changes = [
        "Georgia: 5.39% -> 5.19%",
        "Idaho: 5.695% -> 5.3%",
        "Indiana: 3.0% -> 2.95%",
        "Kentucky: 4.0% -> 3.5%",
        "Maryland: 0.0% -> 6.5%",
        "Mississippi: 4.4% -> 4.0%",
        "Nebraska: 5.0% -> 3.5%",
        "North Carolina: 4.35% -> 4.09%",
        "Ohio: 3.5% -> 2.75%",
        "Oklahoma: 4.75% -> 4.5%",
        "South Carolina: 6.2% -> 6.0%",
        "Utah: 4.55% -> 4.5%",
    ]
    for change in rate_changes:
        pdf.bullet(change)

    pdf.chapter_title("11. Calculation Logic")
    pdf.section_title("Social Security (6.2%)")
    pdf.body_text(
        "Rate: 6.2% (employee) + 6.2% (employer)\n"
        "Annual wage base (2026): $184,500\n"
        "Calculation: taxable = min(gross, max(0, wage_base - YTD_SS))\n"
        "Amount = taxable x 6.2%\n\n"
        "If an employee's YTD wages already exceed the wage base, no Social Security "
        "tax is calculated on the adjustment."
    )
    pdf.section_title("Medicare (1.45%)")
    pdf.body_text(
        "Rate: 1.45% (employee) + 1.45% (employer)\n"
        "No wage base cap - applies to all wages.\n"
        "Amount = gross x 1.45%"
    )
    pdf.section_title("Additional Medicare (0.9%)")
    pdf.body_text(
        "Rate: 0.9% (employee only - no employer match)\n"
        "Threshold: $200,000 cumulative annual wages\n"
        "Calculation: Only applies to wages above $200,000 when combining YTD + current gross.\n"
        "Amount = max(0, (YTD + gross) - $200,000) x 0.9% (minus any already-taxed portion)"
    )
    pdf.section_title("FUTA (0.6%)")
    pdf.body_text(
        "Rate: 0.6% (employer only)\n"
        "Wage base: $7,000\n"
        "Calculation: taxable = min(gross, max(0, $7,000 - YTD))\n"
        "Amount = taxable x 0.6%\n\n"
        "Can be toggled off in Settings if not applicable."
    )
    pdf.section_title("70/30 Reconciliation Split")
    pdf.body_text(
        "When Custom Data provides actual tax withheld amounts, the tool reconciles "
        "the variance between calculated and actual using a 70/30 split:\n\n"
        "- 70% of the variance is applied to Federal Income Tax (00-400)\n"
        "- 30% of the variance is applied to State Income Tax (-450 code)\n\n"
        "This ensures the adjustment distributes the withholding difference "
        "proportionally between federal and state obligations. If no state -450 "
        "code exists for the employee, the full 100% goes to federal."
    )
    pdf.section_title("Gross-Up Algorithm")
    pdf.body_text(
        "When Mode = \"Gross Up\", the tool uses binary search to find the gross pay "
        "that produces the desired net:\n\n"
        "1. Search range: [desired_net, desired_net x 10]\n"
        "2. For each midpoint, calculate all taxes and check resulting net\n"
        "3. Converge within $0.001 (up to 300 iterations)\n"
        "4. Result: the gross amount where net = desired amount after all taxes"
    )
    pdf.section_title("State & Custom Taxes")
    pdf.body_text(
        "State taxes use configurable rates set in the per-employee Settings section. "
        "Each tax row specifies: name, code, rate (%), and optional wage base limit.\n\n"
        "If a wage base limit is set (e.g., SUI): taxable = min(gross, remaining_room)\n"
        "Otherwise: taxable = gross\n"
        "Amount = taxable x rate%"
    )

    pdf.chapter_title("12. Appendix")
    pdf.section_title("Federal Tax Codes")
    federal_codes = [
        ("00-400", "Federal Income Tax Withholding"),
        ("00-402", "FUTA (Federal Unemployment)"),
        ("00-403", "Social Security - Employee"),
        ("00-404", "Social Security - Employer"),
        ("00-406", "Medicare - Employee"),
        ("00-407", "Medicare - Employer"),
        ("00-901", "Additional Medicare"),
    ]
    for code, name in federal_codes:
        pdf.set_font("Courier", "", 9)
        pdf.cell(25, 5, code)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, name, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.section_title("State Tax Code Pattern")
    pdf.body_text(
        "XX-450: State income tax withholding (employee)\n"
        "XX-459: State unemployment (employer)\n"
        "XX-461: Employment training tax\n"
        "XX-466: State disability insurance\n"
        "XX-468: Paid family leave\n\n"
        "Where XX is the state number (01=Alabama through 51=Wyoming, plus territories)."
    )

    pdf.ln(4)
    pdf.section_title("Social Security Wage Bases by Year")
    wage_bases = [
        ("2023", "$160,200"),
        ("2024", "$168,600"),
        ("2025", "$176,100"),
        ("2026", "$184,500"),
    ]
    for year, base in wage_bases:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(15, 5, year)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, base, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.section_title("Key SUI Wage Bases (2026)")
    sui_examples = [
        ("California", "$7,000"),
        ("New York", "$17,600"),
        ("Texas", "$9,000"),
        ("Washington", "$78,200"),
        ("Alaska", "$54,200"),
        ("Massachusetts", "$15,000"),
        ("New Jersey", "$44,800"),
        ("Pennsylvania", "$10,000"),
    ]
    for state, base in sui_examples:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(40, 5, state)
        pdf.cell(0, 5, base, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.section_title("Tips & Best Practices")
    tips = [
        "Always upload YTD data before generating results to avoid over-calculating SS tax",
        "Use Gross Up mode when the employee needs to receive an exact net amount",
        "Enable Split CSV for large batches to stay under portal upload limits",
        "Enable Supplemental Rates to auto-fill state withholding percentages",
        "Check the Dashboard's withholding adjustment explainer when using Custom Data",
        "Use the client PDF report for stakeholder communication (no tax codes shown)",
        "Review per-employee tax rates in Settings before generating - auto-populated rates may need adjustment",
        "The State Tax Export CSV can be fed directly into the State Amendments Automator",
    ]
    for tip in tips:
        pdf.bullet(tip)

    # Save
    pdf.output(str(OUTPUT_PDF))
    return str(OUTPUT_PDF)


if __name__ == "__main__":
    print("Capturing screenshots from the Large Adjustment Generator...")
    screenshots = capture_screenshots()
    print(f"  Captured {len(screenshots)} screenshots in {SCREENSHOT_DIR}")

    print("Building PDF guide...")
    output = build_pdf(screenshots)
    print(f"  PDF saved to: {output}")
    print("Done!")
