import base64
import cStringIO
import datetime
import gzip
import hashlib
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.core.exceptions import ImproperlyConfigured
from mediasync.msettings import TYPES_TO_COMPRESS, AWS_KEY, AWS_SECRET, AWS_BUCKET, AWS_PREFIX, AWS_BUCKET_CNAME
from mediasync.backends import BaseClient

def _checksum(data):
    checksum = hashlib.md5(data)
    hexdigest = checksum.hexdigest()
    b64digest = base64.b64encode(checksum.digest())
    return (hexdigest, b64digest)

def _compress(s):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(s)
    zfile.close()
    return zbuf.getvalue()

class Client(BaseClient):
    def open(self):
        try:
            _conn = S3Connection(AWS_KEY, AWS_SECRET)
        except AttributeError:
            raise ImproperlyConfigured("S3 keys not set and no boto config found.")

        self._bucket = _conn.create_bucket(AWS_BUCKET)

    def remote_media_url(self, with_ssl=False):
        """
        Returns the base remote media URL. In this case, we can safely make
        some assumptions on the URL string based on bucket names, and having
        public ACL on.
        
        args:
          with_ssl: (bool) If True, return an HTTPS url.
        """
        protocol = 'http' if with_ssl is False else 'https'

        if AWS_BUCKET_CNAME:
            # Use a bucket CNAME, custom DNS.
            url = "%s://%s" % (protocol, AWS_BUCKET_CNAME)
        else:
            # Use standard AWS URL.
            url = "%s://s3.amazonaws.com/%s" % (protocol, AWS_BUCKET)

        if AWS_PREFIX:
            url = "%s/%s" % (url, AWS_PREFIX)

        return url

    def put(self, filedata, content_type, remote_path, force=False):
        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(self.expiration_days)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S GMT")

        if AWS_PREFIX:
            remote_path = "%s/%s" % (AWS_PREFIX, remote_path)

        (hexdigest, b64digest) = _checksum(filedata)
        raw_b64digest = b64digest # store raw b64digest to add as file metadata

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
            filedata = _compress(filedata)
            headers["Content-Encoding"] = "gzip"
            (hexdigest, b64digest) = _checksum(filedata) # update checksum with compressed data

        key = self._bucket.get_key(remote_path)

        if key is None:
            key = Key(self._bucket)
            key.key = remote_path

        s3_checksum = key.get_metadata('mediasync-checksum', '').replace(' ', '+')
        if force or s3_checksum != raw_b64digest:

            key.set_metadata('mediasync-checksum', raw_b64digest)
            key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))

            return True
