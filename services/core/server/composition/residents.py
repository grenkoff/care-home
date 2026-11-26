"""Objects of residents, built for the composition root."""

import punq

from server.apps.accounts.public.accounts import Accounts
from server.apps.residents.infra import families, relatives
from server.apps.residents.logic.usecases import find_relative, list_family


def inject(container: punq.Container, accounts: Accounts) -> None:
    """Registers the objects of residents with the facade of accounts."""
    container.register(
        find_relative.FindRelative,
        instance=find_relative.FindRelative(relatives.CopiedRelatives()),
    )
    container.register(
        list_family.ListFamily,
        instance=list_family.ListFamily(families.StoredFamilies()),
    )
