"""
Contains possible interactions with the Galaxy Quota
"""
from bioblend.galaxy.client import Client


class QuotaClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'quotas'
        super(QuotaClient, self).__init__(galaxy_instance)

    def get_quotas(self, deleted=False):
        """
        Get a list of quotas

        :type deleted: Boolean
        :param deleted: Only return quota(s) that have been deleted


        :rtype: list
        :return: A list of dicts with details on individual quotas.
                 For example::

                   [{   u'id': u'0604c8a56abe9a50',
                   u'model_class': u'Quota',
                   u'name': u'test ',
                   u'url': u'/api/quotas/0604c8a56abe9a50'},
                   {   u'id': u'1ee267091d0190af',
                   u'model_class': u'Quota',
                   u'name': u'workshop',
                   u'url': u'/api/quotas/1ee267091d0190af'}]


        """
        return Client._get(self, deleted=deleted)

    def show_quota(self, quota_id, deleted=False):
        """
        Display information on a quota

        :type quota_id: string
        :param quota_id: Encoded quota ID

        :type deleted: Boolean
        :param deleted: Search for quota in list of ones already marked as deleted


        :rtype: dict
        :return: A description of quota
                 For example::

                   {   u'bytes': 107374182400,
                   u'default': [],
                   u'description': u'just testing',
                   u'display_amount': u'100.0 GB',
                   u'groups': [],
                   u'id': u'0604c8a56abe9a50',
                   u'model_class': u'Quota',
                   u'name': u'test ',
                   u'operation': u'=',
                   u'users': []}


        """
        return Client._get(self, id=quota_id, deleted=deleted)
