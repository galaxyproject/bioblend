"""
Contains possible interactions with the Galaxy Histories
"""
from bioblend.galaxy.client import Client


class GenomeClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'genomes'
        super(GenomeClient, self).__init__(galaxy_instance)

    def get_genomes(self):
        """
        Returns a list of installed genomes
        """
        genomes = Client._get(self)
        return genomes

    def show_genome(self, id, num=None, chrom=None, low=None, high=None):
        """
        Returns information about build <id>
        """
        params = {}
        if num:
            params['num'] = num
        if chrom:
            params['chrom'] = chrom
        if low:
            params['low'] = low
        if high:
            params['high'] = high
        return Client._get(self, id, params)

    def install_genome(self, func='download', source=None, dbkey=None, ncbi_name=None, ensembl_dbkey=None, url_dbkey=None, indexers=None):
        """
        Download and/or index a genome.

        Parameters::

            dbkey           DB key of the build to download, ignored unless 'UCSC' is specified as the source
            ncbi_name       NCBI's genome identifier, ignored unless NCBI is specified as the source
            ensembl_dbkey   Ensembl's genome identifier, ignored unless Ensembl is specified as the source
            url_dbkey       DB key to use for this build, ignored unless URL is specified as the source
            source          Data source for this build. Can be: UCSC, Ensembl, NCBI, URL
            indexers        POST array of indexers to run after downloading (indexers[] = first, indexers[] = second, ...)
            func            Allowed values:
                            'download'  Download and index
                            'index'     Index only

        Returns::

            If no error:
            dict( status: 'ok', job: <job ID> )

            If error:
            dict( status: 'error', error: <error message> )
        """
        payload = {}
        if source:
            payload['source'] = source
        if func:
            payload['func'] = func
        if dbkey:
            payload['dbkey'] = dbkey
        if ncbi_name:
            payload['ncbi_name'] = ncbi_name
        if ensembl_dbkey:
            payload['ensembl_dbkey'] = ensembl_dbkey
        if url_dbkey:
            payload['url_dbkey'] = url_dbkey
        if indexers:
            payload['indexers'] = indexers
        return Client._post(self, payload)
