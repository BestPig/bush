import sys
import pprint
import argparse
import progressbar

from distutils import util

import bush.api
import bush.config


class ShowProgress():

    def __init__(self, total):

        widgets = [
            progressbar.Percentage(),
            ' ', progressbar.Bar(),
            ' ', progressbar.ETA(),
            ' ', progressbar.AdaptiveETA(),
            ' ', progressbar.AdaptiveTransferSpeed(),
            ]

        self.bar = progressbar.ProgressBar(widgets=widgets, maxval=total)
        self.bar.start()

    def __call__(self, update):
        self.bar.update(update)

    def __del__(self):
        self.bar.finish()


class UIAPI(bush.api.BushAPI):

    def confirmation(self, msg, level):
        print(msg, file=sys.stderr)

        try:
            status = util.strtobool(input("Do you want to proceed? (y/N) "))
        except ValueError:
            status = False

        return status


def do_list_file(api, args):
    files = api.list()
    maxlen = max(len(f['tag']) for f in files) if files else 0
    for f in files:
        print("%-*s  -> %s" % (maxlen, f['tag'], f['name'][:-7]))


def do_upload_file(api, args):
    api.upload(args.file, tag=args.tag, callback=ShowProgress)


def do_get_file(api, args):
    api.download(args.tag, args.dest, callback=ShowProgress)


def do_delete_file(api, args):
    api.delete(args.tag)


def do_reset_file(api, args):
    api.reset()


def main():

    parser = argparse.ArgumentParser(description="Simplistic file sharing. ",
                                     epilog="Configuration file is searched "
                                     "for in the following locations: %s" %
                                     ", ".join(bush.config.get_configpaths()))
    subs = parser.add_subparsers(dest='action')
    subs.required = True

    sub = subs.add_parser('ls', help="list information about available files")
    sub.set_defaults(callback=do_list_file)

    sub = subs.add_parser('up', help="upload a new file")
    sub.set_defaults(callback=do_upload_file)
    sub.add_argument('file', help='path of the file to upload')
    sub.add_argument('tag', nargs="?", default=None,
                     help='the name associated with the file to upload')

    sub = subs.add_parser('dl', help="download a file")
    sub.set_defaults(callback=do_get_file)
    sub.add_argument('tag',
                     help='the name associated with the file to download')
    sub.add_argument('dest', nargs='?', default='.',
                     help="path where the file should be downloaded")

    sub = subs.add_parser('rm', help="remove an uploaded file")
    sub.set_defaults(callback=do_delete_file)
    sub.add_argument('tag', help='the name associated with the file to delete')

    sub = subs.add_parser('reset', help="delete all files")
    sub.set_defaults(callback=do_reset_file)
    parser.add_argument('-u', '--url', help="API endpoint")
    parser.add_argument("-c", "--config", type=argparse.FileType("r"),
                        help="path overwriting the default configuration file")
    parser.add_argument('-d', '--debug', action='store_true',
                        help="full traceback for exceptions")

    args = parser.parse_args()

    config = bush.config.load_config(args.config)

    url = args.url or config.get('url')

    if url is None:
        exit("No URL specified, check your configuration or specify --url.")

    if not url.endswith('/'):
        print("""\
The API URL doesn't end with a '/', I'll go on and assume you know what
you are doing. But if something fails you might want to try to add one.""",
              file=sys.stderr)

    api = UIAPI(url)

    try:
        args.callback(api, args)
    except KeyboardInterrupt:
        pass  # Canceled by user :(
    except Exception if not args.debug else () as e:
        exit(e)
