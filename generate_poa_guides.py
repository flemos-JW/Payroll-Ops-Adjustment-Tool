"""
Generate PDF user guides for the Payroll Ops Adjustment tool (port 8503).
Creates 3 separate guides: Calculator, FICA Refund, FICA Debit.

Usage: python3 generate_poa_guides.py
Output: POA_Calculator_Guide.pdf, POA_FICA_Refund_Guide.pdf, POA_FICA_Debit_Guide.pdf
"""

import os
import time
import tempfile
from pathlib import Path
from fpdf import FPDF
from playwright.sync_api import sync_playwright

TOOL_URL = "http://localhost:8503"
PASSWORD = "PayOps2026"
OUTPUT_DIR = Path(__file__).parent
SCREENSHOT_DIR = Path(tempfile.mkdtemp(prefix="poa_guide_"))


def capture_screenshots():
    """Capture screenshots of each tab using Playwright."""
    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(TOOL_URL, wait_until="networkidle")
        time.sleep(3)

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

        path = SCREENSHOT_DIR / "calculator.png"
        page.screenshot(path=str(path), full_page=False)
        shots["calculator"] = str(path)

        tab_btn = page.locator('button[role="tab"]:has-text("FICA Refund")')
        if tab_btn.count() > 0:
            tab_btn.first.click()
            time.sleep(2)
            path = SCREENSHOT_DIR / "fica_refund.png"
            page.screenshot(path=str(path), full_page=False)
            shots["fica_refund"] = str(path)

        tab_btn = page.locator('button[role="tab"]:has-text("FICA Debit")')
        if tab_btn.count() > 0:
            tab_btn.first.click()
            time.sleep(2)
            path = SCREENSHOT_DIR / "fica_debit.png"
            page.screenshot(path=str(path), full_page=False)
            shots["fica_debit"] = str(path)

        browser.close()
    return shots


class GuidePDF(FPDF):
    def __init__(self, title):
        super().__init__()
        self._guide_title = title

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, f"{self._guide_title} - User Guide", align="L")
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
        if 100 > available_h:
            self.add_page()
        x = (210 - 180) / 2
        self.image(path, x=x, w=180)
        if caption:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, caption, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)


