"""Payout readiness check for installer projects.

A concept prototype with invented data. Every project is checked at one of
two moments and ends up in one of three outcomes:

    READY             everything is present and consistent, continue without a human
    INSTALLER_ACTION  something is missing, the installer gets one message listing it all
    OPS_REVIEW        something is off, a person decides before any money moves

Rules marked "MY RULE" come from my own experience at kloeckner.i.
Principle: don't try to make every small detail match. Amounts and sizes get a
tolerance; only what really matters (amount above the contract, address,
bank account, duplicates) is strict.
"""
from dataclasses import dataclass, field
from datetime import date

READY = "READY"
INSTALLER_ACTION = "INSTALLER_ACTION"
OPS_REVIEW = "OPS_REVIEW"

INVOICE_LOWER_TOLERANCE = 0.05   # invoice may be up to 5% below the financed amount
KWP_TOLERANCE = 0.10             # installed size may differ from financed size by 10%
PHOTO_MINIMUM = 10               # proof of the job, and future training data for photo checks
TYPICAL_EUR_PER_KWP = 2150       # placeholder from the sample data, to be replaced with real project data
PRICE_FLAG_MULTIPLE = 2          # a quote above 2x the typical price per kWp is probably a typo
DEMO_DATE = date(2026, 11, 4)    # fixed "today" so the demo always shows the same results


@dataclass
class Issue:
    severity: str          # "action" (installer must send something) or "review" (a person decides)
    text: str
    ask: str | None = None  # what to ask the installer for, used in the message


@dataclass
class Result:
    outcome: str
    issues: list[Issue] = field(default_factory=list)
    message: str = ""


def check(project: dict, all_projects: list[dict], today: date = DEMO_DATE) -> Result:
    """Check one project. `all_projects` is used for duplicate checks."""
    if project["gate"] == "financing":
        issues = _before_financing(project, all_projects)
    else:
        issues = _before_payout(project, all_projects, today)

    if any(i.severity == "review" for i in issues):
        outcome = OPS_REVIEW          # anything off wins, even if documents are also missing
    elif issues:
        outcome = INSTALLER_ACTION
    else:
        outcome = READY
    message = _installer_message(project, issues) if outcome == INSTALLER_ACTION else ""
    return Result(outcome, issues, message)


def _before_financing(p: dict, all_projects: list[dict]) -> list[Issue]:
    issues = []
    if not p.get("quote_doc"):
        issues.append(Issue("action", "Signed quote is missing", "the signed quote"))
    if not p.get("assessment"):
        issues.append(Issue("action", "Site assessment is missing", "the site assessment"))

    if p["requested"] > p["quote"]:
        issues.append(Issue("review", f"Requested {eur(p['requested'])} is {eur(p['requested'] - p['quote'])} more than the quote"))

    if p.get("kwp"):
        per_kwp = p["quote"] / p["kwp"]
        if per_kwp > TYPICAL_EUR_PER_KWP * PRICE_FLAG_MULTIPLE:
            issues.append(Issue("review", f"{eur(per_kwp)}/kWp is {per_kwp / TYPICAL_EUR_PER_KWP:.1f}x the typical {eur(TYPICAL_EUR_PER_KWP)}/kWp. Typo in the price or the size?"))

    # Cloover works in Germany (5-digit postcodes) and Austria (4-digit postcodes)
    digits = 4 if p["country"] == "AT" else 5
    postcode = str(p.get("postcode") or "")
    if not (postcode.isdigit() and len(postcode) == digits):
        country = "Austrian (4 digits)" if p["country"] == "AT" else "German (5 digits)"
        issues.append(Issue("review", f'Postcode "{postcode}" is not a valid {country} postcode'))

    # MY RULE: the same homeowner asking twice for the same product could be a second property, or a duplicate
    twins = [o["id"] for o in all_projects
             if o["id"] != p["id"] and o["gate"] == "financing"
             and o["homeowner"] == p["homeowner"] and o["product"] == p["product"]]
    if twins:
        issues.append(Issue("review", f"{p['homeowner']} already has an open {p['product']} request ({', '.join(twins)}). Second property, or a duplicate?"))
    return issues


