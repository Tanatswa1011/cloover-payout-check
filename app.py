"""Streamlit app for the payout readiness check (concept prototype, invented data)."""
from datetime import date

import streamlit as st

from data import load_projects
from edge_cases import CASES
from rules import (DEMO_DATE, INSTALLER_ACTION, INVOICE_LOWER_TOLERANCE, KWP_TOLERANCE, OPS_REVIEW,
                   PHOTO_MINIMUM, READY, check, eur)

st.set_page_config(page_title="Payout Readiness Check", page_icon="✅", layout="wide")

LABELS = {READY: ":green-background[READY]", INSTALLER_ACTION: ":orange-background[INSTALLER ACTION]", OPS_REVIEW: ":red-background[OPS REVIEW]"}
ORDER = [READY, INSTALLER_ACTION, OPS_REVIEW]


@st.cache_data
def projects() -> list[dict]:
    return load_projects()


ALL = projects()

st.caption("PRODUCT CONCEPT · PREPARED FOR CLOOVER BY TANATSWA PHIL MUGANGA")
st.title("Is this project ready to pay out?")
st.write(
    "Cloover promises installers fast payout after a successful installation, and many installers are small "
    "businesses that depend on that cash flow. This prototype checks two moments in the project flow: before "
    "financing is requested, and before money is released. Every project ends up ready, waiting on the installer, "
    "or with ops for review."
)
steps = st.columns(5)
for col, (name, hint) in zip(steps, [("Plan", "Site assessment and quote"), ("Finance", "CHECK 1 · before financing"),
                                     ("Sign", "Digital contract"), ("Install", "Installer completes job"),
                                     ("Pay out", "CHECK 2 · before payout")]):
    with col.container(border=True):
        st.markdown(f"**{name}**  \n:{'blue' if 'CHECK' in hint else 'gray'}[{hint}]")
st.caption(
    f"All installers, homeowners, addresses, amounts and account numbers are invented. I haven't seen Cloover's internal "
    f"tools: the five steps come from Cloover's public website, and every rule is a hypothesis to check with the team. "
    f"Checked as of {DEMO_DATE:%d %b %Y} (fixed demo date)."
)


def show_result(project: dict, result) -> None:
    if result.issues:
        for issue in result.issues:
            who = ":orange[INSTALLER]" if issue.severity == "action" else ":red[OPS]"
            st.markdown(f"{who} {issue.text}")
    else:
        st.markdown(":green[OK] Complete and consistent. " + ("Release payout." if project["gate"] == "payout" else "Send to credit check."))
    if result.message:
        st.caption("Message to installer, written automatically")
        st.code(result.message, language=None, wrap_lines=True)


def facts(project: dict) -> dict:
    if project["gate"] == "financing":
        return {"Homeowner": project["homeowner"], "Country": project["country"], "Postcode": project["postcode"],
                "Size": f"{project['kwp']:g} kWp" if project.get("kwp") else "–", "Quote": eur(project["quote"]),
                "Requested": eur(project["requested"]), "Signed quote": "yes" if project["quote_doc"] else "no",
                "Site assessment": "yes" if project["assessment"] else "no"}
    return {"Homeowner": project["homeowner"], "Financed": eur(project["financed"]),
            "Invoice": eur(project["invoice"]) if project.get("invoice") else "–", "Invoice no.": project.get("invoice_no") or "–",
            "Financed site": project["site_address"], "Installed at": project["install_address"],
            "Payout account": f"…{project['account']} (registered …{project['registered_account']})",
            "Photos": project.get("photos"), "Completion cert.": "signed" if project.get("cert") else "missing",
            "Contract → install → invoice": f"{project['contract_date']} → {project['install_date']} → {project.get('invoice_date')}"}


queue, try_it, spec, tests, approach = st.tabs(["Queue", "Try a project", "Spec ticket", "Tests", "How I'd validate it"])

with queue:
    view = st.segmented_control("Show", ["All projects", "Before financing", "Before payout"], default="All projects")
    gate = {"Before financing": "financing", "Before payout": "payout"}.get(view)
    rows = [(p, check(p, ALL)) for p in ALL if gate is None or p["gate"] == gate]
    a, b, c = st.columns(3)
    a.metric("Ready, no human needed", sum(r.outcome == READY for _, r in rows))
    b.metric("Installer gets one message", sum(r.outcome == INSTALLER_ACTION for _, r in rows))
    c.metric("Ops decides", sum(r.outcome == OPS_REVIEW for _, r in rows))
    st.caption("This sample is deliberately packed with edge cases to show each rule. In real data, most projects should land in Ready; if they don't, a rule is too strict.")
    for project, result in sorted(rows, key=lambda x: (ORDER.index(x[1].outcome), x[0]["id"])):
        amount = project["invoice"] if project["gate"] == "payout" else project["requested"]
        stage = "payout" if project["gate"] == "payout" else "financing"
        with st.expander(f"{LABELS[result.outcome]} **{project['id']}** · {project['installer']} · {project['product']} · {stage} · {eur(amount)}"):
            cols = st.columns(4)
            for i, (k, v) in enumerate(facts(project).items()):
                cols[i % 4].markdown(f":gray[{k}]  \n`{v}`")
            show_result(project, result)

