import bcrypt
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.models.discussion import Discussion
from src.models.organization import Organization
from src.models.ticket import Ticket
from src.models.user import User


def hash_fast(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()


async def make_organization(session: AsyncSession, name: str = "Excellence") -> Organization:
    organization = Organization(name=name)
    session.add(organization)
    await session.flush()
    return organization


async def make_user(
    session: AsyncSession,
    organization: Organization,
    *,
    email: str = "op1@excellence.qai.local",
    name: str = "Operator One",
    role: str = "operator",
    password: str = "password",
) -> User:
    user = User(
        email=email,
        password_hash=hash_fast(password),
        name=name,
        organization_id=organization.id,
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


async def make_ticket(
    session: AsyncSession,
    organization: Organization,
    *,
    title: str = "VPN drops during standup",
    status: int = 1,
    priority: int = 3,
    description: str = "Summary of the ticket.",
    contents: str = "The client wrote this.",
    submitted_by: str = "client@example.com",
    updated_by: int | None = None,
    date_deleted=None,
) -> Ticket:
    ticket = Ticket(
        organization_id=organization.id,
        status=status,
        priority=priority,
        title=title,
        description=description,
        contents=contents,
        submitted_by=submitted_by,
        updated_by=updated_by,
        date_deleted=date_deleted,
    )
    session.add(ticket)
    await session.flush()
    return ticket


async def commit_operator(
    engine: AsyncEngine,
    *,
    email: str = "op1@excellence.qai.local",
    organization_name: str = "Excellence",
    role: str = "operator",
    name: str = "Operator One",
    password: str = "password",
) -> tuple[int, int]:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        organization = await make_organization(session, organization_name)
        user = await make_user(session, organization, email=email, name=name, role=role, password=password)
        await session.commit()
        return organization.id, user.id


async def make_discussion(
    session: AsyncSession,
    ticket: Ticket,
    user: User,
    contents: str = "A staff comment.",
) -> Discussion:
    discussion = Discussion(
        ticket_id=ticket.id,
        organization_id=ticket.organization_id,
        user_id=user.id,
        contents=contents,
    )
    session.add(discussion)
    await session.flush()
    return discussion
