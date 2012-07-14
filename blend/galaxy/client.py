"""
An interface the clients should implement.

This class is primarily a helper for the library and user code
should not use it directly.
"""
import simplejson


class Client(object):
    def __init__(self, galaxy_instance):
        """
        A generic Client interface defining the common fields.

        All clinets *must* define the following field (which will be used as part
        of the URL composition (eg, http://<galaxy_instance>/api/libraries):
        ``self.module = 'workflows' | 'libraries' | 'histories' | ...``
        """
        self.gi = galaxy_instance
        self.url = '/'.join([self.gi.url, self.module])

    def _get(self, id=None, deleted=False, contents=None, url=None):
        """
        Do a generic GET request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided
        to use for the request.

        This action often repeats itself in this library, so use this as a
        generic method that can easily be replaced if it does not do what's
        needed.
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted, contents=contents)
        r = self.gi.make_get_request(url)
        return r.json

    def _post(self, payload, id=None, deleted=False, contents=None, url=None):
        """
        Do a generic POST request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that can be converted
        into a JSON object (which will be done whthin this method)
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted, contents=contents)
        payload = simplejson.dumps(payload)
        r = self.gi.make_post_request(url, payload=payload)
        return r.json

    def _delete(self, payload, id=None, deleted=False, contents=None, url=None):
        """
        Do a generic DELETE request, composing the url from the contents of the
        arguments. Alternatively, an explicit ``url`` can be provided to use
        for the request. ``payload`` must be a dict that can be converted
        into a JSON object (which will be done whthin this method)
        """
        if not url:
            url = self.gi._make_url(self, module_id=id, deleted=deleted, contents=contents)
        payload = simplejson.dumps(payload)
        r = self.gi.make_delete_request(url, payload=payload)
        return r.json
