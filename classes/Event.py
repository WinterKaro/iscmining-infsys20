#!/usr/bin/python3
class Event:    
  def __init__(self, log, trace, attrib = {}):
    self.log = log
    self.trace = trace
    self.attrib = attrib
    
  def __repr__(self):
    return("Eventattribs: \n %s\n" % (self.attrib))
  
  def lb(self):
    return self.attrib['concept:name']
  
  def lc(self):
    if 'lifecycle:transition' in self.attrib:
      return self.attrib['lifecycle:transition']
    return None
  
  def ts(self):
    return self.attrib['time:timestamp']
  
  def rs(self):
    if 'org:resource' in self.attrib.keys():
      return self.attrib['org:resource'] 
    return None
