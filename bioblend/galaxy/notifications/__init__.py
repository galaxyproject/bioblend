"""
Contains possible interaction dealing with Galaxy notifications.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    TYPE_CHECKING,
)

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class NotificationClient(Client):
    module = "notifications"

    def __init__(self, galaxy_instance: "GalaxyInstance") -> None:
        super().__init__(galaxy_instance)

    def get_notification_status(self, since: datetime) -> Dict[str, Any]:
        """
        Returns the current status summary of the user's notifications
        since a particular date.
        :type since: datetime
        :param since: Retrieval of the notifications starts from this point
        in time
        :rtype: dict
        :return: Current status summary of notifications.
        """
        url = self._make_url() + f"/status?since={since}"
        return self._get(url=url)
