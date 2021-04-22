#!/usr/bin/python3
class Trace:# {{{
  def __init__(self, log, trace, events):
    self.log = log
    self.trace = trace
    self.events = events
    self.attribset = {}   # contains each unique attribute key and unique value in this trace
    for e in events:
      for k,v in e.attrib.items():
        if k in self.attribset:
          self.attribset[k].add(v)
        else:
          self.attribset[k] = {v}
          
  def __repr__(self):
    return("Log: %s \nTrace: %s\n\Events:\n%s" %(self.log,self.trace,self.events))
# }}}
