#!/usr/bin/python3
import time
import dateutil
import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from datetime import timedelta
import os.path
from classes.Trace import *
from classes.EHandler import *
from classes.Algorithm import *
from classes.SetEncoder import*
from classes.EventPair import *
from classes.Heuristics import *
from classes.ISCGraph import *
import re
import collections
import pickle

class ISCObject:
  def __init__(self,fn,paths,args):
    self.lifecycle_options = {'lifecycle_exists':1,'lifecycle_options':set()}
    self.logs = {}
    self.start_events = {}
    self.end_events = {}
    self.fn = fn    #filename
    self.algos= dict()
    self.paths = paths
    self.args = args
    self.heuristics = []
    for path in paths:
      ev_map = collections.defaultdict(int)
      parser = SX.make_parser()
      handler = EHandler(path,self.logs,self.start_events,self.end_events,self.lifecycle_options,ev_map)
      parser.setContentHandler(handler)
      parser.parse(path)
    self.mt = self.merge_traces()
    self.create_results()
    for path in paths:
      self.heuristics.append(Heuristics(re.sub(".xes","", os.path.basename(path)), self.logs[path],self.lifecycle_options,self.start_events[path],self.end_events[path]))
      
  def get_attribset(self):
    ret = set()
    for logname,traces in self.logs.items():
      for tracename,trace in traces.items():
        for k,v in trace.attribset.items():
          if len(v)==1 and k!="concept:instance" and k!="cpee:uuid":    #cpee specific checks added
            ret.add(k)
    for logname,traces in self.logs.items():
      for tracename,trace in traces.items():
        for e in trace.events:
          ret = ret.intersection(set(e.attrib.keys()));
    return ret

  def merge_traces(self):
    ret = {}  #inp => [events]
    if len(self.logs.keys())== 1:
      for logname,traces in self.logs.items():
        for tracename,trace in traces.items():
          ret[tracename]=trace.events
      return ret
    attribs = list(self.get_attribset())
    if len(attribs)==1:
      inp = attribs[0]
      self.args.mergeattribute=attribs[0]
    elif self.args.mergeattribute:
      for att in attribs:
        if att == self.args.mergeattribute:
          inp = att
    else:
      raise ValueError("There is no possibility to merge all traces. Either there is no option or too many. If there is more than one, please use the config file")
    for logname,traces in self.logs.items():
      for tracename,trace in traces.items():
        if inp in trace.attribset.keys():
          if len(trace.attribset[inp])>1:
            raise RuntimeError("Only unique trace identifiers possible for merging.")
          temp = list(trace.attribset[inp])
          if temp[0] not in ret:
            ret[temp[0]]=[]
          ret[temp[0]].extend(trace.events)
    for trname,events in ret.items():
      events.sort(key=lambda x: parse(x.attrib['time:timestamp']))
    return ret
    
  def create_results(self):
    if self.args.a1:
        self.algos['a1'] = Algorithm_1(self.args,self)
    if self.args.a2:
        self.algos['a2'] = Algorithm_2(self.args,self)
    if self.args.a3:
      try:
        self.algos['a3'] = Algorithm_3(self.args,self)
      except RuntimeError as err:
         print("RuntimeError: {0} ".format(err))
         self.args.a3=False
    if self.args.a4:
      try:
        self.algos['a4'] = Algorithm_4(self.args,self)
      except RuntimeError as err:
         print("RuntimeError: {0} ".format(err))
         self.args.a4=False
  
  #pickle.load() currently missing-can be inserted to speed processing  
  def write_results(self):
    if 'a1' in self.algos:
        self.algos['a1'].write(os.path.join(self.fn,"json","algo_1"))
        try:
          iscg = ISCGraph(os.path.join(self.fn,"pdf","algo_1"), self.heuristics, self.algos['a1'].result,"_".join([self.fn.split("/")[-1],"algo_1"]))
          iscg.draw(float(self.args.minerabs),float(self.args.minerrel), False)
          pickle.dump(iscg,open(os.path.join(self.fn,"pickle","algo_1.p"),"wb"))
        except RuntimeError as err:
          print("RuntimeError: {0} ".format(err))
    if 'a2' in self.algos:
        self.algos['a2'].write(os.path.join(self.fn,'json',"algo_2"))
        try:
          for key, value in self.algos['a2'].result.items():
            iscg = ISCGraph(os.path.join(self.fn,'pdf',"algo_2")+'_'+key, self.heuristics, value,"_".join([self.fn.split("/")[-1],"algo_2_"+key]))
            iscg.draw_algo2(float(self.args.minerabs), float(self.args.minerrel))
            pickle.dump(iscg,open(os.path.join(self.fn,"pickle","algo_2_"+key+".p"),"wb"))
        except RuntimeError as err:
         print("RuntimeError: {0} ".format(err))
    if 'a3' in self.algos:
        self.algos['a3'].write(os.path.join(self.fn,'json',"algo_3"))
        try:
          iscg = ISCGraph(os.path.join(self.fn,'pdf',"algo_3"), self.heuristics,self.algos['a3'].result,"_".join([self.fn.split("/")[-1],"algo_3"]))
          iscg.draw(float(self.args.minerabs), float(self.args.minerrel), True)
          pickle.dump(iscg,open(os.path.join(self.fn,"pickle","algo_3.p"),"wb"))
        except RuntimeError as err:
          print("RuntimeError: {0} ".format(err))
    if 'a4' in self.algos:
        self.algos['a4'].write(os.path.join(self.fn,'json',"algo_4"))
        try:
          iscg = ISCGraph(os.path.join(self.fn,'pdf',"algo_4"), self.heuristics,self.algos['a4'].result,"_".join([self.fn.split("/")[-1],"algo_4"]))
          iscg.draw(float(self.args.minerabs), float(self.args.minerrel), False)
          pickle.dump(iscg,open(os.path.join(self.fn,"pickle","algo_4.p"),"wb"))
        except RuntimeError as err:
          print("RuntimeError: {0} ".format(err))
