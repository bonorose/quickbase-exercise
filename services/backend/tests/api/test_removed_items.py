import pytest
from tests.factories import commit_operator
from tests.helpers.auth import auth_header

pytestmark = pytest.mark.api


async def test_items_route_is_gone(client, owner_engine):
    assert (await client.get("/api/v1/items")).status_code == 401
    await commit_operator(owner_engine)
    headers = await auth_header(client, "op1@excellence.qai.local")
    assert (await client.get("/api/v1/items", headers=headers)).status_code == 404
