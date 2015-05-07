import os
import cgi
import json
import tarfile
import tempfile
import urllib.parse

import requests

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


INFO = 0
LOW = 1
MODERATE = 2
HIGH = 3
EXTREME = 4


class BushAPI():

    def __init__(self, base, token=None):
        self.base = base
        self.token = token

    def confirmation(self, msg, level):
        # Don't confirm anything by default!
        if level > INFO:
            raise RuntimeError(msg)

    def url(self, url):
        return urllib.parse.urljoin(self.base, url)

    def tag_for_path(self, filepath):
        basename = os.path.basename(filepath)
        return next(part for part in basename.split('.') if part)

    def sanitize_tag(self, tag):
        for sufix in [".tar.gz"]:
            if tag.endswith(sufix):
                tag = tag[:-len(sufix)]
        return tag

    def assert_response(self, r, acceptable=(200,)):
        if r.status_code not in acceptable:
            raise RuntimeError("HTTP status %d received." % r.status_code)

    def assert_status(self, r, acceptable=("OK",)):
        if r["status"] != 'OK':
            raise RuntimeError("Server is not OK despite sending 200 OK.")

    def check_target(self, dest, fdest):

        ok = True

        if ok and fdest != dest and not fdest.startswith(dest + os.sep):
            ok = self.confirmation(
                "Attempting to write to %r, outside target." % fdest,
                level=EXTREME)

        if ok and (os.path.isfile(fdest) or os.path.isdir(fdest)):
            ok = self.confirmation(
                "Attempting to write to %r, file already exists." % fdest,
                level=HIGH)

        return ok

    def list(self):
        r = requests.get(self.url("index.php?request=list"))
        self.assert_response(r)
        return json.loads(r.text)

    def upload(self, filepath, tag=None, callback=None):

        filepath = os.path.realpath(filepath)
        basename = os.path.basename(filepath)

        tag = tag or self.tag_for_path(filepath)
        tag = self.sanitize_tag(tag)

        tmp = tempfile.TemporaryFile()

        tar = tarfile.open("%s.tar.gz" % basename, "w:gz", fileobj=tmp)
        tar.add(filepath, arcname=basename)
        tar.close()

        tmp.seek(0)

        encoder = MultipartEncoder(fields={
            'tag': tag,
            'file': (basename, tmp, 'application/octet-stream')
        })

        if callback is not None:
            callback = callback(encoder.len)

            def _callback(monitor):
                callback(monitor.bytes_read)

        else:
            _callback = None

        monitor = MultipartEncoderMonitor(encoder, _callback)

        r = requests.post(self.url('index.php?request=upload'), data=monitor,
                          headers={'Content-Type': monitor.content_type})

        if _callback:
            del _callback

        self.assert_response(r)
        data = r.json()
        self.assert_status(data)

        return tag

    def download(self, tag, dest, callback=None, chunksz=8192):

        tag = self.sanitize_tag(tag)

        if dest == '-':
            dest = '/dev/stdout'
        else:
            dest = os.path.realpath(dest)

        r = requests.get(self.url("index.php?request=get"),
                         params={"tag": tag}, stream=True)

        self.assert_response(r)

        ctype, params = cgi.parse_header(r.headers['Content-Disposition'])
        filename = params['filename']

        todo = int(r.headers['Content-Length'])
        done = 0

        if callback is not None:
            callback = callback(todo)

        if not filename.endswith('.tar.gz'):
            extract_archive = False
            # Attempt to write to target directly.
            fdest = os.path.realpath(os.path.join(dest, filename))
            if not self.check_target(dest, fdest):
                return
            tmp = open(fdest, 'wb')

        else:
            extract_archive = True
            # Use a temporary file and extract it.
            tmp = tempfile.TemporaryFile()

        for chunk in r.iter_content(chunksz):
            tmp.write(chunk)
            done += len(chunk)

            if callback is not None:
                callback(done)

        del callback

        if todo != done:
            raise RuntimeError("Not enough data received.")

        if not extract_archive:
            return

        tmp.seek(0)

        # Otherwise we need to unpack it:

        tar = tarfile.open(None, "r:gz", fileobj=tmp)
        files = tar.getnames()

        for f in files:

            if len(files) != 1 or os.path.isdir(dest):
                fdest = os.path.realpath(os.path.join(dest, f))
            else:
                fdest = dest

            if not self.check_target(dest, fdest):
                continue

            fo = tar.getmember(f)

            # setting the absolute path, should ensure correct extraction.
            fo.path = fdest
            tar.extract(fo, fdest)

    def delete(self, tag):

        tag = self.sanitize_tag(tag)

        r = requests.get(self.url("index.php?request=delete"),
                         params={"tag": tag})

        self.assert_response(r)
        data = r.json()
        self.assert_status(data)

    def reset(self):

        r = requests.get(self.url("index.php?request=reset"))

        self.assert_response(r)

        data = r.json()
        self.assert_status(data)

        return data.get('files_deleted', 0)
