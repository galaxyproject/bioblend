import os
import shutil
import tempfile

from . import GalaxyTestBase, test_util

FOO_DATA = 'foo\nbar\n'


class TestGalaxyLibraries(GalaxyTestBase.GalaxyTestBase):

    def setUp(self):
        super(TestGalaxyLibraries, self).setUp()
        self.name = 'automated test library'
        self.library = self.gi.libraries.create_library(self.name, description='automated test', synopsis='automated test synopsis')

    def tearDown(self):
        self.gi.libraries.delete_library(self.library['id'])

    def test_create_library(self):
        self.assertEqual(self.library['name'], self.name)
        self.assertIsNotNone(self.library['id'])

    def test_get_libraries(self):
        library_data = self.gi.libraries.get_libraries(library_id=self.library['id'])[0]
        self.assertTrue(library_data['name'] == self.name)
        deleted_name = 'deleted test library'
        deleted_library = self.gi.libraries.create_library(deleted_name, description='a deleted library', synopsis='automated test synopsis')
        self.gi.libraries.delete_library(deleted_library['id'])
        deleted_library_data = self.gi.libraries.get_libraries(library_id=deleted_library['id'], deleted=True)[0]
        self.assertTrue(deleted_library_data['name'] == deleted_name)
        all_non_deleted_libraries = self.gi.libraries.get_libraries(deleted=False)
        self.assertTrue(any(l['id'] == self.library['id'] for l in all_non_deleted_libraries))
        self.assertFalse(any(l['id'] == deleted_library['id'] for l in all_non_deleted_libraries))
        all_deleted_libraries = self.gi.libraries.get_libraries(deleted=True)
        self.assertFalse(any(l['id'] == self.library['id'] for l in all_deleted_libraries))
        self.assertTrue(any(l['id'] == deleted_library['id'] for l in all_deleted_libraries))
        all_libraries = self.gi.libraries.get_libraries(deleted=None)
        self.assertTrue(any(l['id'] == self.library['id'] for l in all_libraries))
        self.assertTrue(any(l['id'] == deleted_library['id'] for l in all_libraries))

    def test_show_library(self):
        library_data = self.gi.libraries.show_library(self.library['id'])
        self.assertEqual(self.library['id'], library_data['id'])
        self.assertEqual(self.library['name'], library_data['name'])

    def test_upload_file_from_url(self):
        pass

    def test_upload_file_contents(self):
        self.gi.libraries.upload_file_contents(self.library['id'], FOO_DATA)

    def test_upload_file_from_local_path(self):
        with tempfile.NamedTemporaryFile(mode='w', prefix='bioblend_test_') as f:
            f.write(FOO_DATA)
            f.flush()
            self.gi.libraries.upload_file_from_local_path(self.library['id'], f.name)

    def test_upload_file_from_server(self):
        pass

    def test_upload_from_galaxy_filesystem(self):
        bnames = ['f%d.txt' % i for i in range(2)]
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        try:
            fnames = [os.path.join(tempdir, _) for _ in bnames]
            for fn in fnames:
                with open(fn, 'w') as f:
                    f.write(FOO_DATA)
            filesystem_paths = '\n'.join(fnames)
            ret = self.gi.libraries.upload_from_galaxy_filesystem(self.library['id'], filesystem_paths)
            for dataset_dict in ret:
                dataset = self.gi.libraries.wait_for_dataset(self.library['id'], dataset_dict['id'])
                self.assertEqual(dataset['state'], 'ok')
            ret = self.gi.libraries.upload_from_galaxy_filesystem(self.library['id'], filesystem_paths, link_data_only='link_to_files')
            for dataset_dict in ret:
                dataset = self.gi.libraries.wait_for_dataset(self.library['id'], dataset_dict['id'])
                self.assertEqual(dataset['state'], 'ok')
        finally:
            shutil.rmtree(tempdir)

    def test_copy_from_dataset(self):
        history = self.gi.histories.create_history()
        dataset_id = self._test_dataset(history['id'])
        self.gi.libraries.copy_from_dataset(self.library['id'], dataset_id, message='Copied from dataset')

    @test_util.skip_unless_galaxy('release_17.09')
    def test_update_dataset(self):
        library_id = self.library["id"]
        dataset1 = self.gi.libraries.upload_file_contents(library_id, FOO_DATA)
        updated_dataset = self.gi.libraries.update_library_dataset(dataset1[0]['id'], name='Modified name', misc_info='Modified the name succesfully')
        self.assertEqual(updated_dataset["name"], 'Modified name')
        self.assertEqual(updated_dataset["misc_info"], 'Modified the name succesfully')

    @test_util.skip_unless_galaxy('release_14.10')
    def test_library_permissions(self):
        current_user = self.gi.users.get_current_user()
        user_id_list_new = [current_user['id']]
        self.gi.libraries.set_library_permissions(self.library['id'], access_in=user_id_list_new, modify_in=user_id_list_new, add_in=user_id_list_new, manage_in=user_id_list_new)
        ret = self.gi.libraries.get_library_permissions(self.library['id'])
        self.assertEqual(set(_[1] for _ in ret['access_library_role_list']), set(user_id_list_new))
        self.assertEqual(set(_[1] for _ in ret['modify_library_role_list']), set(user_id_list_new))
        self.assertEqual(set(_[1] for _ in ret['add_library_item_role_list']), set(user_id_list_new))
        self.assertEqual(set(_[1] for _ in ret['manage_library_role_list']), set(user_id_list_new))
