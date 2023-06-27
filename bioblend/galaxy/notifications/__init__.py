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

    def get_notification_preferences(self) -> Dict[str, Any]:
        """
        Returns the current user's preferences for notifications.
        Anonymous users cannot have notification preferences.
        :rtype: dict
        :return: The notification preferences
        """
        url = self._make_url("preferences")
        return self._get(url=url)

    def update_notification_preferences(
        self,
        message_notifications: bool,
        push_notifications_message: bool,
        new_item_notifications: bool,
        push_notifications_new_items: bool,
    ) -> Dict[str, Any]:
        """
        Updates the user's notifications preferences.
        Enable/disable notifications for a particular type (category)
        or enable/disable a particular channel on each category.
        Channels available:
            - push notifications
        Anonymous users cannot have notification preferences.
        They will receive only broadcasted notifications.
        :type message_notifications: bool
        :param message_notifications: Receive message notifications
        :type push_notifications_message: bool
        :param push_notifications_message: Receive push notifications in the
        browser for this category
        :type new_item_notifications: bool
        :param new_item_notifications: Receive notification when someone
        shares item with you
        :type push_notifications_new_items: bool
        :param push_notifications_new_items: Receive push notifications in the
        browser for this category
        :rtype: dict
        :return: Notification preferences of the user.
        """
        url = self._make_url("preferences")

        # create the payload for updating the preferences
        payload = {
            "preferences": {
                "message": {"enabled": message_notifications, "channels": {"push": push_notifications_message}},
                "new_shared_item": {
                    "enabled": new_item_notifications,
                    "channels": {"push": push_notifications_new_items},
                },
            }
        }
        return self._put(url=url, payload=payload)
