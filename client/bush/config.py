import os
import yaml
import appdirs
import pkg_resources


def get_configpaths(filename="config.yaml"):
    a = appdirs.AppDirs("bush")
    for loc in (a.user_config_dir, a.site_config_dir):
        yield os.path.join(loc, filename)


def get_configfile(filename="config.yaml", mode="r"):

    for filepath in get_configpaths(filename):
        try:
            return open(filepath, mode)
        except OSError:
            pass

    return pkg_resources.resource_stream(__name__, filename)


def load_config(stream=None, *args, **kwargs):

    if stream is not None:
        return yaml.load(stream)

    with get_configfile(*args, **kwargs) as cf:
        return yaml.load(cf)
