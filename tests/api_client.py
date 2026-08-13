from rest_framework.test import APIClient


class JsonAPIClient(APIClient):
    """Keep the former test client's convenient json= request argument."""

    def post(self, path, data=None, format=None, content_type=None, **extra):
        if "json" in extra:
            data = extra.pop("json")
            format = "json"
        return super().post(path, data=data, format=format, content_type=content_type, **extra)

    def get(self, path, data=None, follow=False, **extra):
        if "params" in extra:
            data = extra.pop("params")
        return super().get(path, data=data, follow=follow, **extra)

    def patch(self, path, data=None, format=None, content_type=None, **extra):
        if "json" in extra:
            data = extra.pop("json")
            format = "json"
        return super().patch(path, data=data, format=format, content_type=content_type, **extra)
