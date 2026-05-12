"""
Shared UI components for Payroll Ops Streamlit tools.
Provides consistent styling, alerts, headers, and table helpers.
"""
import streamlit as st

# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------
COLORS = {
    "cyan":    "#00e5ff",
    "green":   "#06ffa5",
    "yellow":  "#ffbe0b",
    "magenta": "#ff006e",
    "purple":  "#8338ec",
    "blue":    "#2563eb",
    "muted":   "#8a9bb0",
    "amber":   "#b45309",
    "amber_bg": "#fffbeb",
}

ALERT_CONFIG = {
    "ok":   {"color": "#06ffa5", "bg": "rgba(6,255,165,0.08)",   "shadow": "rgba(6,255,165,0.12)"},
    "warn": {"color": "#ffbe0b", "bg": "rgba(255,190,11,0.08)",  "shadow": "rgba(255,190,11,0.12)"},
    "info": {"color": "#00e5ff", "bg": "rgba(0,229,255,0.06)",   "shadow": "none"},
    "err":  {"color": "#ff006e", "bg": "rgba(255,0,110,0.08)",   "shadow": "rgba(255,0,110,0.12)"},
}


# ---------------------------------------------------------------------------
# Shared CSS — call once per app at the top
# ---------------------------------------------------------------------------
def inject_global_css(prefix: str, accent_color: str = "#00e5ff"):
    """Inject shared CSS for alerts and number input cleanup. Call once at app start."""
    alert_css = ""
    for atype, cfg in ALERT_CONFIG.items():
        shadow = f"box-shadow: 0 0 15px {cfg['shadow']};" if cfg["shadow"] != "none" else ""
        alert_css += (
            f".{prefix}-alert-{atype} {{ background: {cfg['bg']}; "
            f"border-left: 3px solid {cfg['color']}; {shadow} }}\n"
        )

    st.markdown(f"""
<style>
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {{ display: none !important; }}
.{prefix}-alert {{ padding: 12px 18px; border-radius: 8px; margin: 12px 0; }}
{alert_css}
.{prefix}-alert-label {{ font-weight: 700; font-size: 0.82rem; letter-spacing: 0.08em; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header with shimmer animation
# ---------------------------------------------------------------------------
def render_header(prefix: str, title: str, subtitle: str, accent_color: str = "#00e5ff",
                  secondary_color: str = "#ff006e", icon: str = ""):
    """Render the animated gradient header used by automation tools."""
    st.markdown(f"""
<style>
.{prefix}-header {{
    background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #16213e 100%);
    padding: 26px 30px; border-radius: 14px; margin-bottom: 22px;
    border: 1px solid {_rgba(accent_color, 0.3)};
    box-shadow: 0 0 30px {_rgba(accent_color, 0.15)}, inset 0 0 20px rgba(131, 56, 236, 0.08);
    position: relative; overflow: hidden;
}}
.{prefix}-header::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, {accent_color}, {secondary_color}, #8338ec, transparent);
    background-size: 200% 100%; animation: {prefix}shimmer 4s infinite linear;
}}
@keyframes {prefix}shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}
.{prefix}-header h1 {{
    margin: 0; color: {accent_color}; font-size: 1.55rem; font-weight: 700;
    letter-spacing: 0.05em; text-shadow: 0 0 20px {_rgba(accent_color, 0.4)};
}}
.{prefix}-header p {{ margin: 6px 0 0 0; color: #8a9bb0; font-size: 0.85rem; letter-spacing: 0.12em; }}
</style>
<div class="{prefix}-header">
    <h1>{icon}  {title}</h1>
    <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Alert component
# ---------------------------------------------------------------------------
def render_alert(prefix: str, alert_type: str, label: str, message: str):
    """
    Render a styled alert box.
    alert_type: 'ok', 'warn', 'info', or 'err'
    """
    color = ALERT_CONFIG[alert_type]["color"]
    st.markdown(f"""
<div class="{prefix}-alert {prefix}-alert-{alert_type}">
    <span class="{prefix}-alert-label" style="color:{color};">{label}</span>
    <div style="color:#c5d1e0; font-size:0.85rem; margin-top:4px;">{message}</div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Validation warning box (used by payroll/FICA tools)
# ---------------------------------------------------------------------------
def render_validation_warning(title: str, items: list[str]):
    """Render an amber warning box with a list of validation issues."""
    items_html = "".join(
        f'<p style="margin:4px 0; font-size:0.9rem; color:#b45309;">&#9888; {item}</p>'
        for item in items
    )
    st.markdown(
        f'<div style="background:#fffbeb; border-left:3px solid #b45309; '
        f'padding:10px 14px; border-radius:4px; margin-bottom:8px;">'
        f'<p style="margin:0 0 6px 0; font-size:0.85rem; font-weight:600; color:#b45309;">{title}</p>'
        f'{items_html}</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Breakdown table (Item / Amount)
# ---------------------------------------------------------------------------
def render_breakdown_table(rows: list[tuple[str, str, bool]]):
    """
    Render an Item/Amount breakdown table.
    rows: list of (label, formatted_amount, is_bold)
    """
    html = (
        '<table style="width:100%; border-collapse:collapse; font-family:inherit; font-size:1rem;">'
        '<thead><tr style="border-bottom:2px solid #ccc;">'
        '<th style="text-align:left; padding:6px 4px; font-weight:600;">Item</th>'
        '<th style="text-align:right; padding:6px 8px; font-weight:600;">Amount</th>'
        '</tr></thead><tbody>'
    )
    for label, amount, bold in rows:
        amt_str = f"<b>{amount}</b>" if bold else amount
        lbl_str = f"<b>{label}</b>" if bold else label
        html += (
            f'<tr style="border-bottom:1px solid #f0f0f0;">'
            f'<td style="padding:7px 4px;">{lbl_str}</td>'
            f'<td style="text-align:right; padding:7px 8px; font-variant-numeric:tabular-nums; '
            f'white-space:nowrap;">{amt_str}</td>'
            f'</tr>'
        )
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Copy-to-clipboard component
# ---------------------------------------------------------------------------
_COPY_BUTTON_ID = 0

def render_copyable_html(html_content: str, button_label: str = "Copy to Clipboard"):
    """
    Render HTML content with a copy button that copies rich HTML to clipboard.
    Jira/Confluence will preserve bold, links, and line breaks on paste.
    """
    global _COPY_BUTTON_ID
    _COPY_BUTTON_ID += 1
    container_id = f"copyable-{_COPY_BUTTON_ID}"

    import streamlit.components.v1 as stc
    stc.html(f"""
<div id="{container_id}" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
     font-size: 14px; line-height: 1.8; padding: 12px 0;">
    {html_content}
</div>
<button onclick="copyContent_{_COPY_BUTTON_ID}()" style="
    margin-top: 8px; padding: 6px 14px; font-size: 0.8rem; font-weight: 600;
    background: #f0f2f6; border: 1px solid #d1d5db; border-radius: 6px;
    cursor: pointer; color: #374151; letter-spacing: 0.02em;
    transition: background 0.15s;">
    {button_label}
</button>
<script>
function copyContent_{_COPY_BUTTON_ID}() {{
    const el = document.getElementById("{container_id}");
    const html = el.innerHTML;
    const blob = new Blob([html], {{type: "text/html"}});
    const plainBlob = new Blob([el.innerText], {{type: "text/plain"}});
    const item = new ClipboardItem({{"text/html": blob, "text/plain": plainBlob}});
    navigator.clipboard.write([item]).then(() => {{
        const btn = event.target;
        btn.textContent = "Copied!";
        btn.style.background = "#d1fae5";
        btn.style.borderColor = "#06ffa5";
        setTimeout(() => {{
            btn.textContent = "{button_label}";
            btn.style.background = "#f0f2f6";
            btn.style.borderColor = "#d1d5db";
        }}, 1500);
    }});
}}
</script>
""", height=0, scrolling=False)


# ---------------------------------------------------------------------------
# CS Tools summary block (used by payroll ops calculator)
# ---------------------------------------------------------------------------
def render_cs_tools_summary(header_html: str, lines: list[str]):
    """
    Render a CS Tools adjustment summary block.
    header_html: the clickable/bold header line
    lines: list of HTML strings for each detail line (e.g., "Employee Credit: $X on DATE")
    """
    body = "<br>".join(lines)
    st.markdown(
        f'<div style="font-size:0.9rem; line-height:1.8;">'
        f'<p style="margin:0 0 8px 0; line-height:1.4;">{header_html}<br>{body}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Dashboard CSS (KPI cards, section dividers, viz header)
# ---------------------------------------------------------------------------
def inject_dashboard_css(prefix: str = "viz"):
    """Inject CSS classes for dashboard KPI cards and section dividers."""
    st.markdown(f"""
<style>
.{prefix}-header {{
    background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #16213e 100%);
    padding: 26px 30px; border-radius: 14px; margin-bottom: 22px;
    border: 1px solid rgba(0, 229, 255, 0.3);
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.15), inset 0 0 20px rgba(131, 56, 236, 0.08);
    position: relative; overflow: hidden;
}}
.{prefix}-header::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #00e5ff, #ff006e, #8338ec, transparent);
    background-size: 200% 100%; animation: {prefix}shimmer 4s infinite linear;
}}
@keyframes {prefix}shimmer {{
    0%   {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}
.{prefix}-header h1 {{
    margin: 0; color: #00e5ff; font-size: 1.55rem; font-weight: 700;
    letter-spacing: 0.05em; text-shadow: 0 0 20px rgba(0, 229, 255, 0.4);
}}
.{prefix}-header p {{ margin: 6px 0 0 0; color: #8a9bb0; font-size: 0.85rem; letter-spacing: 0.12em; }}
.kpi-card {{
    background: linear-gradient(135deg, rgba(10, 15, 30, 0.95) 0%, rgba(22, 33, 62, 0.95) 100%);
    border-radius: 10px; padding: 16px 18px; position: relative; overflow: hidden;
}}
.kpi-label {{ color: #8a9bb0; font-size: 0.68rem; letter-spacing: 0.14em; font-weight: 700; text-transform: uppercase; }}
.kpi-value {{ font-size: 1.3rem; font-weight: 700; margin: 6px 0 2px 0; font-variant-numeric: tabular-nums; }}
.kpi-sub {{ color: #64748b; font-size: 0.72rem; }}
.{prefix}-section {{
    background: linear-gradient(135deg, rgba(10,15,30,0.95), rgba(22,33,62,0.95));
    border-radius: 10px; padding: 12px 18px; margin: 18px 0 12px 0;
}}
.{prefix}-section-label {{ font-size: 0.75rem; letter-spacing: 0.16em; font-weight: 700; }}
</style>
""", unsafe_allow_html=True)


def kpi_card_html(label: str, value: str, color: str, sub: str = "") -> str:
    """Return KPI card HTML string (for use with col.markdown())."""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi-card" style="border:1px solid {color}44; box-shadow:0 0 20px {color}22, inset 0 0 30px {color}0e;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg, transparent, {color}, transparent);"></div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}; text-shadow:0 0 14px {color}66;">{value}</div>'
        f'{sub_html}</div>'
    )


def render_kpi_card(label: str, value: str, color: str, sub: str = ""):
    """Render a single KPI card with accent color glow (calls st.markdown directly)."""
    st.markdown(kpi_card_html(label, value, color, sub), unsafe_allow_html=True)


def render_section_divider(prefix: str, label: str, color: str = "#00e5ff"):
    """Render a styled section divider with label."""
    st.markdown(f"""
<div class="{prefix}-section" style="border-left: 3px solid {color}; box-shadow: 0 0 15px {_rgba(color, 0.15)};">
    <div class="{prefix}-section-label" style="color:{color};">{label}</div>
</div>
""", unsafe_allow_html=True)


def render_dashboard_header(prefix: str, title: str, subtitle: str):
    """Render the dashboard viz header."""
    st.markdown(f"""
<div class="{prefix}-header">
    <h1>{title}</h1>
    <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _rgba(hex_color: str, alpha: float) -> str:
    """Convert hex color to rgba string."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
