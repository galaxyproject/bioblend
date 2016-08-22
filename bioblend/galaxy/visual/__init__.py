"""
Contains possible interactions with the Galaxy visualization
"""
from bioblend.galaxy.client import Client


class VisualClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'visualizations'
        super(VisualClient, self).__init__(galaxy_instance)

    def get_visualizations(self):
        """
        Get the list of all visualizations.

        :rtype: list
        :return: A list of dicts with details on individual visualizations.
          For example::

            [{u'dbkey': u'eschColi_K12',
              u'id': u'df1c7c96fc427c2d',
              u'title': u'AVTest1',
              u'type': u'trackster',
              u'url': u'/api/visualizations/df1c7c96fc427c2d'},
             {u'dbkey': u'mm9',
              u'id': u'a669f50f8bf55b02',
              u'title': u'Bam to Bigwig',
              u'type': u'trackster',
              u'url': u'/api/visualizations/a669f50f8bf55b02'}]
        """
        return self._get()

    def show_visualization(self, visual_id):
        """
        Get details of a given visualization.

        :type visual_id: str
        :param visual_id: Encoded visualization ID

        :rtype: dict
        :return: A description of the given visualization.
          For example::

            {u'annotation': None,
             u'dbkey': u'mm9',
             u'id': u'18df9134ea75e49c',
             u'latest_revision': {  ... },
             u'model_class': u'Visualization',
             u'revisions': [u'aa90649bb3ec7dcb', u'20622bc6249c0c71'],
             u'slug': u'visualization-for-grant-1',
             u'title': u'Visualization For Grant',
             u'type': u'trackster',
             u'url': u'/u/azaron/v/visualization-for-grant-1',
             u'user_id': u'21e4aed91386ca8b'}
        """
        return self._get(id=visual_id)
