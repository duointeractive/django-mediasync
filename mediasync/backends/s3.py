import base64
import datetime
import hashlib
import zlib
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.core.exceptions import ImproperlyConfigured
from mediasync.msettings import TYPES_TO_COMPRESS, AWS_KEY, AWS_SECRET, AWS_BUCKET, AWS_PREFIX, AWS_BUCKET_CNAME
from mediasync.backends import BaseClient

class Client(BaseClient):
    def open(self):
        try:
            _conn = S3Connection(AWS_KEY, AWS_SECRET)
        except AttributeError:
            raise ImproperlyConfigured("S3 keys not set and no boto config found.")

        self._bucket = _conn.create_bucket(AWS_BUCKET)

        self._entries = { }
        for entry in self._bucket.list(AWS_PREFIX):
            self._entries[entry.key] = entry.etag.strip('"')

    def remote_media_url(self, with_ssl=False):
        """
        Returns the base remote media URL. In this case, we can safely make
        some assumptions on the URL string based on bucket names, and having
        public ACL on.
        
        args:
          with_ssl: (bool) If True, return an HTTPS url.
        """
        protocol = 'http' if with_ssl is False else 'https'
        url = (AWS_BUCKET_CNAME and "%s://%s" or "%s://s3.amazonaws.com/%s") % (protocol, AWS_BUCKET)
        if AWS_PREFIX:
            url = "%s/%s" % (url, AWS_PREFIX)
        return url

    def put(self, filedata, content_type, remote_path, force=False):
        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(self.expiration_days)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S GMT")

        if AWS_PREFIX:
            remote_path = "%s/%s" % (AWS_PREFIX, remote_path)

        # create initial set of headers
        headers = {
            "x-amz-acl": "public-read",
            "Content-Type": content_type,
            "Expires": expires,
            "Cache-Control": 'max-age=%d' % (self.expiration_days * 24 * 3600),
        }

        # check to see if file should be gzipped based on content_type
        # also check to see if filesize is greater than 1kb
        if content_type in TYPES_TO_COMPRESS and len(filedata) > 1024:
            filedata = zlib.compress(filedata)[2:-4] # strip zlib header and checksum
            headers["Content-Encoding"] = "deflate"

        # calculate md5 digest of filedata
        checksum = hashlib.md5(filedata)
        hexdigest = checksum.hexdigest()
        b64digest = base64.b64encode(checksum.digest())

        # check to see if local file has changed from what is on S3
        etag = self._entries.get(remote_path, '')
        if force or etag != hexdigest:

            # upload file
            key = Key(self._bucket)
            key.key = remote_path
            key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))

            self._entries[remote_path] = etag

            return True