def build_calculator_guide(shots):
    pdf = GuidePDF("POA Calculator")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "Payroll Ops Adjustment", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "Calculator - User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 2.0 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "calculator" in shots:
        pdf.add_screenshot(shots["calculator"])

    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The Calculator tab is the primary tool for computing single-employee payroll "
        "tax adjustments. It supports Net Pay and Gross Up modes, auto-populates "
        "state-specific taxes, generates a compliance-ready CSV export, and produces "
        "a copy-ready CS Tools Summary for ticket resolution."
    )
    pdf.section_title("Key Features")
    for f in [
        "Net Pay mode: enter gross, see taxes and resulting net",
        "Gross Up mode: enter desired net, tool finds the required gross",
        "Auto-populated state taxes when you select a state",
        "SUI wage base auto-applied for employer unemployment taxes",
        "Custom write-in tax rows with manual codes and rates",
        "CSV export with all tax lines (Clearing/Credit + Company/Debit)",
        "CS Tools Summary with clickable link and breakdown table",
        "Three ticket types: MDV, MISC Fully Taxable, and generic",
    ]:
        pdf.bullet(f)

    pdf.chapter_title("2. Input Configuration")
    pdf.section_title("Tax Year & YTD Wages")
    pdf.body_text(
        "Tax Year: Select 2023-2026. Determines SS wage base and SUI wage bases.\n\n"
        "YTD Medicare Wages: Enter the employee's year-to-date wages. Used for:\n"
        "- Social Security cap calculation\n"
        "- Additional Medicare threshold ($200k)\n"
        "- SUI/FUTA wage base remaining room"
    )
    pdf.section_title("Mode & Amount")
    pdf.body_text(
        "Net Pay (enter gross): You provide the gross adjustment amount. The tool "
        "calculates all taxes and shows the resulting net pay.\n\n"
        "Gross Up (enter desired net): You provide the target net amount. The tool "
        "uses binary search to find the gross that yields that exact net."
    )
    pdf.section_title("Additional Tax Rates")
    pdf.body_text(
        "Employee Withholdings: Add state/local taxes from a dropdown of all known "
        "tax descriptions, or use 'Write in custom' for unlisted taxes. Each row has:\n"
        "- Tax Name (dropdown or custom text)\n"
        "- Tax Code (auto-filled from lookup, or manual entry)\n"
        "- Rate (%) - editable\n"
        "- Limit (Yes/No) - when Yes, shows YTD and Limit fields for wage base capping\n\n"
        "Employer Contributions: Same interface for employer-side taxes (SUI, FUTA, etc.). "
        "SUI wage bases auto-populate when you select a state."
    )

    pdf.chapter_title("3. Adjustment Info & Results")
    pdf.section_title("Adjustment Info")
    pdf.body_text(
        "MID: Member ID for the employee.\n"
        "CID: Company ID.\n"
        "Adjustment Date: Defaults to next Friday. Used in CSV export.\n"
        "Ticket Type: MDV, MISC Fully Taxable, or blank (generic).\n"
        "State: Auto-populates employee and employer tax rows.\n"
        "Notes: Free text included in CSV reference field."
    )
    pdf.section_title("Results Panel")
    pdf.body_text(
        "After clicking Calculate:\n"
        "- Breakdown table: Gross -> taxes -> Net Pay\n"
        "- Tax Detail table: every tax line with code, YTD, taxable, amount\n"
        "- Metric cards: Total Tax, Effective Rate, Net Pay\n"
        "- SS wage base callout (when partially or fully capped)"
    )
    pdf.section_title("CSV Export")
    pdf.body_text(
        "Generates a downloadable CSV with:\n"
        "- One Clearing/Credit row per tax (employee + employer)\n"
        "- One Company/Debit row summing all credits\n"
        "- 15 standard columns matching the payroll system format\n"
        "- Filename: {MID} {CID} {TicketType}.csv"
    )

    pdf.chapter_title("4. CS Tools Summary")
    pdf.body_text(
        "After CSV export, a CS Tools Summary section appears. This generates "
        "copy-ready HTML for pasting into CS Tools tickets."
    )
    pdf.section_title("MDV Ticket Type")
    pdf.body_text(
        "Shows:\n"
        "- CS Tools Link input (makes header clickable)\n"
        "- Debit Date input\n"
        "- Summary paragraph: adjustment link, debit amount, debit date, net pay\n"
        "- Breakdown table: Gross -> taxes -> Net\n"
        "- SOP link for refunding benefit deductions\n"
        "- Team page link\n"
        "- Copy Summary to Clipboard button"
    )
    pdf.section_title("MISC Fully Taxable")
    pdf.body_text(
        "Shows:\n"
        "- CS Tools Link input\n"
        "- Debit Date input\n"
        "- Summary: ADJ link header, employer debit amount and date\n"
        "- Breakdown table\n"
        "- Copy Summary to Clipboard button"
    )
    pdf.section_title("Generic (Other Ticket Types)")
    pdf.body_text(
        "Shows:\n"
        "- CS Tools Link input\n"
        "- Debit Date input\n"
        "- Summary: adjustment link, debit amount, debit date\n"
        "- Breakdown table\n"
        "- Copy Summary to Clipboard button"
    )

    pdf.chapter_title("5. Step-by-Step Workflow")
    for step in [
        "1. Select Tax Year (affects wage bases and SUI limits)",
        "2. Enter YTD Medicare Wages if known (for accurate SS capping)",
        "3. Choose Mode: Net Pay or Gross Up",
        "4. Enter the amount (gross or desired net)",
        "5. Fill in MID, CID, Adjustment Date on the right",
        "6. Select Ticket Type and State",
        "7. Review auto-populated tax rows - adjust rates as needed",
        "8. Add any custom taxes via '+ Add Employee/Employer Tax'",
        "9. Click Calculate to see results",
        "10. Download CSV export",
        "11. Fill CS Tools Link and Debit Date",
        "12. Click 'Copy Summary to Clipboard' and paste into CS Tools ticket",
    ]:
        pdf.body_text(step)

    output = OUTPUT_DIR / "POA_Calculator_Guide.pdf"
    pdf.output(str(output))
    return str(output)


