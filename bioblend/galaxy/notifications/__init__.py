"""
Contains possible interaction dealing with Galaxy notifications.
"""

from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
)

from bioblend.galaxy.client import Client

if TYPE_CHECKING:
    from bioblend.galaxy import GalaxyInstance


class NotificationClient(Client):
    """
    This endpoint only works on Galaxy 23.1 or later.
    """

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
        :param message_notifications: Whether to receive message notifications

        :type push_notifications_message: bool
        :param push_notifications_message: Whether to receive push notifications
          in the browser for this category

        :type new_item_notifications: bool
        :param new_item_notifications: Whether to receive notification when
          someone shares item with you

        :type push_notifications_new_items: bool
        :param push_notifications_new_items: Whether to receive push
          notifications in the browser for this category

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

    def get_user_notifications(
        self,
        limit: Optional[int] = 20,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns the list of notifications associated with the user.
        Anonymous users cannot receive personal notifications,
        only broadcasted notifications.

        You can use the `limit` and `offset` parameters
        to paginate through the notifications.

        :type limit: int
        :param limit: Limits the amount of messages returned.

        :type offset: int
        :param offset: Skips the first ... messages.

        :rtype: list
        :return: All notifications of the user
        """
        params = {"limit": limit, "offset": offset}
        return self._get(params=params)

    def show_notification(
        self,
        notification_id: str,
    ) -> Dict[str, Any]:
        """
        Displays information about a notification received by the user.

        :type notification_id: str
        :param notification_id: ID of the notification

        :rtype: dict
        :return: The notification
        """
        url = self._make_url() + f"/{notification_id}"
        return self._get(url=url)

    def update_user_notification(
        self,
        notification_id: str,
        seen: bool,
        deleted: bool,
    ) -> str:
        """
        Updates the state of a notification received by the user.

        :type notification_id: str
        :param notification_id: ID of the notification

        :type seen: bool
        :param seen: Mark notification as seen. When set to true the field is
          set to the current datetime

        :type deleted: bool
        :param deleted: Mark notification as deleted

        :rtype: str
        :return: A verification that the update was successful
        """
        url = self._make_url(notification_id)
        payload = {"seen": seen, "deleted": deleted}

        # Returns a 204, so feedback for the user is manually created
        self._put(url=url, payload=payload)
        return "Notification successfully updated."

    def update_user_notifications(
        self,
        notification_ids: List[str],
        seen: bool,
        deleted: bool,
    ) -> Dict[str, int]:
        """
        Updates a list of notifications in a single request.

        :type notification_ids: list
        :param since: IDs of the messages, which are to be updated

        :type seen: bool
        :param seen: Mark the message as seen. When set to true the field is
          set to the current datetime

        :type delete: bool
        :param seen: Mark the message as deleted

        :rtype: dict
        :return: How many notifications got updated
        """

        # create the payload for updating the notifications
        payload = {
            "notification_ids": notification_ids,
            "changes": {"seen": seen, "deleted": deleted},
        }
        return self._put(payload=payload)

    def update_broadcasted_notification(
        self,
        notification_id: str,
        update_content: bool,
        source: Optional[str] = None,
        variant: Optional[Literal["info", "urgent", "warning"]] = None,
        subject: Optional[str] = None,
        message: Optional[str] = None,
        action_links: Optional[Dict[str, str]] = None,
        publication_time: Optional[datetime] = None,
        expiration_time: Optional[datetime] = None,
    ) -> str:
        """
        Updates the state of a broadcasted notification.

        :type notification_ids: str
        :param since: ID of the broadcast, which is to be updated

        :type update_content: bool
        :param update_content: Indicates if the content will be updated.
          If set to True, subject and message are required.

        :type source: str
        :param source: Source of the broadcast. Represents the agent that
          created the broadcast, e.g. 'galaxy' or 'admin'.

        :type variant: str
        :param variant: Variant of the broadcast. Represents the intent or
          relevance of the broadcast. Available variants:

          - 'info'
          - 'urgent'
          - 'warning'

        :type subject: str
        :param subject: Purpose of the broadcast, which is a part of the
          content of the message.

        :type action_links: dict
        :param action_links: Optional action links (buttons) to be displayed
          in the notification, which are a part of the content of the message.
          Keys must be the title of the links and the value must be the link.
          Links must be URLs, otherwise the request will not be accepted.

        :type message: str
        :param message: Message of the broadcast, which is a part of the
          content of the message.

        :type publication_time: datetime
        :param publication_time: Time when the broadcast was published.
          Broadcasts can be created and then published at a later time.
          Will default to the moment the broadcast is sent.

        :type expiration_time: datetime
        :param expiration_time: Time when the broadcast will expire.
          If not set, the broadcast will expire 6 months later.
          Expired broadcasts will be permanently deleted.

        :rtype: str
        :return: A verification that the update was successful
        """
        broadcast: Dict[str, Any] = {}
        content: Dict[str, Any] = {}

        # catch cases where nothing is set to be updated
        if not (update_content or source or variant or publication_time or expiration_time):
            raise ValueError("Please specify at least one value to update for notifications.")

        # catch case where content is not marked to be updated
        # but content input was given
        if not update_content and (subject or message or action_links):
            raise ValueError("Please set update_content to true to update the content.")
        if update_content:
            if not (subject and message):
                raise ValueError("If Content is to be updated, both subject and message must be specified.")
            content = {"category": "broadcast", "subject": subject, "message": message}
            if action_links:
                links = []
                for k, v in action_links.items():
                    if v[:7] != "http://" and v[:8] != "https://":
                        raise ValueError(f"Link {v} is not a valid URL.")
                    links.append({"action_name": k, "link": v})
                content["action_links"] = links
            broadcast["content"] = content
        if source:
            broadcast["source"] = source
        if variant:
            broadcast["variant"] = variant
        if expiration_time:
            broadcast["expiration_time"] = str(expiration_time)
        if publication_time:
            broadcast["publication_time"] = str(publication_time)
        url = self._make_url("broadcast") + f"/{notification_id}"
        self._put(payload=broadcast, url=url)
        return "Broadcast successfully updated"

    def get_broadcasted(
        self,
        notification_id: str,
    ) -> Dict[str, Any]:
        """
        Returns the information of a specific broadcasted notification.
        Only Admin users can access inactive notifications (scheduled or
        recently expired).

        :type notification_id: str
        :param notification_id: ID of the broadcasted message

        :rtype: dict
        :return: The broadcast
        """
        url = self._make_url("broadcast") + f"/{notification_id}"
        return self._get(url=url)

    def get_all_broadcasted(self) -> List[Dict[str, Any]]:
        """
        Returns all currently active broadcasted notifications.
        Only Admin users can access inactive notifications, which are
        scheduled or recently expired.

        :rtype: list
        :return: A list containing broadcasts
        """
        url = self._make_url("broadcast")
        return self._get(url=url)

    def send_notification(
        self,
        source: str,
        variant: Literal["info", "urgent", "warning"],
        subject: str,
        message: str,
        publication_time: Optional[datetime] = None,
        expiration_time: Optional[datetime] = None,
        user_ids: Optional[List[str]] = None,
        group_ids: Optional[List[str]] = None,
        role_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Sends a notification to a list of recipients (users, groups or roles).

        :type source: str
        :param source: Source of the notification. Represents the agent that
          created the notification, e.g. 'galaxy' or 'admin'.

        :type variant: message_variants
        :param variant: Variant of the notification. Represents the intent or
          relevance of the notification. Available variants:

          - 'info'
          - 'urgent'
          - 'warning'

        :type subject: str
        :param subject: Purpose of the notification

        :type message: str
        :param message: Actual content of the notification.

        :type publication_time: datetime
        :param publication_time: Time when the notification was published.
          Notifications can be created and then published at a later time.
          Will default to the moment the notification is sent.

        :type expiration_time: datetime
        :param expiration_time: Time when the notification will expire.
          If not set, the notification will expire 6 months later.
          Expired notifications will be permanently deleted.

        :type user_ids: List[str]
        :param user_ids: IDs of users to receive the notification.

        :type group_ids: List[str]
        :param group_ids: IDs of groups to receive the notification.

        :type role_ids: List[str]
        :param role_ids: IDs of roles to receive the notification.

        :rtype: dict
        :return: A summary of notification sent.
        """

        # validate the broadcast has receivers
        if user_ids == group_ids == role_ids == []:
            raise ValueError("The message has no recipients.")

        # create the payload
        recipients = {
            "user_ids": user_ids or [],
            "group_ids": group_ids or [],
            "role_ids": role_ids or [],
        }
        content = {
            "source": source,
            "variant": variant,
            "category": "message",
            "content": {
                "category": "message",
                "subject": subject,
                "message": message,
            },
        }
        if expiration_time:
            content["expiration_time"] = str(expiration_time)
        if publication_time:
            content["publication_time"] = str(publication_time)
        notification = {"recipients": recipients, "notification": content}
        return self._post(payload=notification)

    def delete_user_notification(
        self,
        notification_id: str,
    ) -> str:
        """
        Deletes a notification received by the user.

        When a notification is deleted, it is not immediately removed
        from the database, but marked as deleted.

        - It will not be returned in the list of notifications,
          but admins can still access it as long as it is not expired.
        - It will be eventually removed from the database by a background task
          after the expiration time.
        - Deleted notifications will be permanently deleted when the
          expiration time is reached even if they were marked as favorite.

        :type notification_id: str
        :param notification_id: ID of the notification

        :rtype: str
        :return: A verification that the deletion was successful
        """
        url = self._make_url(notification_id)
        self._delete(url=url)
        return "Notification successfully deleted."

    def delete_user_notifications(
        self,
        notification_ids: List[str],
    ) -> Dict[str, int]:
        """
        Deletes a list of notifications in a single request.

        When a notification is deleted, it is not immediately removed from the
        database, but marked as deleted.

        - It will not be returned in the list of notifications, but admins can
          still access it as long as it is not expired.
        - It will be eventually removed from the database by a background task
          after the expiration time.
        - Deleted notifications will be permanently deleted when the
          expiration time is reached even if they were marked as favorite.

        :type notification_ids: list
        :param since: IDs of the messages, which are to be deleted

        :rtype: dict
        :return: How many notifications got deleted
        """
        payload = {
            "notification_ids": notification_ids,
        }
        url = self._make_url()
        return self._delete(url=url, payload=payload)

    def broadcast_notification(
        self,
        source: str,
        variant: Literal["info", "urgent", "warning"],
        subject: str,
        message: str,
        action_links: Optional[Dict[str, str]] = None,
        publication_time: Optional[datetime] = None,
        expiration_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Broadcasts a notification to every user in the system.

        Broadcasted notifications are a special kind of notification that are
        always accessible to all users, including anonymous users.
        They are typically used to display important information such as:

        - maintenance
        - windows
        - new features.

        These notifications are displayed differently from regular
        notifications, usually in a banner at the top or bottom of the page.

        Broadcasted notifications can include action links that are displayed
        as buttons.
        This allows users to easily perform tasks such as filling out surveys,
        accepting legal agreements or accessing new tutorials.

        Some key features of broadcasted notifications include:

        - They are not associated with a specific user, so they cannot be
          deleted or marked as read.
        - They can be scheduled to be displayed in the future or to expire
          after a certain time.
        - By default, broadcasted notifications are published immediately and
          expire six months after publication.
        - Only admins can create, edit, reschedule, or expire broadcasted
          notifications as needed.

        :type source: str
        :param source: Source of the broadcast. Represents the agent that
          created the broadcast, e.g. 'galaxy' or 'admin'.

        :type variant: str
        :param variant: Variant of the broadcast. Represents the intent or
          relevance of the broadcast. Available variants:

          - 'info'
          - 'urgent'
          - 'warning'

        :type subject: str
        :param subject: Purpose of the broadcast

        :type message: str
        :param message: Actual content of the broadcast.

        :type action_links: dict
        :param action_links: Optional action links (buttons) to be displayed
          in the notification. Keys must be the title of the links and the value
          must be the link. Links must be URLs, otherwise the request will not
          be accepted.

        :type publication_time: datetime
        :param publication_time: Time when the broadcast was published.
          Notifications can be created and then published at a later time.
          Will default to the moment the broadcast is sent.

        :type expiration_time: datetime
        :param expiration_time: Time when the broadcast will expire.
          If not set, the broadcast will expire 6 months later.
          Expired broadcast will be permanently deleted.

        :rtype: dict
        :return: A Summary of the broadcast sent.
        """
        broadcast: Dict[str, Any] = {}
        content: Dict[str, Any] = {"category": "broadcast", "subject": subject, "message": message}

        # format the action links(if there are any) for the payload
        if action_links:
            links = []
            for k, v in action_links.items():
                # make sure the links are valid URLs
                if v[:7] != "http://" and v[:8] != "https://":
                    raise ValueError(f"Link {v} is not a valid URL.")
                links.append({"action_name": k, "link": v})
            content["action_links"] = links

        # create the payload
        broadcast["content"] = content
        broadcast = {
            "source": source,
            "variant": variant,
            "category": "broadcast",
            "content": content,
        }
        if expiration_time:
            broadcast["expiration_time"] = str(expiration_time)
        if publication_time:
            broadcast["publication_time"] = str(publication_time)
        url = self._make_url("broadcast")
        return self._post(payload=broadcast, url=url)
