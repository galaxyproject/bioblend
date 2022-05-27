"""
Contains possible interactions with the Galaxy Histories
"""
from bioblend.galaxy.client import Client


class GenomeClient(Client):
    module = "genomes"

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_genomes(self):
        """
        Returns a list of installed genomes

        :rtype: list
        :return: List of installed genomes
        """
        genomes = self._get()
        return genomes

    def show_genome(self, id, num=None, chrom=None, low=None, high=None):
        """
        Returns information about build <id>

        :type id: str
        :param id: Genome build ID to use

        :type num: str
        :param num: num

        :type chrom: str
        :param chrom: chrom

        :type low: str
        :param low: low

        :type high: str
        :param high: high

        :rtype: dict
        :return: Information about the genome build
        """
        params = {}
        if num:
            params["num"] = num
        if chrom:
            params["chrom"] = chrom
        if low:
            params["low"] = low
        if high:
            params["high"] = high
        return self._get(id, params)

    def install_genome(
        self,
        func="download",
        source=None,
        dbkey=None,
        ncbi_name=None,
        ensembl_dbkey=None,
        url_dbkey=None,
        indexers=None,
    ):
        """
        Download and/or index a genome.


        :type dbkey: str
        :param dbkey: DB key of the build to download, ignored unless 'UCSC' is specified as the source

        :type ncbi_name: str
        :param ncbi_name: NCBI's genome identifier, ignored unless NCBI is specified as the source

        :type ensembl_dbkey: str
        :param ensembl_dbkey: Ensembl's genome identifier, ignored unless Ensembl is specified as the source

        :type url_dbkey: str
        :param url_dbkey: DB key to use for this build, ignored unless URL is specified as the source

        :type source: str
        :param source: Data source for this build. Can be: UCSC, Ensembl, NCBI, URL

        :type indexers: list
        :param indexers: POST array of indexers to run after downloading (indexers[] = first, indexers[] = second, ...)

        :type func: str
        :param func: Allowed values: 'download', Download and index; 'index', Index only

        :rtype: dict
        :return: dict( status: 'ok', job: <job ID> )
                 If error:
                 dict( status: 'error', error: <error message> )
        """
        payload = {}
        if source:
            payload["source"] = source
        if func:
            payload["func"] = func
        if dbkey:
            payload["dbkey"] = dbkey
        if ncbi_name:
            payload["ncbi_name"] = ncbi_name
        if ensembl_dbkey:
            payload["ensembl_dbkey"] = ensembl_dbkey
        if url_dbkey:
            payload["url_dbkey"] = url_dbkey
        if indexers:
            payload["indexers"] = indexers
        return self._post(payload)
