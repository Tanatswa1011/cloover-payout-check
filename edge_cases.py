"""Edge cases for the payout readiness check.

Shared by the pytest suite (tests/test_rules.py) and the Tests tab in the app,
so both always run exactly the same cases.
"""
from datetime import date

from rules import INSTALLER_ACTION, OPS_REVIEW, READY

BASE_PAYOUT = {
    "id": "T", "gate": "payout", "installer": "Test GmbH", "homeowner": "Test", "product": "Solar", "country": "DE",
    "kwp": 8.0, "installed_kwp": 8.0, "battery_kwh": None, "installed_battery_kwh": None,
    "financed": 16000.0, "invoice": 16000.0, "invoice_no": "T-1", "cert": True, "photos": 12,
    "site_address": "Weg 1, 10115", "install_address": "Weg 1, 10115", "account": "1111", "registered_account": "1111",
    "contract_date": date(2026, 10, 1), "install_date": date(2026, 10, 20), "invoice_date": date(2026, 10, 21),
}
BASE_FINANCING = {
    "id": "T", "gate": "financing", "installer": "Test GmbH", "homeowner": "Test", "product": "Solar", "country": "DE",
    "postcode": "10115", "kwp": 8.0, "quote": 16800.0, "requested": 16800.0, "quote_doc": True, "assessment": True,
}


def pay(**changes):
    return {**BASE_PAYOUT, **changes}


def fin(**changes):
    return {**BASE_FINANCING, **changes}


# (name, project, expected outcome, other open projects)
CASES = [
    ("Complete payout project is ready", pay(), READY, []),
    ("Invoice 4% below financed amount is still ready", pay(invoice=15360.0), READY, []),
    ("Invoice 6% below financed amount goes to review", pay(invoice=15040.0), OPS_REVIEW, []),
    ("Invoice 1 € above financed amount goes to review", pay(invoice=16001.0), OPS_REVIEW, []),
    ("Missing completion certificate asks the installer", pay(cert=False), INSTALLER_ACTION, []),
    ("Nine photos asks for one more", pay(photos=9), INSTALLER_ACTION, []),
    ("Exactly ten photos is enough", pay(photos=10), READY, []),
    ("Missing document plus a conflict is review, not action", pay(cert=False, invoice=17000.0), OPS_REVIEW, []),
    ("Financed battery not installed goes to review", pay(product="Solar + battery", battery_kwh=8.0, installed_battery_kwh=0.0), OPS_REVIEW, []),
    ("Installed kWp 9% smaller is ready", pay(installed_kwp=7.28), READY, []),
    ("Different install address goes to review", pay(install_address="Parkweg 19, 14482"), OPS_REVIEW, []),
    ("Same address in different letter case is ready", pay(install_address="weg 1,  10115"), READY, []),
    ("Payout to an unregistered account goes to review", pay(account="2222"), OPS_REVIEW, []),
    ("Invoice dated before installation goes to review", pay(invoice_date=date(2026, 10, 10)), OPS_REVIEW, []),
    ("Install date in the future goes to review", pay(install_date=date(2026, 12, 1), invoice_date=date(2026, 12, 1)), OPS_REVIEW, []),
    ("Same invoice number on two projects goes to review", pay(), OPS_REVIEW, [pay(id="T2")]),
    ("Austrian 4-digit postcode passes", fin(country="AT", postcode="6020"), READY, []),
    ("German 4-digit postcode goes to review", fin(postcode="8033"), OPS_REVIEW, []),
    ("Requested above quote goes to review", fin(requested=17000.0), OPS_REVIEW, []),
    ("Quote at 8,000 €/kWp goes to review", fin(quote=64000.0, requested=64000.0), OPS_REVIEW, []),
    ("Missing site assessment asks the installer", fin(assessment=False), INSTALLER_ACTION, []),
    ("Same homeowner with a second solar request goes to review", fin(), OPS_REVIEW, [fin(id="T2")]),
    ("Same homeowner with a different product is ready", fin(), READY, [fin(id="T2", product="Heat pump")]),
]
