from __future__ import annotations

import os

import pytest

from quote_assistant.adapter.confidentiality.adr0009 import (
    ADR_0009_RELATIVE,
    find_repo_file,
    parse_adr_0009_file,
    vendor_is_selected,
)

pytestmark = pytest.mark.vendor_contract


def test_供应商契约_输出满足提取端口():
    """Live vendor contract. Default CI excludes this marker.

    Run later by hand: `uv run pytest -m vendor_contract`
    Ticket 02 / ADR-0009 must be closed first. This test must not call a paid API
    while the ADR is still a template.
    """
    snapshot = parse_adr_0009_file(find_repo_file(*ADR_0009_RELATIVE.split("/")))
    if not vendor_is_selected(snapshot) or os.environ.get("QA_VENDOR_CONTRACT") != "1":
        pytest.skip(
            "票 02 未关闭或未设置 QA_VENDOR_CONTRACT=1；"
            "选定供应商后手工运行：uv run pytest -m vendor_contract"
        )
    raise AssertionError("票 02 已关闭但真实供应商契约尚未接入。不要在未接线前假装已跑通付费 API。")
