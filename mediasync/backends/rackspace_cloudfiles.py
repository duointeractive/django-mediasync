import cloudfiles
from django.conf import settings
from mediasync.msettings import CLOUDFILES_CONTAINER, CLOUDFILES_USERNAME, CLOUDFILES_KEY
from mediasync.backends import BaseClient

class Client(BaseClient):
    def open(self):
        _conn = cloudfiles.get_connection(CLOUDFILES_USERNAME, CLOUDFILES_KEY)
        self._container = _conn.create_container(CLOUDFILES_CONTAINER)

    def remote_media_url(self, with_ssl=False):
        return ""

    def put(self, filedata, content_type, remote_path, force=False):
        obj = self._container.create_object(remote_path)
        obj.write(filedata)

        return True
