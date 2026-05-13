"""
Generate PDF user guides for the automation tools:
- W-2C Automator (port 8506)
- Voucher Reversal Automator (port 8507)
- State Amendments Automator (port 8508)

Usage: python3 generate_automation_guides.py
Output: W2C_User_Guide.pdf, Voucher_Reversal_Guide.pdf, State_Amendments_Guide.pdf
"""

import os
import time
import tempfile
from pathlib import Path
from fpdf import FPDF
from playwright.sync_api import sync_playwright

PASSWORD = "PayOps2026"
OUTPUT_DIR = Path(__file__).parent
SCREENSHOT_DIR = Path(tempfile.mkdtemp(prefix="auto_guide_"))

TOOLS = {
    "w2c": {"url": "http://localhost:8506", "name": "W-2C Automator"},
    "voucher": {"url": "http://localhost:8507", "name": "Voucher Reversal"},
    "state": {"url": "http://localhost:8508", "name": "State Amendments"},
}


def capture_screenshots():
    """Capture screenshots of each automation tool."""
    shots = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for key, tool in TOOLS.items():
            try:
                page = browser.new_page(viewport={"width": 1400, "height": 900})
                page.goto(tool["url"], wait_until="networkidle")
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

                path = SCREENSHOT_DIR / f"{key}.png"
                page.screenshot(path=str(path), full_page=False)
                shots[key] = str(path)
                page.close()
            except Exception as e:
                print(f"  Warning: Could not capture {key}: {e}")

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


def build_w2c_guide(shots):
    pdf = GuidePDF("W-2C Automator")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "W-2C Automator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(0, 12, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 1.2 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "w2c" in shots:
        pdf.add_screenshot(shots["w2c"])

    # Overview
    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The W-2C Automator automates the process of generating and uploading "
        "W-2C corrections in CS Tools (cstools-workforce.justworks.com). It takes "
        "a list of MIDs and a tax year, then uses Playwright browser automation to "
        "click 'Generate W2c' and 'Upload W2c' for each employee."
    )
    pdf.section_title("What It Does")
    actions = [
        "Navigates to each employee's tax forms page in CS Tools",
        "Clicks 'Generate W2c' on the specified tax year row",
        "Waits for generation to complete",
        "Clicks 'Upload W2c' on the highest correction number for that year",
        "Logs success/failure for each MID to results.csv",
        "Writes failed MIDs to failed_mids.txt for retry",
    ]
    for a in actions:
        pdf.bullet(a)

    # Setup
    pdf.chapter_title("2. Setup")
    pdf.section_title("Dependencies")
    pdf.body_text(
        "Click 'Install Dependencies' in the sidebar, or run manually:\n\n"
        "pip install playwright streamlit pandas && python -m playwright install chromium\n\n"
        "This installs the Playwright browser automation library and downloads "
        "the Chromium browser binary."
    )
    pdf.section_title("No Special Folders Needed")
    pdf.body_text(
        "The tool saves mids.txt, results.csv, and failed_mids.txt in the same "
        "directory as the script. No additional folders need to be created."
    )

    # Usage
    pdf.chapter_title("3. Step-by-Step Usage")
    steps = [
        "1. Paste MIDs: Enter one MID per line in the text area. Blank lines and # comments are ignored. Duplicates are removed automatically.",
        "2. Select Tax Year: Choose the year for W-2C generation (2024 is default).",
        "3. Save to mids.txt: Click the Save button. The count of saved MIDs is confirmed.",
        "4. Run the automation: Either click 'Run Now' in the dashboard or copy the terminal command and run it manually.",
        "5. Okta Authentication: When Chromium opens, log in via Okta Verify if prompted, then press Enter in the terminal to start processing.",
        "6. Monitor progress: The automation streams progress live. Each MID is processed and results save to results.csv after every row.",
        "7. Review results: Click 'Refresh Results' to see the outcome. Filter by All, Failures only, or Successes only.",
        "8. Retry failures: If any MIDs failed, edit the retry list and click 'Retry Now' or copy the retry command.",
    ]
    for step in steps:
        pdf.body_text(step)

    # Results
    pdf.chapter_title("4. Understanding Results")
    pdf.section_title("Status Values")
    pdf.body_text(
        "ok: W-2C was successfully generated and uploaded.\n"
        "not_found: The MID was not found in CS Tools.\n"
        "error: An unexpected error occurred during processing.\n\n"
        "The results panel shows metric cards for Processed, Successful, "
        "Not Found, and Errors counts."
    )
    pdf.section_title("Retry Logic")
    pdf.body_text(
        "Failed MIDs are written to failed_mids.txt. You can:\n"
        "- Edit the list to remove MIDs you don't want to retry\n"
        "- Click 'Retry Now' to reprocess them\n"
        "- A successful retry overwrites the original row in results.csv"
    )

    output = OUTPUT_DIR / "W2C_User_Guide.pdf"
    pdf.output(str(output))
    return str(output)


