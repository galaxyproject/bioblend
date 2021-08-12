import os
import unittest

import bioblend
import bioblend.toolshed
from . import test_util


@test_util.skip_unless_toolshed()
class TestToolshed(unittest.TestCase):

    def setUp(self):
        toolshed_url = os.environ.get('BIOBLEND_TOOLSHED_URL', 'https://testtoolshed.g2.bx.psu.edu/')
        self.ts = bioblend.toolshed.ToolShedInstance(url=toolshed_url)

    def test_categories_client(self):
        # get_categories
        categories = self.ts.categories.get_categories()
        self.assertIn('Assembly', [n['name'] for n in categories])
        # we cannot test get_categories with deleted=True as it requires administrator status

        # show_category
        visualization_category_id = [n for n in categories if n['name'] == 'Visualization'][0]['id']
        visualization_category = self.ts.categories.show_category(visualization_category_id)
        self.assertEqual(visualization_category['description'], 'Tools for visualizing data')

        # get_repositories
        repositories = self.ts.categories.get_repositories(visualization_category_id)
        repositories_reversed = self.ts.categories.get_repositories(visualization_category_id, sort_order='desc')
        self.assertEqual(repositories['repositories'][0]['model_class'], 'Repository')
        self.assertGreater(len(repositories['repositories']), 200)
        self.assertEqual(repositories['repositories'][0], repositories_reversed['repositories'][-1])

    def test_repositories_client(self):
        # get_repositories
        repositories = self.ts.repositories.get_repositories()
        self.assertGreater(len(repositories), 5000)
        self.assertEqual(repositories[0]['model_class'], 'Repository')

        # search_repositories
        samtools_search = self.ts.repositories.search_repositories('samtools', page_size=5)
        self.assertGreater(int(samtools_search['total_results']), 20)
        self.assertEqual(len(samtools_search['hits']), 5)

        # show_repository
        bam_to_sam_repo = [n for n in repositories if n['name'] == 'bam_to_sam'][0]
        show_bam_to_sam_repo = self.ts.repositories.show_repository(bam_to_sam_repo['id'])
        self.assertIn('SAM (Sequence Alignment/Map) format', show_bam_to_sam_repo['long_description'])

        # test_create_repository
        # need to provide an API key to test this

        # test_update_repository
        # need to provide an API key to test this

    def test_repositories_revisions(self):
        # repository_revisions
        revisions = self.ts.repositories.repository_revisions()
        self.assertGreater(len(revisions), 15000)
        self.assertEqual(revisions[0]['model_class'], 'RepositoryMetadata')

        # show_repository_revision
        revision_0 = self.ts.repositories.show_repository_revision(revisions[0]['id'])
        self.assertEqual(revision_0['id'], revisions[0]['id'])

        # repository_revisions with filters
        for filter in ["downloadable", "malicious", "missing_test_components", "includes_tools"]:
            filtered_revisions_true = self.ts.repositories.repository_revisions(**{filter: True})
            filtered_revisions_false = self.ts.repositories.repository_revisions(**{filter: False})
            self.assertEqual(len(filtered_revisions_false) + len(filtered_revisions_true), len(revisions))

        # get_ordered_installable_revisions
        bam_to_sam_revisions = self.ts.repositories.get_ordered_installable_revisions('bam_to_sam', 'devteam')
        self.assertGreaterEqual(len(bam_to_sam_revisions), 4)

        # get_repository_revision_install_info
        bam_to_sam_revision_install_info = self.ts.repositories.get_repository_revision_install_info('bam_to_sam', 'devteam', bam_to_sam_revisions[0])
        self.assertEqual(len(bam_to_sam_revision_install_info), 3)
        self.assertEqual(bam_to_sam_revision_install_info[0].get('model_class'), 'Repository')
        self.assertEqual(bam_to_sam_revision_install_info[1].get('model_class'), 'RepositoryMetadata')
        self.assertEqual(bam_to_sam_revision_install_info[2].get('model_class'), None)

    def test_tools_client(self):
        # search_tools
        samtools_search = self.ts.tools.search_tools('samtools', page_size=5)
        self.assertGreater(int(samtools_search['total_results']), 2000)
        self.assertEqual(len(samtools_search['hits']), 5)
