import configparser
import os

BioBlendConfigPath = '/etc/bioblend.cfg'
BioBlendConfigLocations = [BioBlendConfigPath]
UserConfigPath = os.path.join(os.path.expanduser('~'), '.bioblend')
BioBlendConfigLocations.append(UserConfigPath)


class Config(configparser.ConfigParser):
    """
    BioBlend allows library-wide configuration to be set in external files.
    These configuration files can be used to specify access keys, for example.
    By default we use two locations for the BioBlend configurations:

    * System wide: ``/etc/bioblend.cfg``
    * Individual user: ``~/.bioblend`` (which works on both Windows and Unix)
    """
    def __init__(self, path=None, fp=None, do_load=True):
        super().__init__({'working_dir': '/mnt/pyami', 'debug': '0'})
        if do_load:
            if path:
                self.load_from_path(path)
            elif fp:
                self.readfp(fp)
            else:
                self.read(BioBlendConfigLocations)

    def get_value(self, section, name, default=None):
        return self.get(section, name, default)

    def get(self, section, name, default=None):
        """
        """
        try:
            val = super().get(section, name)
        except Exception:
            val = default
        return val

    def getint(self, section, name, default=0):
        try:
            val = super().getint(section, name)
        except Exception:
            val = int(default)
        return val

    def getfloat(self, section, name, default=0.0):
        try:
            val = super().getfloat(section, name)
        except Exception:
            val = float(default)
        return val

    def getbool(self, section, name, default=False):
        if self.has_option(section, name):
            val = self.get(section, name)
            if val.lower() == 'true':
                val = True
            else:
                val = False
        else:
            val = default
        return val
