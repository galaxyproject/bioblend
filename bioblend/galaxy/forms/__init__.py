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
        Get a list of forms

        :rtype:     list
        :returns:   Displays a collection (list) of forms.
                 For example::

                   [   {   u'id': u'f2db41e1fa331b3e',
                   u'model_class': u'FormDefinition',
                   u'name': u'First form',
                   u'url': u'/api/forms/f2db41e1fa331b3e'},
                   {   u'id': u'ebfb8f50c6abde6d',
                   u'model_class': u'FormDefinition',
                   u'name': u'second form',
                   u'url': u'/api/forms/ebfb8f50c6abde6d'}]


        """
        return Client._get(self)

    def show_form(self, form_id):
        """
        Display information on a single form

        :type form_id: string
        :param form_id: Encoded form ID

        :rtype: dict
        :return: A description of single form
                 For example::

                   {   u'desc': u'here it is ',
                   u'fields': [],
                   u'form_definition_current_id': u'f2db41e1fa331b3e',
                   u'id': u'f2db41e1fa331b3e',
                   u'layout': [],
                   u'model_class': u'FormDefinition',
                   u'name': u'First form',
                   u'url': u'/api/forms/f2db41e1fa331b3e'}


        """

        return Client._get(self, id=form_id)

    def create_form(self, form_xml_text):
        """
        Create a new form

        :type   form_xml_text: string
        :param  form_xml_text: Form xml to create a form on galaxy instance

        :rtype:     string
        :returns:   Unique url of newly created form with encoded id

        """

        payload = form_xml_text

        return Client._post(self, payload=payload)
