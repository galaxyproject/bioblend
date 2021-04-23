"""
Contains possible interactions with the Galaxy Forms
"""
from bioblend.galaxy.client import Client


class FormsClient(Client):
    module = 'forms'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_forms(self):
        """
        Get the list of all forms.

        :rtype: list
        :return: Displays a collection (list) of forms.
          For example::

            [{'id': 'f2db41e1fa331b3e',
              'model_class': 'FormDefinition',
              'name': 'First form',
              'url': '/api/forms/f2db41e1fa331b3e'},
             {'id': 'ebfb8f50c6abde6d',
              'model_class': 'FormDefinition',
              'name': 'second form',
              'url': '/api/forms/ebfb8f50c6abde6d'}]
        """
        return self._get()

    def show_form(self, form_id):
        """
        Get details of a given form.

        :type form_id: str
        :param form_id: Encoded form ID

        :rtype: dict
        :return: A description of the given form.
          For example::

            {'desc': 'here it is ',
             'fields': [],
             'form_definition_current_id': 'f2db41e1fa331b3e',
             'id': 'f2db41e1fa331b3e',
             'layout': [],
             'model_class': 'FormDefinition',
             'name': 'First form',
             'url': '/api/forms/f2db41e1fa331b3e'}
        """
        return self._get(id=form_id)

    def create_form(self, form_xml_text):
        """
        Create a new form.

        :type   form_xml_text: str
        :param  form_xml_text: Form xml to create a form on galaxy instance

        :rtype:     str
        :return:   Unique URL of newly created form with encoded id
        """
        payload = form_xml_text
        return self._post(payload=payload)
