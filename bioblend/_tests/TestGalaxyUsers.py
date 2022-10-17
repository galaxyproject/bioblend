import bioblend.galaxy
from . import (
    GalaxyTestBase,
    test_util,
)


class TestGalaxyUsers(GalaxyTestBase.GalaxyTestBase):
    def test_get_users(self):
        users = self.gi.users.get_users()
        for user in users:
            assert user["id"] is not None
            assert user["email"] is not None

    def test_show_user(self):
        current_user = self.gi.users.get_current_user()
        user = self.gi.users.show_user(current_user["id"])
        assert user["id"] == current_user["id"]
        assert user["username"] == current_user["username"]
        assert user["email"] == current_user["email"]
        # The 2 following tests randomly fail

    #        assert user["nice_total_disk_usage"] == current_user["nice_total_disk_usage"]
    #        assert user["total_disk_usage"] == current_user["total_disk_usage"]

    def test_create_remote_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if not self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use remote users")
        new_user_email = "newuser@example.org"
        user = self.gi.users.create_remote_user(new_user_email)
        assert user["email"] == new_user_email
        if self.gi.config.get_config()["allow_user_deletion"]:
            deleted_user = self.gi.users.delete_user(user["id"])
            assert deleted_user["email"] == new_user_email
            assert deleted_user["deleted"]

    def test_create_local_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use local users")
        new_username = test_util.random_string()
        new_user_email = f"{new_username}@example.org"
        password = test_util.random_string(20)
        new_user = self.gi.users.create_local_user(new_username, new_user_email, password)
        assert new_user["username"] == new_username
        assert new_user["email"] == new_user_email
        # test a BioBlend GalaxyInstance can be created using username+password
        user_gi = bioblend.galaxy.GalaxyInstance(url=self.gi.base_url, email=new_user_email, password=password)
        assert user_gi.users.get_current_user()["email"] == new_user_email
        # test deletion
        if self.gi.config.get_config()["allow_user_deletion"]:
            deleted_user = self.gi.users.delete_user(new_user["id"])
            assert deleted_user["email"] == new_user_email
            assert deleted_user["deleted"]

    def test_get_current_user(self):
        user = self.gi.users.get_current_user()
        assert user["id"] is not None
        assert user["username"] is not None
        assert user["email"] is not None
        assert user["nice_total_disk_usage"] is not None
        assert user["total_disk_usage"] is not None

    def test_update_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use local users")
        new_username = test_util.random_string()
        new_user = self.gi.users.create_local_user(
            new_username, f"{new_username}@example.org", test_util.random_string(20)
        )
        new_user_id = new_user["id"]
        updated_username = test_util.random_string()
        updated_user_email = f"{updated_username}@example.org"
        self.gi.users.update_user(new_user_id, username=updated_username, email=updated_user_email)
        updated_user = self.gi.users.show_user(new_user_id)
        assert updated_user["username"] == updated_username
        assert updated_user["email"] == updated_user_email

        if self.gi.config.get_config()["allow_user_deletion"]:
            self.gi.users.delete_user(new_user_id)

    def test_get_user_apikey(self):
        # Test getting the API key of the current user, which surely has one
        user_id = self.gi.users.get_current_user()["id"]
        apikey = self.gi.users.get_user_apikey(user_id)
        assert apikey and apikey != "Not available."
        # Test getting the API key of a new user, which doesn't have one
        new_username = test_util.random_string()
        new_user_id = self.gi.users.create_local_user(
            new_username, f"{new_username}@example.org", test_util.random_string(20)
        )["id"]
        assert self.gi.users.get_user_apikey(new_user_id) == "Not available."

    @test_util.skip_unless_galaxy("release_21.01")
    def test_get_or_create_user_apikey(self):
        # Check that get_or_create_user_apikey() doesn't regenerate an existing API key
        user_id = self.gi.users.get_current_user()["id"]
        apikey = self.gi.users.get_user_apikey(user_id)
        assert self.gi.users.get_or_create_user_apikey(user_id) == apikey
        # Check that get_or_create_user_apikey() generates an API key for a new user
        new_username = test_util.random_string()
        new_user_id = self.gi.users.create_local_user(
            new_username, f"{new_username}@example.org", test_util.random_string(20)
        )["id"]
        new_apikey = self.gi.users.get_or_create_user_apikey(new_user_id)
        assert new_apikey and new_apikey != "Not available."

    def test_create_user_apikey(self):
        # Test creating an API key for a new user
        new_username = test_util.random_string()
        new_user_id = self.gi.users.create_local_user(
            new_username, f"{new_username}@example.org", test_util.random_string(20)
        )["id"]
        new_apikey = self.gi.users.create_user_apikey(new_user_id)
        assert new_apikey and new_apikey != "Not available."
        # Test regenerating an API key for a user that already has one
        regenerated_apikey = self.gi.users.create_user_apikey(new_user_id)
        assert regenerated_apikey and regenerated_apikey not in (new_apikey, "Not available.")
