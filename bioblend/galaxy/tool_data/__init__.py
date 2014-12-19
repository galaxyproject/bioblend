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
        Displays a collection (list) of data tables.

        :rtype: list
        :return: A list of dicts with details on individual data tables.
                 For example::

                [
                    {
                        "model_class": "TabularToolDataTable", 
                        "name": "fasta_indexes"
                    }, 
                    {
                        "model_class": "TabularToolDataTable", 
                        "name": "bwa_indexes"
                    }
                }
        """
        return Client._get(self)

    def show_data_table(self, data_table_id):
        """
        Display information on a single data_table

        :type data_table_id: string
        :param data_table_id: ID of the data table

        :rtype: dict
        :return: A description of data_table and its content
                 For example::

            {
                "columns": ["value", "dbkey", "name", "path"], 
                "fields": [
                    [
                        "test id", "test", "test name",
                        "/opt/galaxy-dist/tool-data/test/seq/test id.fa"
                    ]
                ], 
                "model_class": "TabularToolDataTable", 
                "name": "all_fasta"
            }
        """

        return Client._get(self, id=data_table_id)

    def delete_data_table(self, data_table_id, values):
        """
        Delete an item from a data table.

        The ``values`` is a "|" separated list of column contents,
        there must be a value for all the columns of the data table
        """
        payload = {}
        payload['values'] = values
        
        return Client._delete(self, payload, id=data_table_id)
