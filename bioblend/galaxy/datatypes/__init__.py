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
        Get the list of all installed datatypes.

        :rtype: list
        :return: A list of datatype names.
          For example::

            [u'snpmatrix',
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

        return self._get(params=params)

    def get_sniffers(self):
        """
        Get the list of all installed sniffers.

        :rtype: list
        :return: A list of sniffer names.
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

        return self._get(url=url)
