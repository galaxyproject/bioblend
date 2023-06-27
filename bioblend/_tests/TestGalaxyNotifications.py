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
