"""
Interaction with a Tool Shed instance categories
"""
from bioblend.galaxy.client import Client


class ToolShedCategoryClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'categories'
        super(ToolShedCategoryClient, self).__init__(toolshed_instance)

    def get_categories(self, deleted=False):
        """
        Returns a list of dictionaries that contain descriptions of the
        repository categories found on the given Tool Shed instance.

        :type deleted: bool
        :param deleted: whether to show deleted categories

        :rtype: list
        :return: A list of dictionaries containing information about
          repository categories present in the Tool Shed.
          For example::

            [{u'deleted': False,
              u'description': u'Tools for manipulating data',
              u'id': u'175812cd7caaf439',
              u'model_class': u'Category',
              u'name': u'Text Manipulation',
              u'url': u'/api/categories/175812cd7caaf439'}]

        .. versionadded:: 0.5.2
        """
        return self._get(deleted=deleted)

    def show_category(self, category_id):
        """
        Get details of a given category.

        :type category_id: str
        :param category_id: Encoded category ID

        :rtype: dict
        :return: details of the given category
        """
        return self._get(id=category_id)