def build_fica_refund_guide(shots):
    pdf = GuidePDF("POA FICA Refund")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "Payroll Ops Adjustment", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "FICA Refund - User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 2.0 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "fica_refund" in shots:
        pdf.add_screenshot(shots["fica_refund"])

    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The FICA Refund tab generates CSV exports for refunding over-collected FICA "
        "taxes (Social Security, Medicare, and FUTA) across one or more quarters. "
        "It creates Clearing/Debit rows for each tax type and matching Member/Credit "
        "and Company/Credit rows to refund the employee and reduce the employer liability."
    )
    pdf.section_title("When to Use")
    for u in [
        "Employee was over-withheld for Social Security (exceeded wage base mid-year)",
        "Medicare was over-collected due to payroll error",
        "FUTA was charged beyond the $7,000 wage base",
        "Quarterly corrections needed for prior-period FICA",
    ]:
        pdf.bullet(u)

    pdf.chapter_title("2. Input Fields")
    pdf.section_title("Global Fields")
    pdf.body_text(
        "Member ID: The employee's MID (M-prefix).\n"
        "Company ID: The CID for the company.\n"
        "Tax Year: Determines quarter end dates and wage bases."
    )
    pdf.section_title("Per-Quarter Data")
    pdf.body_text(
        "Each quarter (Q1-Q4) has an expandable section with:\n\n"
        "Social Security:\n"
        "- SS Wages ($): The overstated SS wages for this quarter\n"
        "- SS Tax ($): Auto-calculated at 6.2%, editable\n\n"
        "Medicare:\n"
        "- Medicare Wages ($): The overstated Medicare wages\n"
        "- Medicare Tax ($): Auto-calculated at 1.45%, editable\n\n"
        "FUTA:\n"
        "- FUTA Wages ($): The overstated FUTA wages\n"
        "- FUTA Tax ($): Auto-calculated at 0.6%, editable\n\n"
        "Adjustment Date: Defaults to quarter end date (adjusted for weekends). Editable."
    )
    pdf.section_title("Validation")
    pdf.body_text(
        "The tool validates that entered tax amounts match expected rates. "
        "If SS Tax differs from 6.2% of SS Wages by more than $0.10, a warning "
        "appears. Same for Medicare (1.45%) and FUTA (0.6%). You can override "
        "the amounts if the variance is intentional."
    )

    pdf.chapter_title("3. CSV Output")
    pdf.section_title("Row Structure (per quarter)")
    pdf.body_text(
        "For each quarter with data, the tool generates:\n\n"
        "1. Clearing/Debit - 00-403 (SS Employee): refund SS tax\n"
        "2. Clearing/Debit - 00-404 (SS Employer): refund SS tax\n"
        "3. Clearing/Debit - 00-406 (Medicare Employee): refund Medicare tax\n"
        "4. Clearing/Debit - 00-407 (Medicare Employer): refund Medicare tax\n"
        "5. Clearing/Debit - 00-402 (FUTA): refund FUTA tax (if applicable)\n"
        "6. Member/Credit: sum of employee taxes (SS + Medicare) refunded to employee\n"
        "7. Company/Credit: sum of all taxes (including employer) refunded to company"
    )
    pdf.section_title("Download")
    pdf.body_text(
        "Preview the full CSV in a dataframe before downloading. "
        "Filename: {MID} {CID} FICA Refund.csv\n\n"
        "Missing MID or CID triggers an error prompting you to fill them in."
    )

    pdf.chapter_title("4. Step-by-Step Workflow")
    for step in [
        "1. Enter Member ID, Company ID, and select Tax Year",
        "2. In each relevant quarter, enter SS Wages and/or Medicare Wages",
        "3. Review auto-calculated tax amounts (adjust if needed)",
        "4. Add FUTA wages if applicable",
        "5. Verify adjustment dates (default to quarter-end, weekday-adjusted)",
        "6. Check validation warnings - dismiss or fix",
        "7. Add notes if needed",
        "8. Preview the CSV in the export section",
        "9. Download the CSV file",
    ]:
        pdf.body_text(step)

    output = OUTPUT_DIR / "POA_FICA_Refund_Guide.pdf"
    pdf.output(str(output))
    return str(output)


