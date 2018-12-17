"""
Contains possible interactions with the Galaxy Datasets
"""
import logging
import os
import shlex
import time

from six.moves.urllib.parse import urljoin
from six.moves.urllib.request import urlopen

import bioblend
from bioblend.galaxy.client import Client

log = logging.getLogger(__name__)

terminal_states = ('ok', 'empty', 'error', 'discarded', 'failed_metadata')


class DatasetClient(Client):
    def __init__(self, galaxy_instance):
        self.module = 'datasets'
        super(DatasetClient, self).__init__(galaxy_instance)

    def show_dataset(self, dataset_id, deleted=False, hda_ldda='hda'):
        """
        Get details about a given dataset. This can be a history or a library dataset.

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID

        :type deleted: bool
        :param deleted: Whether to return results for a deleted dataset

        :type hda_ldda: str
        :param hda_ldda: Whether to show a history dataset ('hda' - the default) or library
                         dataset ('ldda').
        """
        params = dict(
            hda_ldda=hda_ldda,
        )
        return self._get(id=dataset_id, deleted=deleted, params=params)

    def download_dataset(self, dataset_id, file_path=None, use_default_filename=True,
                         maxwait=12000):
        """
        Download a dataset to file or in memory. If the dataset state is not
        'ok', a ``DatasetStateException`` will be thrown.

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID

        :type file_path: str
        :param file_path: If this argument is provided, the dataset will be streamed to disk
                          at that path (should be a directory if use_default_filename=True).
                          If the file_path argument is not provided, the dataset content is loaded into memory
                          and returned by the method (Memory consumption may be heavy as the entire file
                          will be in memory).

        :type use_default_filename: bool
        :param use_default_filename: If this argument is True, the exported
                                 file will be saved as file_path/%s,
                                 where %s is the dataset name.
                                 If this argument is False, file_path is assumed to
                                 contain the full file path including the filename.

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the dataset state to
          become terminal. If the dataset state is not terminal within this
          time, a ``DatasetTimeoutException`` will be thrown.

        :rtype: dict
        :return: If a file_path argument is not provided, returns a dict containing the file_content.
                 Otherwise returns nothing.
        """
        dataset = self._block_until_dataset_terminal(dataset_id, maxwait=maxwait)
        if not dataset['state'] == 'ok':
            raise DatasetStateException("Dataset state is not 'ok'. Dataset id: %s, current state: %s" % (dataset_id, dataset['state']))

        # Galaxy release_13.01 and earlier does not have file_ext in the dataset
        # dict, so resort to data_type.
        # N.B.: data_type cannot be used for Galaxy release_14.10 and later
        # because it was changed to the Galaxy datatype class
        file_ext = dataset.get('file_ext', dataset['data_type'])
        # Resort to 'data' when Galaxy returns an empty or temporary extension
        if not file_ext or file_ext == 'auto' or file_ext == '_sniff_':
            file_ext = 'data'
        # The preferred download URL is
        # '/api/histories/<history_id>/contents/<dataset_id>/display?to_ext=<dataset_ext>'
        # since the old URL:
        # '/dataset/<dataset_id>/display/to_ext=<dataset_ext>'
        # does not work when using REMOTE_USER with access disabled to
        # everything but /api without auth
        if 'url' in dataset:
            # This is Galaxy release_15.03 or later
            download_url = dataset['download_url'] + '?to_ext=' + file_ext
        else:
            # This is Galaxy release_15.01 or earlier, for which the preferred
            # URL does not work without a key, so resort to the old URL
            download_url = 'datasets/' + dataset_id + '/display?to_ext=' + file_ext
        url = urljoin(self.gi.base_url, download_url)

        stream_content = file_path is not None
        r = self.gi.make_get_request(url, stream=stream_content)
        r.raise_for_status()

        if file_path is None:
            if 'content-length' in r.headers and len(r.content) != int(r.headers['content-length']):
                log.warning("Transferred content size does not match content-length header (%s != %s)" % (len(r.content), r.headers['content-length']))
            return r.content
        else:
            if use_default_filename:
                # Build a useable filename
                filename = dataset['name'] + '.' + file_ext
                # Now try to get a better filename from the response headers
                # We expect tokens 'filename' '=' to be followed by the quoted filename
                if 'content-disposition' in r.headers:
                    tokens = list(shlex.shlex(r.headers['content-disposition'], posix=True))
                    try:
                        header_filepath = tokens[tokens.index('filename') + 2]
                        filename = os.path.basename(header_filepath)
                    except (ValueError, IndexError):
                        pass
                file_local_path = os.path.join(file_path, filename)
            else:
                file_local_path = file_path

            with open(file_local_path, 'wb') as fp:
                for chunk in r.iter_content(chunk_size=bioblend.CHUNK_SIZE):
                    if chunk:
                        fp.write(chunk)

            # Return location file was saved to
            return file_local_path

    def _block_until_dataset_terminal(self, dataset_id, maxwait=12000, interval=3):
        """
        Wait until the dataset state is terminal ('ok', 'empty', 'error',
        'discarded' or 'failed_metadata').
        """
        assert maxwait >= 0
        assert interval > 0

        time_left = maxwait
        while True:
            dataset = self.show_dataset(dataset_id)
            state = dataset['state']
            if state in terminal_states:
                return dataset
            time_left -= interval
            if time_left > 0:
                log.warning("Waiting for dataset %s to complete. Will wait another %i s" % (dataset_id, time_left))
                time.sleep(min(time_left, interval))
            else:
                raise DatasetTimeoutException("Waited too long for dataset %s to complete" % dataset_id)

    def show_stderr(self, dataset_id):
        """
        Get the stderr output of a dataset.

        .. deprecated:: 0.9.0
           Use :meth:`~bioblend.galaxy.jobs.JobsClient.show_job` with
           ``full_details=True`` instead.

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID
        """
        res = urlopen(self.url[:-len("/api/datasets/") + 1] + "/datasets/" + dataset_id + "/stderr")
        return res.read()

    def show_stdout(self, dataset_id):
        """
        Get the stdout output of a dataset.

        .. deprecated:: 0.9.0
           Use :meth:`~bioblend.galaxy.jobs.JobsClient.show_job` with
           ``full_details=True`` instead.

        :type dataset_id: str
        :param dataset_id: Encoded dataset ID
        """
        res = urlopen(self.url[:-len("/api/datasets/") + 1] + "/datasets/" + dataset_id + "/stdout")
        return res.read()


class DatasetStateException(Exception):
    pass


class DatasetTimeoutException(Exception):
    pass
