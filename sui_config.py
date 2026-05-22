"""SUI Configuration — Single source of truth for all payroll tools.

Contains 2026 wage bases, tax codes, rates, and reporting types per JWEG.
Reporting types: "peo", "client", "hybrid" (client reporting with PEO rate).

Usage:
    from sui_config import SUI_CONFIG
    state = SUI_CONFIG["New York"]
    rate = state["jweg1"]["total_rate"]  # decimal, e.g. 0.04
    reporting = state["jweg1"]["reporting"]  # "peo", "client", or "hybrid"
"""

SUI_CONFIG = {
    "Alabama": {
        "wage_base": {2026: 8000},
        "tax_codes": {
            "major": "01-459",
            "minors": [{"code": "01-461", "name": "Employment Security Assessment"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0064, "minor_rates": {"01-461": 0.0006}, "total_rate": 0.0070},
        "jweg2": {"reporting": "peo", "major_rate": 0.0264, "minor_rates": {"01-461": 0.0006}, "total_rate": 0.0270},
        "jweg3": {"reporting": "peo", "major_rate": 0.0264, "minor_rates": {"01-461": 0.0006}, "total_rate": 0.0270},
    },
    "Alaska": {
        "wage_base": {2026: 54200},
        "tax_codes": {
            "major": "02-459",
            "minors": [],
            "ee_codes": [{"code": "02-458", "name": "EE Unemployment Tax", "rate": 0.0050}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
    },
    "Arizona": {
        "wage_base": {2026: 8000},
        "tax_codes": {
            "major": "03-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0178, "minor_rates": {}, "total_rate": 0.0178},
        "jweg2": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
        "jweg3": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
    },
    "Arkansas": {
        "wage_base": {2026: 7000},
        "tax_codes": {
            "major": "04-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
        "jweg2": {"reporting": "client", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
        "jweg3": {"reporting": "client", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
    },
    "California": {
        "wage_base": {2026: 7000},
        "tax_codes": {
            "major": "05-459",
            "minors": [{"code": "05-461", "name": "Employment Training Tax"}],
            "other": [{"code": "05-466", "name": "State Disability Insurance (SDI)", "rate": 0.0130}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0340, "minor_rates": {"05-461": 0.0010}, "total_rate": 0.0350},
        "jweg2": {"reporting": "client", "major_rate": 0.0340, "minor_rates": {"05-461": 0.0010}, "total_rate": 0.0350},
        "jweg3": {"reporting": "client", "major_rate": 0.0340, "minor_rates": {"05-461": 0.0010}, "total_rate": 0.0350},
    },
    "Colorado": {
        "wage_base": {2026: 30600},
        "tax_codes": {
            "major": "06-459",
            "minors": [
                {"code": "CO0000-128", "name": "Support Surcharge"},
                {"code": "CO0000-145", "name": "Solvency Tax Surcharge"},
            ],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.02220, "minor_rates": {"CO0000-128": 0.00250, "CO0000-145": 0.00725}, "total_rate": 0.03195},
        "jweg2": {"reporting": "peo", "major_rate": 0.02220, "minor_rates": {"CO0000-128": 0.00250, "CO0000-145": 0.00725}, "total_rate": 0.03195},
        "jweg3": {"reporting": "peo", "major_rate": 0.03130, "minor_rates": {"CO0000-128": 0.00350, "CO0000-145": 0.01100}, "total_rate": 0.04580},
    },
    "Connecticut": {
        "wage_base": {2026: 27000},
        "tax_codes": {
            "major": "07-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0190, "minor_rates": {}, "total_rate": 0.0190},
        "jweg2": {"reporting": "client", "major_rate": 0.0190, "minor_rates": {}, "total_rate": 0.0190},
        "jweg3": {"reporting": "client", "major_rate": 0.0190, "minor_rates": {}, "total_rate": 0.0190},
    },
    "Delaware": {
        "wage_base": {2026: 14500},
        "tax_codes": {
            "major": "08-459",
            "minors": [],
            "other": [{"code": "08-461", "name": "DETS (semi-annual, separate tax)"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {}, "total_rate": 0.0120},
        "jweg2": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {}, "total_rate": 0.0120},
        "jweg3": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {}, "total_rate": 0.0120},
    },
    "District of Columbia": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "09-459",
            "minors": [{"code": "09-461", "name": "Admin Funding Assessment"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0190, "minor_rates": {"09-461": 0.0020}, "total_rate": 0.0210},
        "jweg2": {"reporting": "peo", "major_rate": 0.0270, "minor_rates": {"09-461": 0.0020}, "total_rate": 0.0290},
        "jweg3": {"reporting": "peo", "major_rate": 0.0270, "minor_rates": {"09-461": 0.0020}, "total_rate": 0.0290},
    },
    "Florida": {
        "wage_base": {2026: 7000},
        "tax_codes": {
            "major": "10-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0023, "minor_rates": {}, "total_rate": 0.0023},
        "jweg2": {"reporting": "peo", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg3": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
    },
    "Georgia": {
        "wage_base": {2026: 9500},
        "tax_codes": {
            "major": "11-459",
            "minors": [{"code": "11-461", "name": "Admin Assessment"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0077, "minor_rates": {"11-461": 0.0006}, "total_rate": 0.0083},
        "jweg2": {"reporting": "client", "major_rate": 0.0264, "minor_rates": {"11-461": 0.0006}, "total_rate": 0.0270},
        "jweg3": {"reporting": "peo", "major_rate": 0.0264, "minor_rates": {"11-461": 0.0006}, "total_rate": 0.0270},
    },
    "Hawaii": {
        "wage_base": {2026: 64500},
        "tax_codes": {
            "major": "12-459",
            "minors": [{"code": "12-461", "name": "Employment & Training Assessment"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0180, "minor_rates": {"12-461": 0.0001}, "total_rate": 0.0181},
        "jweg2": {"reporting": "peo", "major_rate": 0.0140, "minor_rates": {"12-461": 0.0001}, "total_rate": 0.0141},
        "jweg3": {"reporting": "peo", "major_rate": 0.0240, "minor_rates": {"12-461": 0.0001}, "total_rate": 0.0241},
    },
    "Idaho": {
        "wage_base": {2026: 58300},
        "tax_codes": {
            "major": "13-459",
            "minors": [
                {"code": "13-461", "name": "Workforce Development"},
                {"code": "13-463", "name": "Administrative Reserve"},
            ],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0067318, "minor_rates": {"13-461": 0.0002082, "13-463": 0.0}, "total_rate": 0.00694},
        "jweg2": {"reporting": "peo", "major_rate": 0.0067318, "minor_rates": {"13-461": 0.0002082, "13-463": 0.0}, "total_rate": 0.00694},
        "jweg3": {"reporting": "peo", "major_rate": 0.0097000, "minor_rates": {"13-461": 0.0003000, "13-463": 0.0}, "total_rate": 0.01000},
    },
    "Illinois": {
        "wage_base": {2026: 14250},
        "tax_codes": {
            "major": "14-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.07050, "minor_rates": {}, "total_rate": 0.07050},
        "jweg2": {"reporting": "client", "major_rate": 0.03350, "minor_rates": {}, "total_rate": 0.03350},
        "jweg3": {"reporting": "peo", "major_rate": 0.03450, "minor_rates": {}, "total_rate": 0.03450},
    },
    "Indiana": {
        "wage_base": {2026: 9500},
        "tax_codes": {
            "major": "15-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200},
        "jweg2": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200, "note": "Uses JWEG I cost rate"},
        "jweg3": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {}, "total_rate": 0.0200, "note": "Uses JWEG I cost rate"},
    },
    "Iowa": {
        "wage_base": {2026: 20400},
        "tax_codes": {
            "major": "16-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
    },
    "Kansas": {
        "wage_base": {2026: 15100},
        "tax_codes": {
            "major": "KS0000-010",
            "minors": [],
        },
        "jweg1": {"reporting": "hybrid", "major_rate": 0.0180, "minor_rates": {}, "total_rate": 0.0180},
        "jweg2": {"reporting": "hybrid", "major_rate": 0.0175, "minor_rates": {}, "total_rate": 0.0175},
        "jweg3": {"reporting": "hybrid", "major_rate": 0.0175, "minor_rates": {}, "total_rate": 0.0175},
    },
    "Kentucky": {
        "wage_base": {2026: 12000},
        "tax_codes": {
            "major": "18-459",
            "minors": [],
            "note": "SCUF Minor of 0.75% included in major rate; MasterTax does not separate",
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg2": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg3": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
    },
    "Louisiana": {
        "wage_base": {2026: 7000},
        "tax_codes": {
            "major": "19-459",
            "minors": [],
            "note": "Social charge minor included in main UI rate",
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg2": {"reporting": "client", "major_rate": 0.0206, "minor_rates": {}, "total_rate": 0.0206},
        "jweg3": {"reporting": "client", "major_rate": 0.0206, "minor_rates": {}, "total_rate": 0.0206},
    },
    "Maine": {
        "wage_base": {2026: 12000},
        "tax_codes": {
            "major": "20-459",
            "minors": [
                {"code": "ME0000-129", "name": "UP Administrative Fund Assessment"},
                {"code": "20-461", "name": "CSSF"},
            ],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0223, "minor_rates": {"ME0000-129": 0.0017, "20-461": 0.0014}, "total_rate": 0.0254},
        "jweg2": {"reporting": "client", "major_rate": 0.0223, "minor_rates": {"ME0000-129": 0.0017, "20-461": 0.0014}, "total_rate": 0.0254},
        "jweg3": {"reporting": "client", "major_rate": 0.0223, "minor_rates": {"ME0000-129": 0.0017, "20-461": 0.0014}, "total_rate": 0.0254},
    },
    "Maryland": {
        "wage_base": {2026: 8500},
        "tax_codes": {
            "major": "21-459",
            "minors": [{"code": "21-461", "name": "Admin Fee"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0345, "minor_rates": {"21-461": 0.0015}, "total_rate": 0.0360},
        "jweg2": {"reporting": "peo", "major_rate": 0.0245, "minor_rates": {"21-461": 0.0015}, "total_rate": 0.0260},
        "jweg3": {"reporting": "peo", "major_rate": 0.0245, "minor_rates": {"21-461": 0.0015}, "total_rate": 0.0260},
    },
    "Massachusetts": {
        "wage_base": {2026: 15000},
        "tax_codes": {
            "major": "22-459",
            "minors": [
                {"code": "22-453", "name": "Medical Assistance Contribution (EMAC)"},
                {"code": "22-461", "name": "Workforce Training Fund"},
                {"code": "22-463", "name": "COVID-19 Recovery Assessment"},
            ],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.02364, "minor_rates": {"22-453": 0.0, "22-461": 0.00056, "22-463": 0.00457}, "total_rate": 0.02877},
        "jweg2": {"reporting": "client", "major_rate": 0.02364, "minor_rates": {"22-453": 0.0, "22-461": 0.00056, "22-463": 0.00457}, "total_rate": 0.02877},
        "jweg3": {"reporting": "client", "major_rate": 0.02364, "minor_rates": {"22-453": 0.0, "22-461": 0.00056, "22-463": 0.00457}, "total_rate": 0.02877},
    },
    "Michigan": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "23-459",
            "minors": [],
            "note": "Wage base may be 9,500 depending on state assessment",
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg2": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg3": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
    },
    "Minnesota": {
        "wage_base": {2026: 44000},
        "tax_codes": {
            "major": "24-459",
            "minors": [{"code": "24-461", "name": "Workforce Enhancement Fee"}],
            "note": "Additional 14% assessment on tax due applied separately",
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0140, "minor_rates": {"24-461": 0.0010}, "total_rate": 0.0150},
        "jweg2": {"reporting": "client", "major_rate": 0.0140, "minor_rates": {"24-461": 0.0010}, "total_rate": 0.0150},
        "jweg3": {"reporting": "client", "major_rate": 0.0140, "minor_rates": {"24-461": 0.0010}, "total_rate": 0.0150},
    },
    "Mississippi": {
        "wage_base": {2026: 14000},
        "tax_codes": {
            "major": "MS0000-010",
            "minors": [{"code": "MS0000-128", "name": "Training Contribution"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"MS0000-128": 0.0020}, "total_rate": 0.0120},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"MS0000-128": 0.0020}, "total_rate": 0.0120},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"MS0000-128": 0.0020}, "total_rate": 0.0120},
    },
    "Missouri": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "26-459",
            "minors": [],
        },
        "jweg1": {"reporting": "hybrid", "major_rate": 0.02024, "minor_rates": {}, "total_rate": 0.02024},
        "jweg2": {"reporting": "hybrid", "major_rate": 0.02376, "minor_rates": {}, "total_rate": 0.02376},
        "jweg3": {"reporting": "hybrid", "major_rate": 0.02376, "minor_rates": {}, "total_rate": 0.02376},
    },
    "Montana": {
        "wage_base": {2026: 47300},
        "tax_codes": {
            "major": "27-459",
            "minors": [{"code": "27-461", "name": "Administrative Fund Tax"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0122, "minor_rates": {"27-461": 0.0018}, "total_rate": 0.0140},
        "jweg2": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {"27-461": 0.0018}, "total_rate": 0.0218},
        "jweg3": {"reporting": "peo", "major_rate": 0.0200, "minor_rates": {"27-461": 0.0018}, "total_rate": 0.0218},
    },
    "Nebraska": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "28-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0125, "minor_rates": {}, "total_rate": 0.0125},
        "jweg2": {"reporting": "client", "major_rate": 0.0125, "minor_rates": {}, "total_rate": 0.0125},
        "jweg3": {"reporting": "client", "major_rate": 0.0125, "minor_rates": {}, "total_rate": 0.0125},
    },
    "Nevada": {
        "wage_base": {2026: 43700},
        "tax_codes": {
            "major": "29-459",
            "minors": [{"code": "29-461", "name": "Career Enhancement Program"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0295, "minor_rates": {"29-461": 0.0005}, "total_rate": 0.0300},
        "jweg2": {"reporting": "client", "major_rate": 0.0295, "minor_rates": {"29-461": 0.0005}, "total_rate": 0.0300},
        "jweg3": {"reporting": "client", "major_rate": 0.0295, "minor_rates": {"29-461": 0.0005}, "total_rate": 0.0300},
    },
    "New Hampshire": {
        "wage_base": {2026: 14000},
        "tax_codes": {
            "major": "30-459",
            "minors": [{"code": "30-461", "name": "Administrative Contribution Tax"}],
        },
        "effective_date": "Jul 1, 2025 to Jun 30, 2026",
        "jweg1": {"reporting": "peo", "major_rate": 0.0090, "minor_rates": {"30-461": 0.0040}, "total_rate": 0.0130},
        "jweg2": {"reporting": "peo", "major_rate": 0.0130, "minor_rates": {"30-461": 0.0040}, "total_rate": 0.0170},
        "jweg3": {"reporting": "peo", "major_rate": 0.0130, "minor_rates": {"30-461": 0.0040}, "total_rate": 0.0170},
    },
    "New Jersey": {
        "wage_base": {2026: 44800},
        "tax_codes": {
            "major": "31-459",
            "minors": [{"code": "NJ0000-018", "name": "Workforce Development Tax (ER)"}],
            "ee_codes": [
                {"code": "31-458", "name": "EE State Unemployment Tax", "rate": 0.003825},
                {"code": "NJ0000-024", "name": "EE Workforce Development Partnership", "rate": 0.000250},
                {"code": "NJ0000-145", "name": "EE Supplemental Workforce Administrative", "rate": 0.000175},
            ],
        },
        "effective_date": "Jul 1, 2025 to Jun 30, 2026 (ER); Jan 1 to Dec 31 (EE)",
        "jweg1": {"reporting": "peo", "major_rate": 0.029825, "minor_rates": {"NJ0000-018": 0.001175}, "total_rate": 0.031000},
        "jweg2": {"reporting": "peo", "major_rate": 0.026825, "minor_rates": {"NJ0000-018": 0.001175}, "total_rate": 0.028000},
        "jweg3": {"reporting": "peo", "major_rate": 0.026825, "minor_rates": {"NJ0000-018": 0.001175}, "total_rate": 0.028000},
    },
    "New Mexico": {
        "wage_base": {2026: 34800},
        "tax_codes": {
            "major": "32-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0471, "minor_rates": {}, "total_rate": 0.0471},
        "jweg2": {"reporting": "peo", "major_rate": 0.0119, "minor_rates": {}, "total_rate": 0.0119},
        "jweg3": {"reporting": "peo", "major_rate": 0.0119, "minor_rates": {}, "total_rate": 0.0119},
    },
    "New York": {
        "wage_base": {2026: 17600},
        "tax_codes": {
            "major": "33-459",
            "minors": [{"code": "33-461", "name": "Re-employment Service Fund"}],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.03925, "minor_rates": {"33-461": 0.00075}, "total_rate": 0.04000},
        "jweg2": {"reporting": "peo", "major_rate": 0.02525, "minor_rates": {"33-461": 0.00075}, "total_rate": 0.02600},
        "jweg3": {"reporting": "peo", "major_rate": 0.04025, "minor_rates": {"33-461": 0.00075}, "total_rate": 0.04100},
    },
    "North Carolina": {
        "wage_base": {2026: 34200},
        "tax_codes": {
            "major": "34-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0095, "minor_rates": {}, "total_rate": 0.0095},
        "jweg2": {"reporting": "peo", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg3": {"reporting": "peo", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
    },
    "North Dakota": {
        "wage_base": {2026: 46600},
        "tax_codes": {
            "major": "35-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
    },
    "Ohio": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "36-459",
            "minors": [{"code": "36-461", "name": "Tech Surcharge"}],
            "note": "Vertex has minor separate; MTAX bundles it in major",
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {"36-461": 0.0015}, "total_rate": 0.0285},
        "jweg2": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {"36-461": 0.0015}, "total_rate": 0.0285},
        "jweg3": {"reporting": "client", "major_rate": 0.0270, "minor_rates": {"36-461": 0.0015}, "total_rate": 0.0285},
    },
    "Oklahoma": {
        "wage_base": {2026: 25000},
        "tax_codes": {
            "major": "37-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0180, "minor_rates": {}, "total_rate": 0.0180},
        "jweg2": {"reporting": "peo", "major_rate": 0.0150, "minor_rates": {}, "total_rate": 0.0150},
        "jweg3": {"reporting": "client", "major_rate": 0.0180, "minor_rates": {}, "total_rate": 0.0180},
    },
    "Oregon": {
        "wage_base": {2026: 56700},
        "tax_codes": {
            "major": "38-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0300, "minor_rates": {}, "total_rate": 0.0300},
        "jweg2": {"reporting": "peo", "major_rate": 0.0240, "minor_rates": {}, "total_rate": 0.0240},
        "jweg3": {"reporting": "peo", "major_rate": 0.0240, "minor_rates": {}, "total_rate": 0.0240},
    },
    "Pennsylvania": {
        "wage_base": {2026: 10000},
        "tax_codes": {
            "major": "39-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.03822, "minor_rates": {}, "total_rate": 0.03822},
        "jweg2": {"reporting": "client", "major_rate": 0.03822, "minor_rates": {}, "total_rate": 0.03822},
        "jweg3": {"reporting": "client", "major_rate": 0.03822, "minor_rates": {}, "total_rate": 0.03822},
    },
    "Rhode Island": {
        "wage_base": {2026: 30800},
        "tax_codes": {
            "major": "40-459",
            "minors": [{"code": "40-461", "name": "Job Development Assessment"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"40-461": 0.0021}, "total_rate": 0.0121},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"40-461": 0.0021}, "total_rate": 0.0121},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"40-461": 0.0021}, "total_rate": 0.0121},
    },
    "South Carolina": {
        "wage_base": {2026: 14000},
        "tax_codes": {
            "major": "41-459",
            "minors": [{"code": "41-461", "name": "Contingency Assessment Tax"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"41-461": 0.0006}, "total_rate": 0.0106},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"41-461": 0.0006}, "total_rate": 0.0106},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"41-461": 0.0006}, "total_rate": 0.0106},
    },
    "South Dakota": {
        "wage_base": {2026: 15000},
        "tax_codes": {
            "major": "42-459",
            "minors": [
                {"code": "42-461", "name": "Investment Fee"},
                {"code": "SD0000-148", "name": "Administrative Fee"},
            ],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {"42-461": 0.0055, "SD0000-148": 0.0008}, "total_rate": 0.0183},
        "jweg2": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {"42-461": 0.0055, "SD0000-148": 0.0008}, "total_rate": 0.0183},
        "jweg3": {"reporting": "client", "major_rate": 0.0120, "minor_rates": {"42-461": 0.0055, "SD0000-148": 0.0008}, "total_rate": 0.0183},
    },
    "Tennessee": {
        "wage_base": {2026: 7000},
        "tax_codes": {
            "major": "43-459",
            "minors": [],
        },
        "effective_date": "Jul 1, 2025 to Jun 30, 2026",
        "jweg1": {"reporting": "hybrid", "major_rate": 0.0230, "minor_rates": {}, "total_rate": 0.0230},
        "jweg2": {"reporting": "hybrid", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg3": {"reporting": "hybrid", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
    },
    "Texas": {
        "wage_base": {2026: 9000},
        "tax_codes": {
            "major": "44-459",
            "minors": [
                {"code": "44-461", "name": "Obligation Assessment Tax"},
                {"code": "44-463", "name": "Employment & Training Assessment"},
            ],
            "note": "Vertex & MTAX include Replenishment Tax Rate of 0.21% in major rate",
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0601, "minor_rates": {"44-461": 0.0001, "44-463": 0.0010}, "total_rate": 0.0612},
        "jweg2": {"reporting": "peo", "major_rate": 0.0061, "minor_rates": {"44-461": 0.0001, "44-463": 0.0010}, "total_rate": 0.0072},
        "jweg3": {"reporting": "peo", "major_rate": 0.0259, "minor_rates": {"44-461": 0.0001, "44-463": 0.0010}, "total_rate": 0.0270},
    },
    "Utah": {
        "wage_base": {2026: 50700},
        "tax_codes": {
            "major": "45-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0110, "minor_rates": {}, "total_rate": 0.0110},
        "jweg2": {"reporting": "peo", "major_rate": 0.0010, "minor_rates": {}, "total_rate": 0.0010},
        "jweg3": {"reporting": "peo", "major_rate": 0.0120, "minor_rates": {}, "total_rate": 0.0120},
    },
    "Vermont": {
        "wage_base": {2026: 15400},
        "tax_codes": {
            "major": "46-459",
            "minors": [],
        },
        "effective_date": "Jul 1, 2025 to Jun 30, 2026",
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {}, "total_rate": 0.0100},
    },
    "Virginia": {
        "wage_base": {2026: 8000},
        "tax_codes": {
            "major": "47-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0195, "minor_rates": {}, "total_rate": 0.0195},
        "jweg2": {"reporting": "peo", "major_rate": 0.0015, "minor_rates": {}, "total_rate": 0.0015},
        "jweg3": {"reporting": "peo", "major_rate": 0.0250, "minor_rates": {}, "total_rate": 0.0250},
    },
    "Washington": {
        "wage_base": {2026: 78200},
        "tax_codes": {
            "major": "48-459",
            "minors": [{"code": "48-461", "name": "Employment Administration Fund"}],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"48-461": 0.0002}, "total_rate": 0.0102},
        "jweg2": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"48-461": 0.0002}, "total_rate": 0.0102},
        "jweg3": {"reporting": "client", "major_rate": 0.0100, "minor_rates": {"48-461": 0.0002}, "total_rate": 0.0102},
    },
    "West Virginia": {
        "wage_base": {2026: 9500},
        "tax_codes": {
            "major": "49-459",
            "minors": [],
        },
        "jweg1": {"reporting": "peo", "major_rate": 0.0390, "minor_rates": {}, "total_rate": 0.0390},
        "jweg2": {"reporting": "peo", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
        "jweg3": {"reporting": "peo", "major_rate": 0.0270, "minor_rates": {}, "total_rate": 0.0270},
    },
    "Wisconsin": {
        "wage_base": {2026: 14000},
        "tax_codes": {
            "major": "50-459",
            "minors": [],
        },
        "jweg1": {"reporting": "client", "major_rate": 0.0305, "minor_rates": {}, "total_rate": 0.0305},
        "jweg2": {"reporting": "client", "major_rate": 0.0305, "minor_rates": {}, "total_rate": 0.0305},
        "jweg3": {"reporting": "client", "major_rate": 0.0305, "minor_rates": {}, "total_rate": 0.0305},
    },
    "Wyoming": {
        "wage_base": {2026: 33800},
        "tax_codes": {
            "major": "51-459",
            "minors": [
                {"code": "51-461", "name": "Employment Support Fund"},
                {"code": "WY0000-018", "name": "Workforce Development Training Fund"},
            ],
        },
        "jweg1": {"reporting": "hybrid", "major_rate": 0.01560, "minor_rates": {"51-461": 0.00060, "WY0000-018": 0.00020}, "total_rate": 0.01640},
        "jweg2": {"reporting": "hybrid", "major_rate": 0.00020, "minor_rates": {"51-461": 0.00060, "WY0000-018": 0.00020}, "total_rate": 0.00100},
        "jweg3": {"reporting": "hybrid", "major_rate": 0.01020, "minor_rates": {"51-461": 0.00060, "WY0000-018": 0.00020}, "total_rate": 0.01100},
    },
}


def get_sui_total_rate(state, jweg):
    """Get the total SUI rate (major + all minors) for a state and JWEG.

    Args:
        state: State name (e.g. "New York")
        jweg: "jweg1", "jweg2", or "jweg3"

    Returns: total rate as decimal (e.g. 0.04), or 0.0 if not found.
    """
    cfg = SUI_CONFIG.get(state, {}).get(jweg, {})
    return cfg.get("total_rate", 0.0)


def get_sui_reporting(state, jweg):
    """Get reporting type for a state/JWEG. Returns 'peo', 'client', or 'hybrid'."""
    cfg = SUI_CONFIG.get(state, {}).get(jweg, {})
    return cfg.get("reporting", "")


def get_sui_wage_base(state, year=2026):
    """Get SUI wage base for a state and year."""
    return SUI_CONFIG.get(state, {}).get("wage_base", {}).get(year, 0)


def get_sui_major_code(state):
    """Get the major SUI tax code for a state (the -459 code)."""
    return SUI_CONFIG.get(state, {}).get("tax_codes", {}).get("major", "")


def get_sui_minor_codes(state):
    """Get list of minor SUI code dicts for a state."""
    return SUI_CONFIG.get(state, {}).get("tax_codes", {}).get("minors", [])


def get_all_sui_codes(state):
    """Get all SUI-related tax codes for a state (major + minors)."""
    codes = []
    tc = SUI_CONFIG.get(state, {}).get("tax_codes", {})
    if tc.get("major"):
        codes.append(tc["major"])
    for m in tc.get("minors", []):
        codes.append(m["code"])
    return codes


def states_needing_refund_for_jweg(jweg):
    """Return list of states where reporting is 'client' or 'hybrid' for given JWEG."""
    result = []
    for state, cfg in SUI_CONFIG.items():
        reporting = cfg.get(jweg, {}).get("reporting", "")
        if reporting in ("client", "hybrid"):
            result.append(state)
    return sorted(result)
