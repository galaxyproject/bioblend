from datetime import datetime

from . import GalaxyTestBase


class TestGalaxyNotifications(GalaxyTestBase.GalaxyTestBase):
    def test_empty_notification_status(self):
        status = self.gi.notifications.get_notification_status(datetime.utcnow())
        # check the datatype
        assert type(status["total_unread_count"]) == int
        assert type(status["broadcasts"]) == list
        assert type(status["notifications"]) == list
        # check if the notification is really empty
        assert status["total_unread_count"] == 0
        assert status["broadcasts"] == []
        assert status["notifications"] == []
