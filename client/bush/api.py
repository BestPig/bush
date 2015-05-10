import os
import sys
import cgi
import json
import tarfile
import tempfile
import urllib.parse

import arrow
import requests

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor


INFO = 0
LOW = 1
MODERATE = 2
HIGH = 3
EXTREME = 4


class BushFile():

    def __init__(self, tag, name, date=0, compressed=None, url=None, **kwargs):

        if compressed is None:
            compressed = name.endswith('.tar.gz')

        self.tag = tag
        self.compressed = compressed
        self.name = name[:-7] if self.compressed else name
        self.date = arrow.get(date)
        self.url = url

    def __repr__(self):
        return "BushFile(tag=%s, name=%s, date=%s, compressed=%s)" % (
            self.tag, self.name, self.data, self.compressed)

    def output(self, file=sys.stdout, align=0, extended=False):
        if not extended:
            date = self.date.humanize()
        else:
            date = self.date.strftime("%Y-%m-%d %H:%M:%S")

        desc = "%s\t%-*s  -> %s" % (date, align, self.tag, self.name)

        if extended:
            desc += " [%s]" % self.url

        print(desc, file=file)


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
        for part in basename.split('.'):
            if part:
                return part
        return basename  # lol: this was only dots!

    def assert_response(self, r, acceptable=(200,)):
        if r.status_code not in acceptable:
            raise RuntimeError("HTTP status %d received." % r.status_code)

    def assert_status(self, r, acceptable=("OK",)):
        if r["status"] != 'OK':
            raise RuntimeError("Server is not OK despite sending 200 OK.")

    def check_target(self, dest, fdest, isdir=False, placeholder=True):

        if fdest != dest and not fdest.startswith(dest + os.sep):
            if not self.confirmation("Attempting to write to %r, "
                                     "outside target." % fdest,
                                     level=EXTREME):
                return False

        if isdir:
            try:
                if placeholder:
                    os.makedirs(fdest)
            except FileExistsError:
                pass
            return True

        try:
            if placeholder:
                open(fdest, "x").close()
            elif os.path.lexists(fdest):
                raise FileExistsError()
        except FileExistsError:
            if not self.confirmation("Attempting to write to %r, but file "
                                     "already exists." % fdest, level=HIGH):
                return False

            if not placeholder:
                os.unlink(fdest)

        return True

    def list(self):
        r = requests.get(self.url("index.php?request=list"))
        self.assert_response(r)
        return [BushFile(url=self.getddl(f['tag']), **f)
                for f in json.loads(r.text)]

    def upload(self, filepath, tag=None, callback=None):

        if isinstance(filepath, str):
            filepaths = [filepath]
        else:
            filepaths = filepath

        filepaths = list(map(os.path.abspath, filepaths))

        if tag is None and len(filepaths) != 1:
            raise ValueError("Must specify tag for multifile.")

        tag = tag or self.tag_for_path(filepaths[0])

        tmp = tempfile.TemporaryFile()
        tar = tarfile.open("bush_upload.tar.gz", "w:gz", fileobj=tmp)

        basenames = []

        for fp in filepaths:
            basename = os.path.basename(fp)
            basenames.append(basename)
            tar.add(fp, arcname=basename)

        tar.close()
        tmp.seek(0)

        filename = "%s.tar.gz" % ", ".join(basenames)
        encoder = MultipartEncoder(fields={
            'tag': tag,
            'file': (filename, tmp, 'application/octet-stream')
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

        self.assert_response(r, acceptable=(201,))
        data = r.json()
        self.assert_status(data)

        return tag

    def getddl(self, tag):
        tag = urllib.parse.quote(tag)
        return self.url("index.php?request=get&tag=%s" % tag)

    def download(self, tag, dest, callback=None, chunksz=8192):

        r = requests.get(self.url("index.php?request=get"),
                         params={"tag": tag}, stream=True)

        self.assert_response(r)

        ctype, params = cgi.parse_header(r.headers['Content-Disposition'])
        filename = params['filename']

        extract_archive = filename.endswith('.tar.gz')

        # This is delicate. If the destination isn't a
        # folder we want to rename the downloaded data
        # accordingly. However even if it is a folder
        # we still want to get the name if we are about
        # to extract from an archive because we'll be
        # able to do smart things.
        if extract_archive or not os.path.isdir(dest):
            dest, filename = os.path.split(dest)

        dest = os.path.realpath(dest)

        todo = int(r.headers['Content-Length'])
        done = 0

        if callback is not None:
            callback = callback(todo)

        if extract_archive:
            # Use a temporary file for extraction.
            tmp = tempfile.TemporaryFile()
        else:
            # Or attempt to write to target directly.
            fdest = os.path.realpath(os.path.join(dest, filename))
            if not self.check_target(dest, fdest):
                return
            tmp = open(fdest, 'wb')

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

        # Otherwise we need to unpack it:

        tmp.seek(0)
        tar = tarfile.open(None, "r:gz", fileobj=tmp)

        members = tar.getmembers()

        # If the user's destination is not a folder filename is set.
        # In this case we need to do our best to rename the contents
        # of the archive to be this filename. But if there are multiple
        # files at the root of the archive this is not possible. In
        # that case we'll create a folder named filename and put
        # everything inside.

        roots = set(m.name.split(os.sep)[0] for m in members)
        singleroot = roots.pop() if len(roots) == 1 else None

        if not filename:
            def _transform(path):
                return path
        elif singleroot is not None:
            def _transform(path):
                # This is the tricky case: replace the root.
                if path == singleroot or path.startswith(singleroot + os.sep):
                    return filename + path[len(singleroot):]
                return path
        else:
            # There is a destination name but we can't rename
            # multiple entries, create a folder to hold them.

            try:
                os.mkdir(os.path.join(dest, filename))
            except FileExistsError:
                pass

            def _transform(path):
                return os.path.join(filename, path)

        for m in members:
            m.name = _transform(m.name)
            if m.issym() or m.islnk():
                m.linkname = _transform(m.linkname)

        # Make sure we check in order, we need have a chance to
        # create the parent directories before testing children.
        sortedmembers = sorted(members, key=lambda m: m.name)

        def check_member(member):
            fdest = os.path.join(dest, member.name)
            return self.check_target(dest, fdest, member.isdir(),
                                     placeholder=not member.issym())

        members = list(filter(check_member, sortedmembers))

        tar.extractall(path=dest, members=members)

    def delete(self, tag):

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
