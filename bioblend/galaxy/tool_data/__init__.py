"""
Contains possible interactions with the Galaxy Tool data tables
"""
from bioblend.galaxy.client import Client


class ToolDataClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'tool_data'
        super(ToolDataClient, self).__init__(galaxy_instance)

    def get_data_tables(self):
        """
        Get the list of all data tables.

        :rtype: list
        :return: A list of dicts with details on individual data tables.
          For example::

            [{"model_class": "TabularToolDataTable", "name": "fasta_indexes"},
             {"model_class": "TabularToolDataTable", "name": "bwa_indexes"}]
        """
        return self._get()

    def show_data_table(self, data_table_id):
        """
        Get details of a given data table.

        :type data_table_id: str
        :param data_table_id: ID of the data table

        :rtype: dict
        :return: A description of the given data table and its content.
          For example::

            {"columns": ["value", "dbkey", "name", "path"],
             "fields": [["test id",
               "test",
               "test name",
               "/opt/galaxy-dist/tool-data/test/seq/test id.fa"]],
             "model_class": "TabularToolDataTable",
             "name": "all_fasta"}
        """
        return self._get(id=data_table_id)

    def reload_data_table(self, data_table_id):
        """
        Reload a data table.

        :type data_table_id: str
        :param data_table_id: ID of the data table

        :rtype: dict
        :return: A description of the given data table and its content.
          For example::

            {"columns": ["value", "dbkey", "name", "path"],
             "fields": [["test id",
               "test",
               "test name",
               "/opt/galaxy-dist/tool-data/test/seq/test id.fa"]],
             "model_class": "TabularToolDataTable",
             "name": "all_fasta"}
        """
        url = "%s/tool_data/%s/reload" % (self.gi.url, data_table_id)
        return self._get(url=url)

    def delete_data_table(self, data_table_id, values):
        """
        Delete an item from a data table.

        :type data_table_id: str
        :param data_table_id: ID of the data table

        :type values: str
        :param values: a "|" separated list of column contents, there must be a
          value for all the columns of the data table
        """
        payload = {'values': values}
        return self._delete(payload=payload, id=data_table_id)
