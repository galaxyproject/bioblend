"""
Helper class for Galaxy and ToolShed Instance object

This class is primarily a helper for the library and user code
should not use it directly.
A base representation of an instance 
"""
import urlparse
import requests
import simplejson

class GalaxyClient(object):
    def _make_url(self, module, module_id=None, deleted=False, contents=False):
        """
        Compose a URL based on the provided arguments.

        :type module: string
        :param module: The name of the base module for which to make the URL.
                       For example: ``libraries``, ``workflows``, ``histories``

        :type module_id: string
        :param module_id: The encoded ID for a specific module (eg, library ID)

        :type deleted: bool
        :param deleted: If ``True``, include ``deleted`` in the URL, after the module
                        name (eg, ``<base_url>/api/libraries/deleted``)

        :type contents: bool
        :param contents: If ``True``, include 'contents' in the URL, after the module ID:
                         ``<base_url>/api/libraries/<encoded_library_id>/contents``
        """
        c_url = self.url
        c_url = '/'.join([c_url, module.module])
        if deleted is True:
            c_url = '/'.join([c_url, 'deleted'])
        if module_id is not None:
            c_url = '/'.join([c_url, module_id])
            if contents is True:
                c_url = '/'.join([c_url, 'contents'])
        return c_url

    def make_get_request(self, url, params=None):
        """
        Make a GET request using the provided url.

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.get(url, verify=self.verify, params=params)
        return r

    def make_post_request(self, url, payload, params=None, files_attached=False):
        """
        Make a POST request using the provided ``url`` and ``payload``.
        The ``payload`` must be a dict that contains the request values.
        The payload dict may contain file handles (in which case the files_attached
        flag must be set to true).

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.

        The return value will contain the response body as a JSON object.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params


        if files_attached:
            payload.update(params)  # merge query string values into request body instead
            poster.streaminghttp.register_openers()
            datagen, headers = poster.encode.multipart_encode(payload)
            request = urllib2.Request(url, datagen, headers)
            fp = urllib2.urlopen(request)
            return simplejson.load(fp)
        else:
            payload = simplejson.dumps(payload)
            r = requests.post(url, data=payload, headers=self.json_headers,
                    verify=self.verify, params=params)
            return r.json()

    def make_delete_request(self, url, payload=None, params=None):
        """
        Make a DELETE request using the provided ``url`` and the optional
        arguments.
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``simplejson.dumps``)

        If the ``params`` are not provided, use ``default_params`` class field.
        If params are provided and the provided dict does not have ``key`` key,
        the default ``self.key`` value will be included in what's passed to
        the server via the request.
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
        r = requests.delete(url, verify=self.verify, data=payload, params=params)
        return r

    def make_put_request(self,url,payload=None,params=None):
        """
        Make a PUT request using the provided ``url`` with required playload
        The ``payload`` must be a dict that can be converted into a JSON
        object (via ``simplejson.dumps``)
        """
        if params is not None and params.get('key', False) is False:
            params['key'] = self.key
        else:
            params = self.default_params
            
        payload = simplejson.dumps(payload)
        r = requests.put(url,data=payload,params=params)
        return r
