"""
Contains possible interactions with the Galaxy Forms
"""
from bioblend.galaxy.client import Client


class FormsClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'forms'
        super(FormsClient, self).__init__(galaxy_instance)

    def get_forms(self):
        """
        Get the list of all forms.

        :rtype: list
        :returns: Displays a collection (list) of forms.
          For example::

            [{u'id': u'f2db41e1fa331b3e',
              u'model_class': u'FormDefinition',
              u'name': u'First form',
              u'url': u'/api/forms/f2db41e1fa331b3e'},
             {u'id': u'ebfb8f50c6abde6d',
              u'model_class': u'FormDefinition',
              u'name': u'second form',
              u'url': u'/api/forms/ebfb8f50c6abde6d'}]
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

            {u'desc': u'here it is ',
             u'fields': [],
             u'form_definition_current_id': u'f2db41e1fa331b3e',
             u'id': u'f2db41e1fa331b3e',
             u'layout': [],
             u'model_class': u'FormDefinition',
             u'name': u'First form',
             u'url': u'/api/forms/f2db41e1fa331b3e'}
        """
        return self._get(id=form_id)

    def create_form(self, form_xml_text):
        """
        Create a new form.

        :type   form_xml_text: str
        :param  form_xml_text: Form xml to create a form on galaxy instance

        :rtype:     str
        :returns:   Unique url of newly created form with encoded id
        """
        payload = form_xml_text
        return self._post(payload=payload)
