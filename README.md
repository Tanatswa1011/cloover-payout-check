# Payout Readiness Check

A product concept for Cloover's installer flow, by Tanatswa Phil Muganga. It uses **invented data** and is **not affiliated with Cloover**.

Cloover pays installers after a successful installation. This prototype checks every project at two moments, before financing and before payout, and gives each one of three outcomes:

| Outcome | Meaning |
|---|---|
| **Ready** | Everything is present and consistent. Continue without a human. |
| **Installer action** | Something is missing. The installer gets one message listing all of it. |
| **Ops review** | Something is off. A person decides before any money moves. |

## Files
- `rules.py`: every check, in plain Python. Rules marked `MY RULE` come from my experience at kloeckner.i.
- `edge_cases.py`: 23 edge cases. The test suite and the app's Tests tab both use them.
- `tests/test_rules.py`: the pytest suite.
- `sample_projects.csv`: 21 invented projects.
- `app.py`: the Streamlit app.

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
pytest
streamlit run app.py
```

## How it was made
I chose the problem, the flow and the rules, and changed them after reviewing the first version. [Claude Code](https://claude.com/claude-code) wrote the code. Every rule is a hypothesis to validate with the Cloover team.