def _before_payout(p: dict, all_projects: list[dict], today: date) -> list[Issue]:
    issues = []
    if not p.get("cert"):
        issues.append(Issue("action", "Signed completion certificate is missing", "the signed completion certificate"))
    photos = p.get("photos") or 0
    if photos < PHOTO_MINIMUM:
        missing = PHOTO_MINIMUM - photos
        issues.append(Issue("action", f"{photos} installation photos ({PHOTO_MINIMUM} needed)", f"{missing} more installation photo{'s' if missing > 1 else ''}"))
    if not p.get("invoice"):
        issues.append(Issue("action", "Final invoice is missing", "the final invoice"))

    if p.get("invoice"):
        difference = p["invoice"] - p["financed"]
        if difference > 0:
            # extra costs can be real (work found on site, transport), but a person confirms them
            issues.append(Issue("review", f"Invoice is {eur(difference)} above the financed {eur(p['financed'])}. Ask the installer why (extra work found on site, transport) before deciding"))
        elif -difference / p["financed"] > INVOICE_LOWER_TOLERANCE:
            issues.append(Issue("review", f"Invoice is {-difference / p['financed']:.0%} below the financed amount. Scope changed? Adjust the loan before payout"))

    if p.get("kwp") and p.get("installed_kwp") is not None:
        if abs(p["installed_kwp"] - p["kwp"]) / p["kwp"] > KWP_TOLERANCE:
            issues.append(Issue("review", f"Installed {p['installed_kwp']:g} kWp vs financed {p['kwp']:g} kWp: fewer panels than the homeowner is paying for"))
    if p.get("battery_kwh") and not p.get("installed_battery_kwh"):
        issues.append(Issue("review", f"Battery ({p['battery_kwh']:g} kWh) was financed but not installed"))

    # MY RULE: at kloeckner.i, purchase orders often had a different delivery address from the requesting site
    if _normalise(p.get("site_address")) != _normalise(p.get("install_address")):
        issues.append(Issue("review", f"Completion certificate says {p['install_address']}, but financing was for {p['site_address']}"))

    # MY RULE: money must go to the installer's registered account
    if p.get("account") != p.get("registered_account"):
        issues.append(Issue("review", f"Invoice asks for payment to account ending {p['account']}, but the installer's registered account ends {p['registered_account']}"))

    # MY RULE: dates out of order usually mean an error
    if p["install_date"] < p["contract_date"]:
        issues.append(Issue("review", "Install date is before the contract was signed"))
    if p["install_date"] > today:
        issues.append(Issue("review", f"Install date {p['install_date']} is in the future"))
    if p.get("invoice_date") and p["invoice_date"] < p["install_date"]:
        issues.append(Issue("review", f"Final invoice is dated {p['invoice_date']}, before the installation on {p['install_date']}"))

    # never pay twice for the same job
    duplicates = [o["id"] for o in all_projects if o["id"] != p["id"] and o.get("invoice_no") and o.get("invoice_no") == p.get("invoice_no")]
    if duplicates:
        issues.append(Issue("review", f"Invoice number {p['invoice_no']} is also used on {', '.join(duplicates)}. Risk of paying twice"))
    return issues


def _installer_message(p: dict, issues: list[Issue]) -> str:
    asks = [i.ask for i in issues if i.ask]
    items = asks[0] if len(asks) == 1 else ", ".join(asks[:-1]) + " and " + asks[-1]
    stage = "payout" if p["gate"] == "payout" else "financing"
    return (f"Hi {p['installer']}, project {p['id']} is almost ready for {stage}. "
            f"Please upload {items}. As soon as {'they arrive' if len(asks) > 1 else 'it arrives'}, we'll continue automatically.")


def _normalise(address: str | None) -> str:
    return " ".join((address or "").lower().split())


def eur(amount: float) -> str:
    return f"{amount:,.0f} €".replace(",", ".")
