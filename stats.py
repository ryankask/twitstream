#!/usr/bin/env python

from collections import defaultdict
import types
import re
import math
import sys

# The key module provided here:
import twitstream

# Provide documentation:
USAGE = """stats.py [options] <key>

Extract statistics from the spritzer stream until interrupted.
Potential keys are: %s"""

link_re = re.compile(">([^<]+)</a>")

def linked(string):
    m = link_re.search(string)
    if m:
        return m.groups()[0]
    else:
        return string

def log_spacing(integer):
    m = math.sqrt(10)
    if integer == 0:
        return 0
    return m ** math.floor(math.log(integer, m))

def linear_chunk(interval):
    def linear(x):
        return interval * math.floor(x/interval)
    return linear

class Counter(object):
    def __init__(self, field):
        self.field = field
        self.path = self.FIELDS[field]
        self.counter = defaultdict(int)
    
    def __call__(self, status):
        key = status
        for elem in self.path:
            if isinstance(elem, types.FunctionType) or isinstance(elem, types.BuiltinFunctionType):
                key = elem(key)
            else:
                key = key[elem]
        self.counter[key] += 1
        print >> sys.stderr, ".",
        sys.stderr.flush()
    
    def top(self, count):
        if self.field in self.UNORDERED:
            hist = sorted(self.counter.items(), key=lambda x: x[1], reverse=True)
            for val in hist[:count]:
                print "%6d:\t%s" % (val[1], val[0])
        else:
            hist = sorted(self.counter.items(), key=lambda x: x[0])
            for val in hist:
                print "%6d:\t%d" % val
    
    FIELDS = {'source':     ('source', linked),
              'client':     ('source', linked),
              'user':       ('user', 'screen_name'),
              'timezone':   ('user', 'time_zone'),
              'followers':  ('user', 'followers_count', log_spacing),
              'friends':    ('user', 'friends_count', log_spacing),
              'favourites': ('user', 'favourites_count', log_spacing),
              'favorites':  ('user', 'favourites_count', log_spacing),
              'statuses':   ('user', 'statuses_count', log_spacing),
              'length':     ('text', len, linear_chunk(10)),
              }
    
    UNORDERED = set(('source', 'client', 'user', 'timezone'))

if __name__ == '__main__':
    parser = twitstream.parser
    parser.usage = USAGE % ", ".join(Counter.FIELDS)
    parser.add_option('-m', '--maximum', type='int', default=10,
        help="Maximum number of results to print (for non-numerical values) (default: 10, -1 for all)")
    (options, args) = parser.parse_args()
    
    if len(args) == 1 and args[0] in Counter.FIELDS:
        field = args[0]
    else:
        raise NotImplementedError("Requires exactly one argument from:\n%s" % ", ".join(Counter.FIELDS.keys()))
    
    twitstream.ensure_credentials(options)            
    count = Counter(field)
    
    stream = twitstream.spritzer(options.username, options.password, count, debug=options.debug)
    
    try:
        stream.run()
    except: 
        stream.cleanup()
        count.top(options.maximum)
        print "=" * 40
        print " Total: %d" % sum(count.counter.values())
    
