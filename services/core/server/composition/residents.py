"""Objects of residents, built for the composition root."""

import punq

from server.apps.residents.infra import families, kin, relatives
from server.apps.residents.logic.usecases import find_relative, list_family
from server.apps.residents.public.kin import Kin


def inject(container: punq.Container) -> Kin:
    """Registers the objects of residents and returns their facade for others."""
    container.register(
        find_relative.FindRelative,
        instance=find_relative.FindRelative(relatives.CopiedRelatives()),
    )
    container.register(
        list_family.ListFamily,
        instance=list_family.ListFamily(families.StoredFamilies()),
    )
    return kin.StoredKin()