def build_fica_debit_guide(shots):
    pdf = GuidePDF("POA FICA Debit")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "Payroll Ops Adjustment", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "FICA Debit - User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 2.0 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "fica_debit" in shots:
        pdf.add_screenshot(shots["fica_debit"])

    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The FICA Debit tab generates CSV exports for collecting under-withheld FICA "
        "taxes (Social Security, Medicare, and FUTA) across one or more quarters. "
        "It creates Clearing/Credit rows for each tax type and matching Member/Debit "
        "and Company/Debit rows to charge the employee and increase the employer liability."
    )
    pdf.section_title("When to Use")
    for u in [
        "Employee was under-withheld for Social Security",
        "Medicare was under-collected and needs to be charged",
        "FUTA was missed or under-calculated",
        "Quarterly corrections to increase FICA withholding",
    ]:
        pdf.bullet(u)

    pdf.chapter_title("2. Input Fields")
    pdf.section_title("Global Fields")
    pdf.body_text(
        "Member ID: The employee's MID (M-prefix).\n"
        "Company ID: The CID for the company.\n"
        "Tax Year: Determines quarter end dates and wage bases."
    )
    pdf.section_title("Per-Quarter Data")
    pdf.body_text(
        "Each quarter (Q1-Q4) has an expandable section with:\n\n"
        "Gross: The taxable gross amount for this quarter's correction.\n\n"
        "Social Security:\n"
        "- SS Tax ($): Auto-calculated at 6.2% of gross, editable\n\n"
        "Medicare:\n"
        "- Medicare Tax ($): Auto-calculated at 1.45% of gross, editable\n\n"
        "FUTA:\n"
        "- FUTA Tax ($): Auto-calculated at 0.6% of gross, editable\n\n"
        "Adjustment Date: Defaults to quarter end date (adjusted for weekends). Editable."
    )
    pdf.section_title("Validation")
    pdf.body_text(
        "Same validation as FICA Refund - warns when entered amounts don't match "
        "expected rates. Override if the variance is intentional (e.g., partial-quarter "
        "correction or wage base capping)."
    )

    pdf.chapter_title("3. CSV Output")
    pdf.section_title("Row Structure (per quarter)")
    pdf.body_text(
        "For each quarter with data, the tool generates:\n\n"
        "1. Clearing/Credit - 00-403 (SS Employee): charge SS tax\n"
        "2. Clearing/Credit - 00-404 (SS Employer): charge SS tax\n"
        "3. Clearing/Credit - 00-406 (Medicare Employee): charge Medicare tax\n"
        "4. Clearing/Credit - 00-407 (Medicare Employer): charge Medicare tax\n"
        "5. Clearing/Credit - 00-402 (FUTA): charge FUTA tax (if applicable)\n"
        "6. Member/Debit: sum of employee taxes charged to employee\n"
        "7. Company/Debit: sum of all taxes (including employer) charged to company"
    )
    pdf.section_title("Download")
    pdf.body_text(
        "Preview the full CSV in a dataframe before downloading. "
        "Filename: {MID} {CID} FICA Debit.csv\n\n"
        "Missing MID or CID triggers an error prompting you to fill them in."
    )

    pdf.chapter_title("4. Step-by-Step Workflow")
    for step in [
        "1. Enter Member ID, Company ID, and select Tax Year",
        "2. In each relevant quarter, enter the Gross amount",
        "3. Review auto-calculated tax amounts (adjust if needed)",
        "4. Verify adjustment dates (default to quarter-end, weekday-adjusted)",
        "5. Check validation warnings - dismiss or fix",
        "6. Add notes if needed",
        "7. Preview the CSV in the export section",
        "8. Download the CSV file",
    ]:
        pdf.body_text(step)

    output = OUTPUT_DIR / "POA_FICA_Debit_Guide.pdf"
    pdf.output(str(output))
    return str(output)


if __name__ == "__main__":
    print("Capturing screenshots from Payroll Ops Adjustment...")
    screenshots = capture_screenshots()
    print(f"  Captured {len(screenshots)} screenshots in {SCREENSHOT_DIR}")

    print("Building Calculator guide...")
    print(f"  Saved: {build_calculator_guide(screenshots)}")

    print("Building FICA Refund guide...")
    print(f"  Saved: {build_fica_refund_guide(screenshots)}")

    print("Building FICA Debit guide...")
    print(f"  Saved: {build_fica_debit_guide(screenshots)}")

    print("Done!")
