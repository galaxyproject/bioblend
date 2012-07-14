import os
import ConfigParser

# By default we use two locations for the blend configurations,
# /etc/blend.cfg and ~/.blend (which works on Windows and Unix).
BlendConfigPath = '/etc/blend.cfg'
BlendConfigLocations = [BlendConfigPath]
UserConfigPath = os.path.join(os.path.expanduser('~'), '.blend')
BlendConfigLocations.append(UserConfigPath)


class Config(ConfigParser.SafeConfigParser):
    def __init__(self, path=None, fp=None, do_load=True):
        ConfigParser.SafeConfigParser.__init__(self, {'working_dir': '/mnt/pyami',
                                                      'debug': '0'})
        if do_load:
            if path:
                self.load_from_path(path)
            elif fp:
                self.readfp(fp)
            else:
                self.read(BlendConfigLocations)

    def get_value(self, section, name, default=None):
        return self.get(section, name, default)

    def get(self, section, name, default=None):
        try:
            val = ConfigParser.SafeConfigParser.get(self, section, name)
        except:
            val = default
        return val

    def getint(self, section, name, default=0):
        try:
            val = ConfigParser.SafeConfigParser.getint(self, section, name)
        except:
            val = int(default)
        return val

    def getfloat(self, section, name, default=0.0):
        try:
            val = ConfigParser.SafeConfigParser.getfloat(self, section, name)
        except:
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
