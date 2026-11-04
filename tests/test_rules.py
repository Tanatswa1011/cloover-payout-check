import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data import load_projects  # noqa: E402
from edge_cases import CASES  # noqa: E402
from rules import INSTALLER_ACTION, OPS_REVIEW, READY, check  # noqa: E402


@pytest.mark.parametrize("name, project, expected, others", CASES, ids=[c[0] for c in CASES])
def test_edge_case(name, project, expected, others):
    assert check(project, [project, *others]).outcome == expected


def test_installer_gets_one_message_listing_everything():
    project = {**CASES[0][1], "cert": False, "photos": 8}
    result = check(project, [project])
    assert result.outcome == INSTALLER_ACTION
    assert "completion certificate" in result.message and "2 more installation photos" in result.message


def test_sample_data_outcomes():
    projects = load_projects()
    outcomes = {p["id"]: check(p, projects).outcome for p in projects}
    assert [i for i, o in outcomes.items() if o == READY] == ["F-201", "F-204", "P-308", "P-310"]
    assert outcomes["P-311"] == OPS_REVIEW  # address mismatch
    assert outcomes["P-312"] == OPS_REVIEW  # unregistered bank account
    assert outcomes["P-302"] == INSTALLER_ACTION  # missing completion certificate
