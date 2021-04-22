#!/usr/bin/python3
import json
import collections 
from classes.Event import *
from classes.EventPair import *

class SetEncoder(json.JSONEncoder):# {{{
  def default(self, obj):
    if isinstance(obj, frozenset):
      return list(obj)
    if isinstance(obj, set):
      return list(obj)
    if isinstance(obj, collections.defaultdict):
      return dict(obj)
    if isinstance(obj,Event):
      return {"log" : obj.log,"trace" : obj.trace, "attrib" :  obj.attrib}
    if isinstance(obj,EventPair):
      return {'ev1':obj.ev1,'ev2':obj.ev2}
    if isinstance(obj,Hund):
      return {"name":obj.name}
    return json.JSONEncoder.default(self, obj)# }}}
