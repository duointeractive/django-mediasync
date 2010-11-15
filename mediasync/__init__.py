import os
import cStringIO
import mimetypes
from django.conf import settings
from mediasync.msettings import CSS_PATH, JS_PATH, JS_MIMETYPES, CSS_MIMETYPES, TYPES_TO_COMPRESS, JOINED
from mediasync import backends

class SyncException(Exception):
    pass

def is_syncable_dir(dir_str):
    return not dir_str.startswith('.') and not dir_str.startswith('_')

def is_syncable_file(file_str):
    return not file_str.startswith('.') and not file_str.startswith('_')

def listdir_recursive(dir_str):
    for root, dirs, files in os.walk(dir_str):
        # Go through and yank any directories that don't pass our syncable
        # dir test. This needs to be done in place so that walk() will avoid.
        for dir_candidate in dirs:
            if not is_syncable_dir(dir_candidate):
                dirs.remove(dir_candidate)

        basename = os.path.basename(root)
        if is_syncable_dir(basename):
            for file in files:
                fname = os.path.join(root, file).replace(dir_str, '', 1)
                if fname.startswith('/'):
                    fname = fname[1:]
                yield fname
        else:
            # "Skipping directory %s" % root
            pass

def combine_files(joinfile, sourcefiles, client):
    """
    Given a combo file name (joinfile), combine the sourcefiles into a single
    monolithic file.
    
    Returns a string containing the combo file, or None if the specified
    file can not be combo'd.
    """
    joinfile = joinfile.strip('/')

    if joinfile.endswith('.css'):
        dirname = CSS_PATH.strip('/')
    elif joinfile.endswith('.js'):
        dirname = JS_PATH.strip('/')
    else:
        # By-pass this file since we only join CSS and JS.
        return None

    buffer = cStringIO.StringIO()

    for sourcefile in sourcefiles:
        sourcepath = os.path.join(client.media_root, dirname, sourcefile)
        if os.path.isfile(sourcepath):
            f = open(sourcepath)
            buffer.write(f.read())
            f.close()
            buffer.write('\n')

    filedata = buffer.getvalue()
    buffer.close()
    return (filedata, dirname)

def sync(client=None, force=False):
    """ Let's face it... pushing this stuff to S3 is messy.
        A lot of different things need to be calculated for each file
        and they have to be in a certain order as some variables rely
        on others.
    """
    # create client connection
    if client is None:
        client = backends.client()

    client.open()
    client.serve_remote = True

    #
    # sync joined media
    #

    for joinfile, sourcefiles in JOINED.iteritems():
        filedata = combine_files(joinfile, sourcefiles, client)
        if filedata is None:
            # combine_files() is only interested in CSS/JS files.
            continue
        filedata, dirname = filedata

        content_type = mimetypes.guess_type(joinfile)[0] or 'application/octet-stream'

        remote_path = joinfile
        if dirname:
            remote_path = "%s/%s" % (dirname, remote_path)

        if client.process_and_put(filedata, content_type, remote_path, force=force):
            print "[%s] %s" % (content_type, remote_path)

    #
    # sync static media
    #

    for dirname in os.listdir(client.media_root):

        dirpath = os.path.abspath(os.path.join(client.media_root, dirname))

        if os.path.isdir(dirpath):

            for filename in listdir_recursive(dirpath):

                # calculate local and remote paths
                filepath = os.path.join(dirpath, filename)
                remote_path = "%s/%s" % (dirname, filename)

                content_type = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

                if not is_syncable_file(os.path.basename(filename)) or not os.path.isfile(filepath):
                    continue # hidden file or directory, do not upload

                filedata = open(filepath, 'rb').read()

                if client.process_and_put(filedata, content_type, remote_path, force=force):
                    print "[%s] %s" % (content_type, remote_path)

    client.close()


__all__ = ['sync', 'SyncException']
__version__ = '2.0.0dev'
