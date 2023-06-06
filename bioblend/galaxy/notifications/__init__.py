"""
Contains possible interaction dealing with Galaxy notifications.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    TYPE_CHECKING,
    Union,
)

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class NotificationClient(Client):
    module = "notifications"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def get_notification_status(self, since: datetime) -> Dict[str, Union[int, List[Any]]]:
        """
        Returns the current status summary of the user's notifications
        since a particular date.
        :type since: datetime
        :param since: Retrieval of the notifications starts from this point in time
        :return: A dictionary containing the current status summary of notifications.
        :rtype: dict
        """
        url = self._make_url() + f"/status?since={since}"
        return self._get(url=url)