def build_voucher_guide(shots):
    pdf = GuidePDF("Voucher Reversal")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "Voucher Reversal Automator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(255, 190, 11)
    pdf.cell(0, 12, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 1.2 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "voucher" in shots:
        pdf.add_screenshot(shots["voucher"])

    # Overview
    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The Voucher Reversal Automator processes voucher reversals in CS Tools "
        "(cstools-workforce.justworks.com). It takes a table of voucher data "
        "(MID, VoucherID, SettlementDate, AdjComment) and automates the reversal "
        "form submission for each row."
    )
    pdf.section_title("What It Does")
    actions = [
        "Navigates to the voucher management page for each MID",
        "Locates the specified voucher by ID",
        "Fills in the settlement date and adjustment comment",
        "Submits the reversal form",
        "Logs success/failure for each voucher to results.csv",
        "Writes failed rows to failed_vouchers.csv for retry",
    ]
    for a in actions:
        pdf.bullet(a)

    # Setup
    pdf.chapter_title("2. Setup")
    pdf.section_title("Dependencies")
    pdf.body_text(
        "Click 'Install Dependencies' in the sidebar, or run manually:\n\n"
        "pip install playwright streamlit pandas && python -m playwright install chromium"
    )
    pdf.section_title("No Special Folders Needed")
    pdf.body_text(
        "The tool saves vouchers.csv, results.csv, and failed_vouchers.csv in the "
        "same directory as the script. No additional setup required."
    )

    # Usage
    pdf.chapter_title("3. Step-by-Step Usage")
    steps = [
        "1. Paste Table: Enter a 4-column table with headers: MID, VoucherID, SettlementDate, AdjComment. Tab or comma separated.",
        "2. Verify Preview: Check that columns were parsed correctly. Duplicates are auto-removed.",
        "3. Save to vouchers.csv: Click the Save button. Row count is confirmed.",
        "4. Run the automation: Click 'Run Now' or copy the terminal command.",
        "5. Okta Authentication: Log in via Okta Verify if prompted, then press Enter.",
        "6. Monitor progress: Progress streams live in the terminal.",
        "7. Review results: Click 'Refresh Results' to see outcomes.",
        "8. Retry failures: Edit failed rows and click 'Retry Now'.",
    ]
    for step in steps:
        pdf.body_text(step)

    # Input format
    pdf.chapter_title("4. Input Format")
    pdf.section_title("Required Columns")
    pdf.body_text(
        "MID: Member ID for the employee (e.g., M123456).\n"
        "VoucherID: The voucher identifier to reverse (e.g., V789012).\n"
        "SettlementDate: Date in MM/DD/YYYY format (e.g., 03/15/2025).\n"
        "AdjComment: Adjustment comment explaining the reversal."
    )
    pdf.section_title("Column Name Flexibility")
    pdf.body_text(
        "The parser accepts various column name formats:\n"
        "- MID: also accepts 'MemberID'\n"
        "- VoucherID: also accepts 'Voucher'\n"
        "- SettlementDate: also accepts 'SettleDate', 'Settlement'\n"
        "- AdjComment: also accepts 'AdjustmentComment', 'Comment', 'Comments', 'Note', 'Notes'"
    )

    # Results
    pdf.chapter_title("5. Understanding Results")
    pdf.section_title("Status Values")
    pdf.body_text(
        "ok: Voucher was successfully reversed.\n"
        "placeholder: Voucher exists but is a placeholder (not reversible).\n"
        "not_found: The voucher was not found for the given MID.\n"
        "error: An unexpected error occurred.\n\n"
        "Metric cards show: Processed, Successful, Placeholder, Not Found, Errors."
    )
    pdf.section_title("Retry")
    pdf.body_text(
        "Failed rows are saved in CSV format. You can edit the CSV directly "
        "in the retry text area to remove rows before retrying. A successful "
        "retry overwrites the original row in results.csv."
    )

    output = OUTPUT_DIR / "Voucher_Reversal_Guide.pdf"
    pdf.output(str(output))
    return str(output)


