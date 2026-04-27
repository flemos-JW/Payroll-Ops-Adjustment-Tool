# Payroll Ops Adjustment Tool

A Streamlit app for payroll tax calculations, FICA refunds, and FICA debits.

---

## One-Time Setup

### 1. Install Python
Download and install Python from [python.org/downloads](https://www.python.org/downloads/). Choose the latest version and run the installer.

To verify it installed, open **Terminal** and run:
```
python3 --version
```

### 2. Clone the repo
In Terminal, run:
```
git clone https://github.com/flemos-JW/Payroll-Ops-Adjustment-Tool.git
cd Payroll-Ops-Adjustment-Tool
```

### 3. Install dependencies
```
pip3 install -r requirements.txt
```

---

## Running the App

Any time you want to open the app, run this in Terminal:
```
streamlit run payroll_ops_adjustment.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## Auto-Launch on Startup (Mac)

Follow these steps once to have the app start automatically every time you turn on your Mac.

### 1. Find your three values
Open Terminal and run each of these commands. Write down the output — you'll need all three in the next step.

**Your username:**
```
whoami
```
Example output: `janesmith`

**Your Python path:**
```
which python3
```
Example output: `/usr/local/bin/python3`

**Your repo path** — this is the folder where you cloned the repo. Run:
```
cd ~/Payroll-Ops-Adjustment-Tool && pwd
```
Example output: `/Users/janesmith/Payroll-Ops-Adjustment-Tool`

### 2. Create the launch agent file
Open TextEdit, switch to plain text mode (**Format → Make Plain Text**), and paste the following — replacing `YOUR_USERNAME`, `YOUR_PYTHON_PATH`, and `YOUR_REPO_PATH` with the values you just collected.

For example, if your username is `janesmith`, your Python path is `/usr/local/bin/python3`, and your repo path is `/Users/janesmith/Payroll-Ops-Adjustment-Tool`, the file would look like:
- `com.janesmith.payrollopstool`
- `<string>/usr/local/bin/python3</string>`
- `<string>/Users/janesmith/Payroll-Ops-Adjustment-Tool/payroll_ops_adjustment.py</string>`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.YOUR_USERNAME.payrollopstool</string>

    <key>ProgramArguments</key>
    <array>
        <string>YOUR_PYTHON_PATH</string>
        <string>-m</string>
        <string>streamlit</string>
        <string>run</string>
        <string>/Users/YOUR_USERNAME/YOUR_REPO_PATH/payroll_ops_adjustment.py</string>
        <string>--server.headless</string>
        <string>true</string>
        <string>--server.port</string>
        <string>8501</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/payrollopstool.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/payrollopstool.log</string>
</dict>
</plist>
```

Save the file as `com.YOUR_USERNAME.payrollopstool.plist` in this folder:
```
/Users/YOUR_USERNAME/Library/LaunchAgents/
```

### 3. Register the launch agent
In Terminal, run:
```
launchctl load ~/Library/LaunchAgents/com.YOUR_USERNAME.payrollopstool.plist
```

The app will now start automatically on login and restart if it ever crashes. Access it at `http://localhost:8501`.

### To stop the auto-launch
```
launchctl unload ~/Library/LaunchAgents/com.YOUR_USERNAME.payrollopstool.plist
```
