import pytest
from fastapi import Request

from src.core.exceptions import UnauthorizedError
from src.core.organization import OrganizationContext
from src.dependencies.organizations import get_organization_context
from src.models.ticket import Ticket
from src.repositories.ticket_repository import TicketRepository, escape_like

pytestmark = pytest.mark.unit


def test_escape_like_treats_wildcards_as_text():
    assert escape_like(r"100%_done") == r"100\%\_done"


def test_select_includes_organization_predicate():
    repository = TicketRepository(session=None, organization=OrganizationContext(3, 1, "operator"))
    compiled = str(repository._select().compile())
    assert "organization_id" in compiled
    assert "date_deleted" in compiled


async def test_create_and_update_reject_caller_organization_id():
    repository = TicketRepository(session=None, organization=OrganizationContext(3, 1, "operator"))
    with pytest.raises(ValueError):
        await repository.create(organization_id=9, title="x")
    with pytest.raises(ValueError):
        await repository.update(Ticket(title="x"), organization_id=9)


def test_organization_dependency_requires_middleware_state():
    request = Request({"type": "http", "headers": [], "method": "GET", "path": "/", "query_string": b""})
    with pytest.raises(UnauthorizedError):
        get_organization_context(request)
