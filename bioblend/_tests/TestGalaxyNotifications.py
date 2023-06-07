from datetime import datetime

import pytest

from . import GalaxyTestBase


class TestGalaxyNotifications(GalaxyTestBase.GalaxyTestBase):
    def test_empty_notification_status(self):
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        day = datetime.utcnow().day
        hour = datetime.utcnow().hour
        status = self.gi.notifications.get_notification_status(year=year, month=month, day=day, hour=hour)
        # check the datatype
        assert type(status["total_unread_count"]) == int
        assert type(status["broadcasts"]) == list
        assert type(status["notifications"]) == list
        # check if the notification is really empty
        assert status["total_unread_count"] == 0
        assert status["broadcasts"] == []
        assert status["notifications"] == []
        # check if incorrect gets processed correctly
        with pytest.raises(ValueError) as error_info:
            self.gi.notifications.get_notification_status(year=year, month=13, day=day, hour=hour)
        assert error_info.type == ValueError
        assert str(error_info.value) == "Invalid date and time inputs."