with try_it:
    st.subheader("Change a project and watch the result")
    choice = st.selectbox("Example project", [p["id"] for p in ALL], index=[p["id"] for p in ALL].index("P-311"),
                          format_func=lambda i: f"{i} · " + next(p["installer"] for p in ALL if p["id"] == i))
    base = dict(next(p for p in ALL if p["id"] == choice))
    left, right = st.columns(2)
    with left:
        if base["gate"] == "financing":
            base["homeowner"] = st.text_input("Homeowner", base["homeowner"])
            base["country"] = st.selectbox("Country", ["DE", "AT"], index=["DE", "AT"].index(base["country"]))
            base["postcode"] = st.text_input("Postcode", base["postcode"])
            base["kwp"] = st.number_input("Size (kWp, solar only)", value=base.get("kwp") or 0.0, step=0.1) or None
            base["quote"] = st.number_input("Quote (€)", value=base["quote"], step=100.0)
            base["requested"] = st.number_input("Requested (€)", value=base["requested"], step=100.0)
            base["quote_doc"] = st.checkbox("Signed quote uploaded", base["quote_doc"])
            base["assessment"] = st.checkbox("Site assessment done", base["assessment"])
        else:
            base["financed"] = st.number_input("Financed (€)", value=base["financed"], step=100.0)
            base["invoice"] = st.number_input("Invoice (€)", value=base["invoice"], step=100.0)
            base["invoice_no"] = st.text_input("Invoice number", base["invoice_no"])
            base["site_address"] = st.text_input("Financed site address", base["site_address"])
            base["install_address"] = st.text_input("Address on completion certificate", base["install_address"])
            base["account"] = st.text_input("Payout account (last 4 digits)", base["account"])
            base["registered_account"] = st.text_input("Registered account (last 4 digits)", base["registered_account"])
            if base.get("kwp"):
                base["installed_kwp"] = st.number_input("Installed size (kWp)", value=base["installed_kwp"], step=0.1)
            if base.get("battery_kwh"):
                base["installed_battery_kwh"] = st.number_input("Battery installed (kWh)", value=base.get("installed_battery_kwh") or 0.0, step=1.0)
            base["cert"] = st.checkbox("Completion certificate signed", base["cert"])
            base["photos"] = st.number_input("Installation photos", value=base["photos"], step=1, min_value=0)
            base["contract_date"] = st.date_input("Contract signed", base["contract_date"])
            base["install_date"] = st.date_input("Installed on", base["install_date"])
            base["invoice_date"] = st.date_input("Invoice date", base["invoice_date"])
    with right:
        result = check(base, [base if p["id"] == base["id"] else p for p in ALL])
        st.markdown(f"### {LABELS[result.outcome]}")
        show_result(base, result)

