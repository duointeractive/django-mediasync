from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from mediasync.msettings import BACKEND, PROCESSORS, EXPIRATION_DAYS, SERVE_REMOTE, MEDIA_ROOT, MEDIA_URL, EMULATE_COMBO
from mediasync import processors

def client():
    if not BACKEND:
        raise ImproperlyConfigured('must define a mediasync BACKEND property')
    return load_backend(BACKEND)

def load_backend(backend_name):
    try:
        backend = import_module(backend_name)
        return backend.Client()
    except ImportError, e:
        raise ImproperlyConfigured(("%s is not a valid mediasync backend. \n" +
            "Error was: %s") % (backend_name, e))

class BaseClient(object):
    def __init__(self, *args, **kwargs):
        # mediasync settings
        self.expiration_days = EXPIRATION_DAYS
        self.serve_remote = SERVE_REMOTE

        self.local_media_url = self.get_local_media_url()
        self.media_root = self.get_media_root()

        # This will end up being a list of callables, if all goes well.
        self.processors = []
        for proc in PROCESSORS:
            if isinstance(proc, basestring):
                # Processor is a string value, try to import the module with
                # the same name.
                (module, attr) = proc.rsplit('.', 1)
                module = import_module(module)
                proc = getattr(module, attr, None)

            if isinstance(proc, type):
                proc = proc()

            if callable(proc):
                self.processors.append(proc)

    def get_local_media_url(self):
        """
        Broken out to allow overriding if need be.
        """
        return MEDIA_URL

    def get_media_root(self):
        """
        Broken out to allow overriding if need be.
        """
        return MEDIA_ROOT

    def media_url(self, with_ssl=False):
        """
        Used to return a base media URL. Depending on whether we're serving
        media remotely or locally, this either hands the decision off to the
        backend, or just uses the value in settings.MEDIA_URL.
        
        args:
          with_ssl: (bool) If True, return an HTTPS url (depending on how
                           the backend handles it).
        """
        if self.serve_remote:
            # Hand this off to whichever backend is being used.
            url = self.remote_media_url(with_ssl)
        else:
            # Serving locally, just use the value in settings.py.
            url = self.local_media_url
        return url.rstrip('/')

    def process(self, filedata, content_type, remote_path):
        """
        This method is used when syncing local media assets to S3, and when
        serving local media assets through Django during development. It
        iterates through all processors, which typically minify or slim
        assets, and returns the results (if the processors return a
        non-None value).
        
        filedata: (basestr) The content to process.
        content_type: (basestr) A valid mimetype.
        remote_path: (basestr) Remote path where the file will be served from
            (if applicable). Most important thing is that the filename and
            extension are present.
        """
        # self.processors is a now a list of callables.
        for proc in self.processors:
            # Only want to process stuff when self.serve_remote == True while
            # running ./manage.py syncmedia, or when EMULATE_COMBO is enabled
            # and we're running locally.
            processors_active = self.serve_remote or EMULATE_COMBO
            # This will be the content after the processor runs on it.
            prcssd_filedata = proc(filedata, content_type, remote_path, 
                                   processors_active)
            if prcssd_filedata is not None:
                # We got a useful value back from the processor, use it.
                filedata = prcssd_filedata
        return filedata

    def process_and_put(self, filedata, content_type, remote_path, force=False):
        """
        Processes the content, then put/saves it to your backend.
        """
        filedata = self.process(filedata, content_type, remote_path)
        return self.put(filedata, content_type, remote_path, force)

    def put(self, filedata, content_type, remote_path, force=False):
        raise NotImplementedError('put not defined in ' + self.__class__.__name__)

    def remote_media_url(self, with_ssl=False):
        raise NotImplementedError('remote_media_url not defined in ' + self.__class__.__name__)

    def open(self):
        pass

    def close(self):
        pass
