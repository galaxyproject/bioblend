"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import unittest
from bioblend.cloudman.launch import Bunch
from bioblend.cloudman import CloudManConfig
from bioblend.cloudman import CloudManInstance
import GalaxyTestBase

class TestGalaxyLibraries(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyLibraries, self).setUp()
        self.library = self.gi.libraries.create_library('automated test library', description='automated test', synopsis='automated test synopsis')

    def test_create_library(self):
        lib_name = 'another automated test library'
        test_library = self.gi.libraries.create_library(lib_name, description='automated test', synopsis='automated test synopsis')
        self.assertEqual(test_library['name'], lib_name)
        self.assertNotEqual(test_library['id'], None)
        self.assertNotEqual(test_library['url'], None)

    def test_create_folder(self):
        pass

    def test_get_libraries(self):
        # Make sure there's at least one value - the one we created
        all_libraries = self.gi.libraries.get_libraries()
        self.assertIsNotNone(all_libraries)

#        # Check whether name is correct, when searched by id
#        new_library = self.gi.libraries.get_libraries(library_id=self.library['id'])
#        self.assertTrue(any(d['name'] == self.default_library_name for d in new_library))
#
#        # Check whether id is present, when searched by name
#        new_library = self.gi.histories.get_libraries(name=self.default_library_name)
#        self.assertTrue(any(d['id'] == self.library['id'] for d in new_library))

        # check whether deleted history is returned correctly
        deleted_libraries = self.gi.libraries.get_libraries(deleted=True)
        deleted_ids = [lib['id'] for lib in deleted_libraries]
        all_ids = [lib['id'] for lib in all_libraries]
        intersection = list(set(all_ids) & set(deleted_ids))
        self.assertEqual(intersection, [], 'Deleted libraries and current libraries should not overlap')

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
