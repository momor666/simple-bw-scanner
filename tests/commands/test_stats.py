from sbws.util.parser import create_parser
from sbws.util.config import get_config
from sbws.lib.resultdump import ResultError
from sbws.lib.resultdump import ResultSuccess
from sbws.lib.resultdump import Result
import sbws.commands.init
import sbws.commands.stats
from datetime import date
import os
import time


class MockPastlyLogger:
    def __init__(self, *a, **kw):
        pass

    def debug(self, *s):
        print(*s)

    def info(self, *s):
        return self.debug(*s)

    def notice(self, *s):
        return self.info(*s)

    def warn(self, *s):
        return self.notice(*s)

    def error(self, *s):
        return self.warn(*s)


def init_directory(dname):
    p = create_parser()
    args = p.parse_args('-d {} -vvvv init'.format(dname).split())
    conf = get_config(args, log_fn=log.debug)
    sbws.commands.init.main(args, conf, log)


def add_single_stale_result(dname):
    r = ResultError(
        Result.Relay('DEADBEEF1111', 'CowSayWhat', '127.0.0.1'),
        ['DEADBEEF1111', 'BEADDEEF2222'],
        '127.0.1.1', 'SBWSclient', t=19950216)
    os.makedirs(os.path.join(str(dname), 'datadir'))
    dt = date.fromtimestamp(r.time)
    ext = '.txt'
    fname = os.path.join(str(dname), 'datadir', '{}{}'.format(dt, ext))
    with open(fname, 'wt') as fd:
        fd.write('{}\n'.format(str(r)))


def add_single_fresh_result(dname):
    r = ResultError(
        Result.Relay('DEADBEEF1111', 'CowSayWhat', '127.0.0.1'),
        ['DEADBEEF1111', 'BEADDEEF2222'],
        '127.0.1.1', 'SBWSclient', t=time.time())
    os.makedirs(os.path.join(str(dname), 'datadir'))
    dt = date.fromtimestamp(r.time)
    ext = '.txt'
    fname = os.path.join(str(dname), 'datadir', '{}{}'.format(dt, ext))
    with open(fname, 'wt') as fd:
        fd.write('{}\n'.format(str(r)))


def add_two_fresh_results(dname):
    r1 = ResultError(
        Result.Relay('DEADBEEF1111', 'CowSayWhat', '127.0.0.1'),
        ['DEADBEEF1111', 'BEADDEEF2222'],
        '127.0.1.1', 'SBWSclient', t=time.time())
    r2 = ResultSuccess(
        [1, 2, 3], [{'amount': 100, 'duration': 1}],
        Result.Relay('DEADBEEF1111', 'CowSayWhat', '127.0.0.1'),
        ['DEADBEEF1111', 'BEADDEEF2222'],
        '127.0.1.1', 'SBWSclient', t=time.time())
    os.makedirs(os.path.join(str(dname), 'datadir'))
    dt = date.fromtimestamp(r1.time)
    ext = '.txt'
    fname = os.path.join(str(dname), 'datadir', '{}{}'.format(dt, ext))
    with open(fname, 'wt') as fd:
        fd.write('{}\n'.format(str(r1)))
        fd.write('{}\n'.format(str(r2)))


log = MockPastlyLogger()


def test_stats_uninitted(tmpdir, capsys):
    '''
    An un-initialized .sbws directory should fail hard and exit immediately
    '''
    p = create_parser()
    args = p.parse_args('-d {} -vvvv stats'.format(tmpdir).split())
    conf = get_config(args, log_fn=log.debug)
    try:
        sbws.commands.stats.main(args, conf, log)
    except SystemExit as e:
        assert e.code == 1
    else:
        assert None, 'Should have failed'
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert 'Sbws isn\'t initialized. Try sbws init' == lines[-1]


def test_stats_initted(tmpdir, capsys):
    '''
    An initialized but rather empty .sbws directory should fail about missing
    ~/.sbws/datadir
    '''
    init_directory(tmpdir)
    p = create_parser()
    args = p.parse_args('-d {} -vvvv stats'.format(tmpdir).split())
    conf = get_config(args, log_fn=log.debug)
    try:
        sbws.commands.stats.main(args, conf, log)
    except SystemExit as e:
        assert e.code == 1
    else:
        assert None, 'Should have failed'
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert '{}/datadir does not exist'.format(tmpdir) == lines[-1]


def test_stats_stale_result(tmpdir, capsys):
    '''
    An initialized .sbws directory with no fresh results should say so and
    exit cleanly
    '''
    init_directory(tmpdir)
    add_single_stale_result(tmpdir)
    p = create_parser()
    args = p.parse_args('-d {} -vvvv stats'.format(tmpdir).split())
    conf = get_config(args, log_fn=log.debug)
    sbws.commands.stats.main(args, conf, log)
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert 'No fresh results' == lines[-1]


def test_stats_fresh_result(tmpdir, capsys):
    '''
    An initialized .sbws directory with a fresh error result should have some
    boring stats and exit cleanly
    '''
    init_directory(tmpdir)
    add_single_fresh_result(tmpdir)
    p = create_parser()
    args = p.parse_args(
        '-d {} -vvvv stats --error-types'.format(tmpdir).split())
    conf = get_config(args, log_fn=log.debug)
    sbws.commands.stats.main(args, conf, log)
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    needed_lines = [
        'Read 1 lines from {}/{}/{}.txt'.format(
            tmpdir, 'datadir', date.fromtimestamp(time.time())),
        'Keeping 1/1 results',
        '1 relays have recent results',
        'Average 0.00 successful measurements per relay',
        '0 success results and 1 error results',
    ]
    for needed_line in needed_lines:
        assert needed_line in lines


def test_stats_fresh_results(tmpdir, capsys):
    '''
    An initialized .sbws directory with a fresh error and fresh success should
    have some exciting stats and exit cleanly
    '''
    init_directory(tmpdir)
    add_two_fresh_results(tmpdir)
    p = create_parser()
    args = p.parse_args(
        '-d {} -vvvv stats --error-types'.format(tmpdir).split())
    conf = get_config(args, log_fn=log.debug)
    sbws.commands.stats.main(args, conf, log)
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    needed_lines = [
        'Read 2 lines from {}/{}/{}.txt'.format(
            tmpdir, 'datadir', date.fromtimestamp(time.time())),
        'Keeping 2/2 results',
        '1 relays have recent results',
        '1 success results and 1 error results',
        'Average 1.00 successful measurements per relay',
        'Found a _ResultType.Error for the first time',
        'Found a _ResultType.Success for the first time',
        '1/2 (50.00%) results were error-misc',
    ]
    for needed_line in needed_lines:
        assert needed_line in lines
