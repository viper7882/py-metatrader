# -*- coding: utf-8 -*-
'''
Created on 2015/01/25

@author: samuraitaiga
'''
from __future__ import absolute_import, division
import os
from metatrader.mt4 import get_mt4
from metatrader.mt4 import DEFAULT_MT4_NAME
from metatrader.report import BacktestReport
from metatrader.report import OptimizationReport
from builtins import str


class BackTest(object):
    """
    Attributes:
      ea_name(string): ea name
      param(dict): ea parameter
      symbol(string): currency symbol. e.g.: USDJPY
      from_date(datetime.datetime): backtest from date
      to_date(datetime.datetime): backtest to date
      model(int): backtest model
        0: Every tick
        1: Control points
        2: Open prices only
      spread(int): spread
      optimization(bool): optimization flag. optimization is enabled if True
      replace_report(bool): replace report flag. replace report is enabled if True

    """

    def __init__(self, ea_name, param, symbol, period, from_date, to_date, model=0, spread=5, replace_report=True, read_report=True, portable_mode=True):
        self.ea_full_path = ea_name
        self.ea_path, self.ea_name = os.path.split(ea_name)
        self.param = param
        self.symbol = symbol
        self.period = period
        self.from_date = from_date
        self.to_date = to_date
        self.model = model
        self.spread = spread
        self.replace_report = replace_report
        self.read_report = read_report
        self.portable_mode = portable_mode
        self.optimization = False

    def _prepare(self, alias=DEFAULT_MT4_NAME):
        """
        Notes:
          create backtest config file and parameter file
        """
        self._create_conf(alias=alias)
        self._create_param(alias=alias)

    def _create_conf(self, alias=DEFAULT_MT4_NAME):
        """
        Notes:
          create config file(.conf) which is used parameter of terminal.exe
          in %APPDATA%\\MetaQuotes\\Terminal\\<UUID>\\tester

          file contents goes to
            TestExpert=SampleEA
            TestExpertParameters=SampleEA.set
            TestSymbol=USDJPY
            TestPeriod=M5
            TestModel=0
            TestSpread=5
            TestOptimization=true
            TestDateEnable=true
            TestFromDate=2014.09.01
            TestToDate=2015.01.05
            TestReport=SampleEA
            TestReplaceReport=false
            TestShutdownTerminal=true
        """

        mt4 = get_mt4(alias = alias, portable_mode = self.portable_mode)
        #print ('_create_conf, self.portable_mode: %r, mt4.appdata_path: %s' % (self.portable_mode, mt4.appdata_path))
        conf_file = os.path.join(mt4.appdata_path, 'tester', '%s.conf' % self.ea_name)

        # shutdown_terminal must be True.
        # If false, popen don't end and backtest report analyze don't start.
        shutdown_terminal = True

        with open(conf_file, 'w') as fp:
            fp.write('TestExpert=%s\n' % self.ea_full_path)
            fp.write('TestExpertParameters=%s.set\n' % self.ea_name)
            fp.write('TestSymbol=%s\n' % self.symbol)
            fp.write('TestPeriod=%s\n' % self.period)
            fp.write('TestModel=%s\n' % self.model)
            fp.write('TestSpread=%s\n' % self.spread)
            fp.write('TestOptimization=%s\n' % str(self.optimization).lower())
            fp.write('TestDateEnable=true\n')
            fp.write('TestFromDate=%s\n' % self.from_date.strftime('%Y.%m.%d'))
            fp.write('TestToDate=%s\n' % self.to_date.strftime('%Y.%m.%d'))
            fp.write('TestReport=%s\n' % self.ea_name)
            fp.write('TestReplaceReport=%s\n' % str(self.replace_report).lower())
            fp.write('TestShutdownTerminal=%s\n' % str(shutdown_terminal).lower())

    def _create_param(self, alias=DEFAULT_MT4_NAME):
        """
        Notes:
          create ea parameter file(.set) in %APPDATA%\\MetaQuotes\\Terminal\\<UUID>\\tester
        Args:
          ea_name(string): ea name
        """
        mt4 = get_mt4(alias = alias, portable_mode = self.portable_mode)
        #print ('_create_param, self.portable_mode: %r, mt4.appdata_path: %s' % (self.portable_mode, mt4.appdata_path))
        param_file = os.path.join(mt4.appdata_path, 'tester', '%s.set' % self.ea_name)

        with open(param_file, 'w') as fp:
            for k in self.param:
                values = self.param[k].copy()
                value = values.pop('value')
                fp.write('%s=%s\n' % (k, value))
                if self.optimization:
                    if values.has_key('max') and values.has_key('interval'):
                        fp.write('%s,F=1\n' % k)
                        fp.write('%s,1=%s\n' % (k, value))
                        interval = values.pop('interval')
                        fp.write('%s,2=%s\n' % (k, interval))
                        maximum = values.pop('max')
                        fp.write('%s,3=%s\n' % (k, maximum))
                    else:
                        # if this value won't be optimized, write unused dummy data for same format.
                        fp.write('%s,F=0\n' % k)
                        fp.write('%s,1=0\n' % k)
                        fp.write('%s,2=0\n' % k)
                        fp.write('%s,3=0\n' % k)
                else:
                    if type(value) == str:
                        # this ea arg is string. then don't write F,1,2,3 section in config
                        pass
                    else:
                        # write unused dummy data for same format.
                        fp.write('%s,F=0\n' % k)
                        fp.write('%s,1=0\n' % k)
                        fp.write('%s,2=0\n' % k)
                        fp.write('%s,3=0\n' % k)

    def _get_conf_abs_path(self, alias=DEFAULT_MT4_NAME, portable_mode = False):
        mt4 = get_mt4(alias = alias, portable_mode = portable_mode)
        #print ('_get_conf_abs_path, portable_mode: %r, mt4.appdata_path: %s' % (portable_mode, mt4.appdata_path))
        conf_file = os.path.join(mt4.appdata_path, 'tester', '%s.conf' % self.ea_name)
        return conf_file

    def run(self, alias=DEFAULT_MT4_NAME):
        """
        Notes:
          run backtest
        """
        self.optimization = False
        ret = None

        self._prepare(alias=alias)
        bt_conf = self._get_conf_abs_path(alias = alias, portable_mode = self.portable_mode)

        mt4 = get_mt4(alias = alias, portable_mode = self.portable_mode)
        #print ('run, self.portable_mode: %r, mt4.appdata_path: %s, bt_conf: %s' % (self.portable_mode, mt4.appdata_path, bt_conf))
        mt4.run(self.ea_name, conf=bt_conf, portable_mode = self.portable_mode)

        if self.read_report == True:
            ret = BacktestReport(self)
        return ret

    def optimize(self, alias=DEFAULT_MT4_NAME):
        """
        """
        self.optimization = True
        ret = None
        self._prepare(alias=alias)
        bt_conf = self._get_conf_abs_path(alias = alias, portable_mode = self.portable_mode)

        mt4 = get_mt4(alias = alias, portable_mode = self.portable_mode)
        #print ('optimize, self.portable_mode: %r, mt4.appdata_path: %s, bt_conf: %s' % (self.portable_mode, mt4.appdata_path, bt_conf))
        mt4.run(self.ea_name, conf=bt_conf, portable_mode = self.portable_mode)

        if self.read_report == True:
            ret = OptimizationReport(self)
        return ret


def load_from_file(dsl_file):
    pass
