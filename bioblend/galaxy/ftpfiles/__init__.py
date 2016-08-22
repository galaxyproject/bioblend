"""
Contains possible interactions with the Galaxy FTP Files
"""
from bioblend.galaxy.client import Client


class FTPFilesClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'ftp_files'
        super(FTPFilesClient, self).__init__(galaxy_instance)

    def get_ftp_files(self, deleted=False):
        """
        Get a list of local files.

        :rtype: list
        :return: A list of dicts with details on individual files on FTP
        """
        return self._get()