def build_state_amendments_guide(shots):
    pdf = GuidePDF("State Amendments")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(10, 14, 39)
    pdf.cell(0, 15, "State Amendments Automator", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(131, 56, 236)
    pdf.cell(0, 12, "User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Payroll Operations Team", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Version 1.2 | May 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    if "state" in shots:
        pdf.add_screenshot(shots["state"])

    # Overview
    pdf.chapter_title("1. Overview")
    pdf.body_text(
        "The State Amendments Automator processes state tax amendment filings in "
        "CS Tools (cstools-workforce.justworks.com). It takes a CSV with employee "
        "data grouped by state, batch settings (CID, Company Name), and automates "
        "the amendment form submission for each state."
    )
    pdf.section_title("What It Does")
    actions = [
        "Groups employees by state from the uploaded CSV",
        "Navigates to the state amendment form in CS Tools",
        "Fills in CID, Company Name, employee details, and total state tax",
        "Uses the Amendment Title for JWEG/Period identification",
        "Submits each state amendment",
        "Logs success/failure to results.csv",
        "Writes failed rows to failed_amendments.csv for retry",
    ]
    for a in actions:
        pdf.bullet(a)

    # Setup
    pdf.chapter_title("2. Setup")
    pdf.section_title("Dependencies")
    pdf.body_text(
        "Click 'Install Dependencies' in the sidebar, or run manually:\n\n"
        "pip install playwright streamlit pandas && python -m playwright install chromium"
    )
    pdf.section_title("No Special Folders Needed")
    pdf.body_text(
        "The tool saves amendments.csv, results.csv, and failed_amendments.csv in "
        "the same directory as the script. No additional setup required."
    )

    # Input
    pdf.chapter_title("3. Input Format")
    pdf.section_title("CSV Upload")
    pdf.body_text(
        "Upload a CSV file with 5 columns:\n\n"
        "State: The state name (e.g., California, New York).\n"
        "Employee Name: Full name of the employee.\n"
        "MID: Member ID (auto-prefixed with M if missing).\n"
        "Total State Tax: The total state tax amount for the amendment.\n"
        "Amendment Title: Used for JWEG/Period identification in CS Tools."
    )
    pdf.section_title("Grouping Logic")
    pdf.body_text(
        "Rows with the same State are grouped into a single amendment. "
        "The preview shows:\n"
        "- Number of employees per state\n"
        "- Total state tax per state\n"
        "- Amendment title per state\n"
        "- Grand total across all states"
    )
    pdf.section_title("Data Source")
    pdf.body_text(
        "You can drop in the Large Adjustment Generator's State Tax Export "
        "directly - it produces the exact format needed."
    )
    pdf.section_title("Validation Warnings")
    pdf.body_text(
        "The tool warns about:\n"
        "- States missing an Amendment Title (required for form submission)\n"
        "- States with different Total State Tax values across rows\n"
        "- Mismatch between number of Names and MIDs"
    )

    # Batch Settings
    pdf.chapter_title("4. Batch Settings")
    pdf.body_text(
        "These settings apply to every amendment in the batch:\n\n"
        "CID: Company identifier (e.g., C12345). Passed to the automation script.\n"
        "Company Name: Full company name (e.g., Zip Co US Inc.). Used in the form.\n\n"
        "Both are required - the tool warns if either is missing."
    )

    # Usage
    pdf.chapter_title("5. Step-by-Step Usage")
    steps = [
        "1. Upload CSV: Drop in a CSV file with the 5 required columns.",
        "2. Verify Preview: Check the state grouping summary - employees per state, totals.",
        "3. Fix any warnings: Missing titles, tax variances, or name/MID mismatches.",
        "4. Save to amendments.csv: Click Save. Row and state counts are confirmed.",
        "5. Enter Batch Settings: Fill in CID and Company Name.",
        "6. Run the automation: Click 'Run Now' or copy the terminal command.",
        "7. Okta Authentication: Log in via Okta Verify if prompted, then press Enter.",
        "8. Monitor progress: Progress streams live in the terminal.",
        "9. Review results: Click 'Refresh Results' to see outcomes.",
        "10. Retry failures: Edit failed rows and click 'Retry Now'.",
    ]
    for step in steps:
        pdf.body_text(step)

    # Results
    pdf.chapter_title("6. Understanding Results")
    pdf.section_title("Status Values")
    pdf.body_text(
        "ok: Amendment was successfully submitted.\n"
        "placeholder: Form submitted but in placeholder state.\n"
        "not_found: The company/employee was not found.\n"
        "error: An unexpected error occurred.\n\n"
        "Metric cards show: Processed, Successful, Placeholder, Not Found, Errors."
    )
    pdf.section_title("Retry")
    pdf.body_text(
        "Failed rows are saved in CSV format. Edit the retry area to remove "
        "rows you don't want to retry. A successful retry overwrites the "
        "original row in results.csv."
    )

    output = OUTPUT_DIR / "State_Amendments_Guide.pdf"
    pdf.output(str(output))
    return str(output)


if __name__ == "__main__":
    print("Capturing screenshots from automation tools...")
    screenshots = capture_screenshots()
    print(f"  Captured {len(screenshots)} screenshots in {SCREENSHOT_DIR}")

    print("Building W-2C Automator guide...")
    print(f"  Saved: {build_w2c_guide(screenshots)}")

    print("Building Voucher Reversal guide...")
    print(f"  Saved: {build_voucher_guide(screenshots)}")

    print("Building State Amendments guide...")
    print(f"  Saved: {build_state_amendments_guide(screenshots)}")

    print("Done!")
