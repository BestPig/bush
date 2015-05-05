import pprint
import argparse
import progressbar

import bush.api


BASE_URL = "http://127.0.0.1/bush/server/"


def do_list_file(api, args):
    ret = api.list()
    return ret


def do_upload_file(api, args):
    ret = api.upload(args.file, tag=args.tag)
    return ret


def do_get_file(api, args):
    ret = api.download(args.tag, args.dest)
    return ret


def do_delete_file(api, args):
    ret = api.delete(args.tag)
    return ret


def do_reset_file(api, args):
    ret = api.reset()
    return ret


def main():

    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest='action')
    subs.required = True


    sub = subs.add_parser('ls', help="List informations about files already uploaded")
    sub.set_defaults(callback=do_list_file)


    sub = subs.add_parser('up', help="upload a new file")
    sub.set_defaults(callback=do_upload_file)

    sub.add_argument('file', help='path of the file to upload')
    sub.add_argument('tag', nargs="?", default=None,
                     help='tag, the name to specify to get the file easily')


    sub = subs.add_parser('dl', help="download a file")
    sub.set_defaults(callback=do_get_file)

    sub.add_argument('tag',
                     help='tag, the name to specify to get the file easily')
    sub.add_argument('dest', nargs='?', default='.',
                    help="destination directory where the file will be downloaded")


    sub = subs.add_parser('rm', help="remove an uploaded file")
    sub.set_defaults(callback=do_delete_file)

    sub.add_argument('tag', help='tag, the name to specify to delete the file easily')


    sub = subs.add_parser('reset', help="delete all files")
    sub.set_defaults(callback=do_reset_file)

    parser.add_argument('-u', '--url', help="API endpoint", default=BASE_URL)

    args = parser.parse_args()


    api = bush.api.BushAPI(args.url)
    ret = args.callback(api, args)
    pprint.pprint(ret)
