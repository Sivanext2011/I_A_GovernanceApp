"""Department classification logic for all datasets."""

MAPPING_DEPT_MAP = {
    "BCSS BOS SER SL BOS IN BE Billing": "Billing",
    "BCSS BOS SER SL BOS Monetization": "Charging",
    "BCSS BOS SER SL BOS Monetization EC1": "Charging",
    "BCSS BOS SER SL BOS Monetization EC2": "Charging",
    "BCSS BOS SER SL BOS Monetization EC3": "Charging",
    "BCSS BOS SER SL BOS MonetizationECEV": "Charging",
    "BCSS BOS SER SL BOS SDC Billing&MW": "SDC Billing&MW",
    "BCSS BOS SER SL BOS SDC CS&DFE": "SDC CS&DFE",
}

SAVINGS_L5_MAP = {
    "BCSS SD BOS SDU BOS IN BE Billing": "Billing",
    "BCSS SD BOS SDU BOS SDC Billing&MW": "SDC Billing&MW",
    "BCSS SD BOS SDU BOS SDC CS&DFE": "SDC CS&DFE",
    "BCSS SD BOS SDU SL BOS Monetization EC1": "Charging",
    "BCSS SD BOS SDU SL BOS Monetization EC2": "Charging",
    "BCSS SD BOS SDU SL BOS Monetization EC3": "Charging",
    "BCSS SD BOS SDU SL BOS MonetizationECEV": "Charging",
}

SAVINGS_L6_MAP = {
    "BCSS BOS SER SL BOS IN BE Billing": "Billing",
    "BCSS BOS SER SL BOS Monetization EC1": "Charging",
    "BCSS BOS SER SL BOS Monetization EC2": "Charging",
    "BCSS BOS SER SL BOS Monetization EC3": "Charging",
    "BCSS BOS SER SL BOS MonetizationECEV": "Charging",
    "BCSS BOS SER SL BOS SDC Billing&MW": "SDC Billing&MW",
    "BCSS BOS SER SL BOS SDC CS&DFE": "SDC CS&DFE",
}

TEAMS = ["Overall", "Billing", "Charging", "SDC Billing&MW", "SDC CS&DFE"]


def classify_mapping_dept(level6: str) -> str:
    if not level6:
        return "Unknown"
    return MAPPING_DEPT_MAP.get(str(level6).strip(), "Unknown")


def classify_savings_download_dept(l4org: str, l5org: str, l6org: str) -> str:
    l4 = str(l4org).strip() if l4org else ""
    l5 = str(l5org).strip() if l5org else ""
    l6 = str(l6org).strip() if l6org else ""

    # Logic Type 1
    if l4 == "BCSS SD BOS SDU SL BOS Monetization":
        result = SAVINGS_L5_MAP.get(l5, None)
        if result:
            return result

    # Logic Type 2
    if l5 == "BCSS BOS SER SL BOS Monetization":
        result = SAVINGS_L6_MAP.get(l6, None)
        if result:
            return result

    return "Unknown"
