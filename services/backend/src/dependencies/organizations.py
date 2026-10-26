#!/usr/bin/env python3
# ******************************************************************************
# * @file    dependencies/organizations.py
# * @author  Simeon Marlokov
# * @brief   Organization context resolved by the auth middleware
# * @date    25.10.2026
# ******************************************************************************
from typing import Annotated

from fastapi import Depends, Request

from src.core.exceptions import UnauthorizedError
from src.core.organization import OrganizationContext


def get_organization_context(request: Request) -> OrganizationContext:
    organization = getattr(request.state, "organization", None)
    if not isinstance(organization, OrganizationContext):
        raise UnauthorizedError("Not authenticated")
    return organization


OrganizationDep = Annotated[OrganizationContext, Depends(get_organization_context)]
