from datetime import datetime

from . import (
    GalaxyTestBase,
    test_util,
)


class TestGalaxyNotifications(GalaxyTestBase.GalaxyTestBase):
    @test_util.skip_unless_galaxy("release_23.1")
    def test_empty_notification_status(self):
        if not self.gi.config.get_config()["enable_notification_system"]:
            self.skipTest("This Galaxy instance is not configured to use notifications.")

        # fetch the empty notification status
        now = datetime.utcnow()
        status = self.gi.notifications.get_notification_status(since=now)

        # check the datatype
        assert type(status["total_unread_count"]) == int
        assert type(status["broadcasts"]) == list
        assert type(status["notifications"]) == list

        # check if the notification is really empty
        assert status["total_unread_count"] == 0
        assert status["broadcasts"] == []
        assert status["notifications"] == []

    @test_util.skip_unless_galaxy("release_23.1")
    def test_notification_preferences(self):
        if not self.gi.config.get_config()["enable_notification_system"]:
            self.skipTest("This Galaxy instance is not configured to use notifications.")

        # the notification preferences, which should be set to true by default
        preferences = self.gi.notifications.get_notification_preferences()

        # notifications preferences for messages
        message_preferences = preferences["preferences"]["message"]
        assert message_preferences["enabled"] is True
        assert message_preferences["channels"]["push"] is True

        # notifications preferences for new shared items
        new_items_preferences = preferences["preferences"]["new_shared_item"]
        assert new_items_preferences["enabled"] is True
        assert new_items_preferences["channels"]["push"] is True

        # change preferences to False
        self.gi.notifications.update_notification_preferences(
            message_notifications=False,
            push_notifications_message=False,
            new_item_notifications=False,
            push_notifications_new_items=False,
        )

        # check the updated notification preferences
        preferences = self.gi.notifications.get_notification_preferences()
        message_preferences = preferences["preferences"]["message"]
        assert message_preferences["enabled"] is False
        assert message_preferences["channels"]["push"] is False
        new_items_preferences = preferences["preferences"]["new_shared_item"]
        assert new_items_preferences["enabled"] is False
        assert new_items_preferences["channels"]["push"] is False
