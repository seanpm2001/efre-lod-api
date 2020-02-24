import requests
import lod_api


class HttpStatusBase:

    host = None

    def setup(self):
        """ get debug_host and debug_port out off the api's config """

        self.host = "http://{host}:{port}".format(
            host=lod_api.CONFIG.get("debug_host"),
            port=lod_api.CONFIG.get("debug_port"),
        )

    def _http_response(self, path, status_code=200, host=None):
        """ Prepends host to path and queries the url expecting
            a status code of `status_code` for the test to
            succeed (assert)
        """
        if host:
            url = host + path
        else:
            url = self.host + path
        print(url)
        res = requests.get(url)
        if res.status_code != status_code:
            print("expected: {}; got: {}"
                  .format(status_code, res.status_code)
                  )
        assert(res.status_code == status_code)
        return res
