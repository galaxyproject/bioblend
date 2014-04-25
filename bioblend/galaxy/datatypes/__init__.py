"""
Contains possible interactions with the Galaxy Datatype
"""
from bioblend.galaxy.client import Client


class DatatypesClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'datatypes'
        super(DatatypesClient, self).__init__(galaxy_instance)

    def get_datatypes(self, extension_only=False, upload_only=False):
        """
        Displays a collection (list) of datatypes.


        :rtype: list
        :return: A list of dicts with details on individual datatypes.
                 For example::

                 [ u'snpmatrix',
                 u'snptest',
                 u'tabular',
                 u'taxonomy',
                 u'twobit',
                 u'txt',
                 u'vcf',
                 u'wig',
                 u'xgmml',
                 u'xml']

        """

        params = {}
        if extension_only:
            params['extension_only'] = True

        if upload_only:
            params['upload_only'] = True

        return Client._get(self, params=params)

    def get_sniffers(self):
        """
        Displays a collection (list) of sniffers.

        :rtype: list
        :return: A list of  individual sniffers.
                 For example::

                 [u'galaxy.datatypes.tabular:Vcf',
                 u'galaxy.datatypes.binary:TwoBit',
                 u'galaxy.datatypes.binary:Bam',
                 u'galaxy.datatypes.binary:Sff',
                 u'galaxy.datatypes.xml:Phyloxml',
                 u'galaxy.datatypes.xml:GenericXml',
                 u'galaxy.datatypes.sequence:Maf',
                 u'galaxy.datatypes.sequence:Lav',
                 u'galaxy.datatypes.sequence:csFasta']



        """

        url = self.gi._make_url(self)
        url = '/'.join([url, "sniffers"])

        return Client._get(self, url=url)
