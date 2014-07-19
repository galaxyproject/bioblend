"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.

Use ``nose`` to run these unit tests.
"""
import GalaxyTestBase
import test_util


@test_util.skip_unless_galaxy()
class TestGalaxyLibraries(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyLibraries, self).setUp()
        self.library = self.gi.libraries.create_library('automated test library', description='automated test', synopsis='automated test synopsis')

    def test_create_library(self):
        lib_name = 'another automated test library'
        test_library = self.gi.libraries.create_library(lib_name, description='automated test', synopsis='automated test synopsis')
        self.assertEqual(test_library['name'], lib_name)
        self.assertNotEqual(test_library['id'], None)

    def test_create_folder(self):
        pass

    def test_get_libraries(self):
        # Make sure there's at least one value - the one we created
        all_libraries = self.gi.libraries.get_libraries()
        self.assertTrue(len(all_libraries) >= 1)

    def test_show_library(self):
#        library_data = self.gi.libraries.show_library(self.library['id'])
#        self.assertEqual(self.library['id'], library_data['id'])
#        self.assertEqual(self.library['name'], library_data['name'])
#        self.assertEqual('new', library_data['state'])
        pass

    def test_upload_file_from_url(self):
        pass

    def test_upload_file_contents(self):
        pass

    def test_upload_file_from_local_path(self):
        pass

    def test_upload_file_from_server(self):
        pass
