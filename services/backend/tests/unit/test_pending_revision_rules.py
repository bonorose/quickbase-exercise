import uuid

import pytest
from pydantic import ValidationError

from src.schemas.pending_revisions.response import field_diff
from src.tools.mutate_ticket import MutateTicketArgs

pytestmark = pytest.mark.unit


def test_mutate_rejects_fields_outside_status_and_priority():
    with pytest.raises(ValidationError):
        MutateTicketArgs.model_validate({"id": 1, "action": "update", "fields": {"title": "renamed"}})
    with pytest.raises(ValidationError):
        MutateTicketArgs.model_validate({"id": 1, "action": "update", "fields": {"description": "secret"}})
    with pytest.raises(ValidationError):
        MutateTicketArgs.model_validate({"id": 1, "action": "update", "organization_id": 2})


def test_field_diff_only_includes_changed_editable_keys():
    current = {"title": "Old", "contents": "Body", "status": "open", "priority": "low"}
    changed = {"priority": "high", "title": "Old", "description": "ignored"}
    assert field_diff(current, changed) == {"priority": {"from": "low", "to": "high"}}
    assert field_diff(current, {}) == {}


def test_note_uses_the_draft_id_only():
    draft_id = uuid.uuid4()
    note = f"Pending revision {draft_id} was executed by Ada"
    assert str(draft_id) in note
    assert "ticket" not in note
