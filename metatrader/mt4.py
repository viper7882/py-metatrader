# -*- coding: utf-8 -*-
"""
@author: samuraitaiga
"""
import os
import sys
import logging
import subprocess

try:
    import winreg
except:
    import _winreg as winreg
import codecs

_mt4s = {}
_portable_mode = False

DEFAULT_MT4_NAME = 'default'
# mt4 program file path is written in origin.txt
ORIGIN_TXT = 'origin.txt'
MT4_EXE = 'terminal.exe'


class MT4(object):
    """
    Notes:
      meta trader4 class which can lunch metatrader4.
      this class will only lunch metatrader4,
      because metatrader4 can lunch either normal mode or backtest mode.
    """
    prog_path = None
    appdata_path = None

    def __init__(self, prog_path):
        self.prog_path_raw = prog_path
        self.get_appdata_path

    @property
    def get_appdata_path(self):
        if os.path.exists(self.prog_path_raw):
            self.prog_path = self.prog_path_raw
            if ((is_uac_enabled() == True) and (_portable_mode == False)):
                self.appdata_path = get_appdata_path(self.prog_path_raw)
            else:
                self.appdata_path = self.prog_path_raw

        else:
            err_msg = 'prog_path_raw %s not exists' % self.prog_path_raw
            logging.error(err_msg)
            raise IOError(err_msg)

        if not has_mt4_subdirs(self.appdata_path):
            err_msg = 'appdata path %s has not sufficient dirs' % self.appdata_path
            logging.error(err_msg)
            raise IOError(err_msg)

    def run(self, ea_name, conf=None, portable_mode=False):
        """
        Notes:
          run terminal.exe.
        Args:
          conf(string): abs path of conf file.
            details see mt4 help doc Client Terminal/Tools/Configuration at Startup
        """
        import subprocess

        if conf:
            if portable_mode == False:
                prog = '"%s"' % os.path.join(self.prog_path, MT4_EXE)
            else:
                prog = '"%s" /portable' % os.path.join(self.prog_path, MT4_EXE)
            conf = '"%s"' % conf
            cmd = '%s %s' % (prog, conf)

            p = subprocess.Popen(cmd)
            p.wait()
            if ((p.returncode == 0) or (p.returncode == 3)):
                # Logging info will cause command prompt to wait for enter key which is not required in this case
                #logging.info('cmd[%s] succeeded', cmd)
                pass
            else:
                err_msg = 'run mt4 with cmd[%s] failed with %d error code!!' % (cmd, p.returncode)
                logging.error(err_msg)
                raise RuntimeError(err_msg)


def has_mt4_subdirs(appdata_path):
    """
    Note:
      check this appdata path has required mt4 sub dirs.
      currently chech backtest related dirs.
      - history
      - profiles
      - tester
      - MQL4\\Experts
      - MQL4\\Libraries
    Returns:
      True if has required mt4 sub dirs,
      False if doesn't have
    """
    sub_dirs = [os.path.join(appdata_path, 'history'),
                os.path.join(appdata_path, 'profiles'),
                os.path.join(appdata_path, 'tester'),
                os.path.join(appdata_path, 'MQL4', 'Experts'),
                os.path.join(appdata_path, 'MQL4', 'Libraries')]
    ret = True

    for sub_dir in sub_dirs:
        if not os.path.exists(sub_dir) and not os.path.isdir(sub_dir):
            ret = False

    return ret


def is_uac_enabled():
    """
    Note:
      check uac is enabled or not from reg value.
    Returns:
     True if uac is enabled, False if uac is disabled.
    """
    import winreg

    reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_READ)
    value, regtype = winreg.QueryValueEx(reg_key, 'EnableLUA')

    if value == 1:
        # reg value 1 means UAC is enabled
        return True
    else:
        return False


def get_appdata_path(program_file_dir):
    """
    Returns:
      AppData path corresponding to provided program file path
      e.g.: C:\\Users\\UserName\\AppData\\Roaming\\MetaQuotes\\Terminal\\7269C010EA668AEAE793BEE37C26ED57
    """
    app_data = os.environ.get('APPDATA')
    mt4_appdata_path = os.path.join(app_data, 'MetaQuotes', 'Terminal')

    app_dir = None

    walk_depth = 1
    for root, dirs, files in os.walk(mt4_appdata_path):
        # search ORIGIN_TXT until walk_depth
        depth = root[len(mt4_appdata_path):].count(os.path.sep)

        if ORIGIN_TXT in files:
            origin_file = os.path.join(root, ORIGIN_TXT)

            import codecs
            with codecs.open(origin_file, 'r', 'utf-16') as fp:
                line = fp.read()
                if line == program_file_dir:
                    app_dir = root
                    break

        if depth >= walk_depth:
            dirs[:] = []

    if app_dir == None:
        err_msg = '%s does not have appdata dir!.' % program_file_dir
        logging.error(err_msg)
        raise IOError(err_msg)

    return app_dir


def initizalize(ntpath, alias = DEFAULT_MT4_NAME):
    """
    Notes:
      initialize mt4
    Args:
      ntpath(string): mt4 install folder path.
        e.g.: C:\\Program Files (x86)\\MetaTrader 4 - Alpari Japan
      alias(string): mt4 object alias name. default value is DEFAULT_MT4_NAME
    """
    global _mt4s
    if alias not in _mt4s:
        # store mt4 object with alias name
        _mt4s[alias] = MT4(ntpath, )
    else:
        logging.info('%s is already initialized' % alias)


def get_mt4(alias = DEFAULT_MT4_NAME, portable_mode = False):
    """
    Notes:
      return mt4 object which is initialized.
    Args:
      alias(string): mt4 object alias name. default value is DEFAULT_MT4_NAME
    Returns:
      mt4 object(metatrader.backtest.MT4): instantiated mt4 object
    """
    global _mt4s
    global _portable_mode
    
    _portable_mode = portable_mode

    if alias in _mt4s:
        _mt4s[alias].get_appdata_path
        return _mt4s[alias]
    else:
        raise RuntimeError('mt4[%s] is not initialized.' % alias)
