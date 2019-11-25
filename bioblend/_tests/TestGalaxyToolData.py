"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.
"""
from . import GalaxyTestBase


class TestGalaxyToolData(GalaxyTestBase.GalaxyTestBase):

    def test_get_data_tables(self):
        tables = self.gi.tool_data.get_data_tables()
        for table in tables:
            self.assertIsNotNone(table['name'])

    def test_show_data_table(self):
        tables = self.gi.tool_data.get_data_tables()
        table = self.gi.tool_data.show_data_table(tables[0]['name'])
        self.assertIsNotNone(table['columns'])
        self.assertIsNotNone(table['fields'])
        self.assertIsNotNone(table['name'])