with spec:
    st.caption("TICKET · DRAFT")
    st.subheader("Payout readiness check for installer projects")
    st.markdown(f"""
**Problem (hypothesis).** Installers are paid after a successful installation. If documents are missing, or don't match
what was financed, someone has to notice, ask the installer and wait. That slows payouts for installers who depend on
them for cash flow. Catching errors before money moves also protects Cloover from paying the wrong amount, to the wrong
account, or twice.

**Users.** *Installer:* wants to be paid quickly and to know exactly what is missing, in one message.
*Ops / finance:* wants to release money only when the paperwork matches the contract, and to spend review time on real exceptions.

**Outcomes.** Ready (continue without a human) · Installer action (one message listing everything missing) · Ops review (a person decides; nothing is paid automatically).

**Principle: don't try to make every detail match.** When thousands of documents arrive in different formats, an exact
match on every field is impossible and floods the review queue. Amounts and sizes get a tolerance; only what really
matters is strict.
""")
    st.markdown("**Rules (v1).** Rules marked ✱ come from my own experience at kloeckner.i.")
    st.table({
        "Check": ["Before financing"] * 5 + ["Before payout"] * 8,
        "Rule": [
            "Signed quote and site assessment are uploaded",
            "Requested amount is not above the quote",
            "Price per kWp is under 2× the typical level",
            "Postcode has 5 digits in Germany, 4 in Austria",
            "✱ Same homeowner, same product, two open requests",
            f"✱ Completion certificate, final invoice and at least {PHOTO_MINIMUM} photos",
            "Invoice is not above the financed amount",
            f"Invoice is no more than {INVOICE_LOWER_TOLERANCE:.0%} below the financed amount",
            f"Installed kWp within {KWP_TOLERANCE:.0%} of financed; a financed battery is installed",
            "✱ Address on the completion certificate matches the financed site",
            "✱ Payout account matches the installer's registered account",
            "✱ Dates in order: contract → install → invoice, nothing in the future",
            "Invoice number is not used on another project",
        ],
        "Outcome": ["Installer action"] + ["Ops review"] * 4 + ["Installer action"] + ["Ops review"] * 7,
    })
    st.markdown("""
**Acceptance criteria.**
1. Every project shows exactly one outcome and the reasons behind it.
2. Installer messages list all missing items in one message.
3. A project with anything off is never ready, even if documents are also missing.
4. Austrian (4-digit) and German (5-digit) postcodes both pass.
5. An invoice up to 5% below the financed amount passes; above it never does.
6. All tests pass before release.

**Next versions.**
- *Quote check against past projects:* find the most similar past projects (product, size, region), compare price and line items in code, let AI explain the result with sources, and mark the quote go, review or stop. A person decides every stop.
- *Reading installer PDFs:* extract amounts, sizes, addresses and dates from quotes, invoices and certificates in many formats.
- *Photo checks:* look at the installation photos, not just count them. Needs labelled installation photos first; the 10-photo rule starts that dataset.

**How we'd know it works.** Time from quote through invoice verification to payout · share of payouts that needed document rework · review queue size, and how many reviews end with "nothing wrong".

**Open questions for the team.** Which documents are required per product, in Germany and Austria? What tolerance does finance already accept? Is 10 photos realistic on site? Where are completion documents uploaded?
""")

with tests:
    results = [(name, expected, check(project, [project, *others]).outcome) for name, project, expected, others in CASES]
    passed = sum(expected == got for _, expected, got in results)
    st.subheader(f"Edge cases: {passed} / {len(results)} passing")
    st.caption("The same cases run in the pytest suite in this repo (tests/test_rules.py). They run here on every page load.")
    for name, expected, got in results:
        mark = ":green[PASS]" if expected == got else ":red[FAIL]"
        st.markdown(f"{mark} {name} · :gray[expects {expected.replace('_', ' ').lower()}]")
    st.caption("The Austrian postcode case exists because the first version of this check marked 4-digit postcodes as errors. Cloover operates in Austria.")

with approach:
    st.subheader("How I'd validate this, and what I'd build first")
    st.markdown("""
1. **Check the assumption with the people who live it.** Talk to ops, finance and a few installers: what holds up a payout, which documents get sent back most, how long a rework round takes. If payouts rarely stall, I'd drop this.
2. **Measure the flow.** Time from quote to invoice verification to payout, the share needing rework, and the most common missing item.
3. **Ship the smallest useful piece.** The single message to installers listing everything missing.
4. **Then build the quote check** against similar past projects.

**What I learned at kloeckner.i that shaped these rules**
- A customer with two locations would send a request for quotation from one site and a purchase order with a completely different delivery address. That's why the address rule exists.
- PDFs came in different layouts, fonts and wording, and some were handwritten. Extraction is hardest where formats vary, which will be true for installer documents too.
- Never try to make every small detail match when processing thousands of documents. That's why amounts have tolerances.

**Related things I've built**
- *Photo checks:* I fine-tuned a YOLO11n object detector on BMW's public SORDI logistics dataset (not affiliated with BMW). On an untouched test split it reached mAP@0.50 of 0.79. Small objects stayed hard, which matters for spotting a battery or inverter in a busy installation photo.
- *Reading documents:* ContractGuard, a technical MVP that turns contract text into structured terms and pulls out key dates.

**How this prototype was made.** I chose the problem, the flow and the rules, and changed them after reviewing the first version: photos went from 3 to 10, and I added the address, bank account, invoice date and second-request checks. Claude Code wrote the code.
""")

st.divider()
st.caption("Tanatswa Phil Muganga · Berlin · tanaphil.com · Concept prototype built with Claude Code, using invented data. Not affiliated with Cloover.")
