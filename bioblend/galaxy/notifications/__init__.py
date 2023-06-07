"""
Contains possible interaction dealing with Galaxy notifications.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
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

    def get_notification_status(
        self, year: int, month: int, day: int, hour: int, minute: Optional[int] = None, second: Optional[int] = None
    ) -> Dict[str, Union[int, List[Any]]]:
        """
        Fetches the current status summary of the user's notifications
        since a particular date.

        :type since: datetime
        :param since: Retrieval of the notifications starts from this point in time

        :type year: int
        :param year: Retrieval of the notifications starts from this year

        :type month: int
        :param month: Retrieval of the notifications starts from this month

        :type day: int
        :param day: Retrieval of the notifications starts from this day

        :type hour: int
        :param hour: Retrieval of the notifications starts from this hour

        :type minute: int
        :param minute: Retrieval of the notifications starts from this minute. Defaults to 0

        :type second: int
        :param second: Retrieval of the notifications starts from this second. Defaults to 0

        :return: A dictionary containing the current status summary of notifications.
        :rtype: dict
        """
        minute = minute or 0
        second = second or 0
        try:
            # Construct the datetime object based on the provided inputs
            since = datetime(year, month, day, hour, minute, second)
        except ValueError as e:
            # Handle the conversion error
            raise ValueError("Invalid date and time inputs.") from e
        url = self._make_url() + f"/status?since={since}"
        return self._get(url=url)
