#!/usr/bin/python3
from graphviz import Digraph
from classes.ISCObject import *

class Heuristics:
  def __init__(self,logname, logfile,lc_options,starte,ende):
    self.logname = logname
    self.logfile = logfile
    self.directly_follows_abs = None
    self.directly_follows_rel = None
    self.start_events = starte
    self.end_events = ende
    directly_follows_abs = dict()
    for trname,trace in logfile.items():
      events = trace.events
      for idx1,ev1 in enumerate(events):
        if lc_options['lifecycle_exists'] == 1 and len(lc_options['lifecycle_options']) > 1 and  ev1.attrib['lifecycle:transition'] != "start":
          continue
        for idx2 in range(idx1+1,len(events)):
          ev2 = events[idx2]
          if(lc_options['lifecycle_exists'] == 1 and (ev2.attrib['lifecycle:transition'] == "start" or len(lc_options['lifecycle_options']) == 1) or lc_options['lifecycle_exists'] == 0): #and ev2.log != ev1.log):
            if (ev1.attrib['concept:name'], ev2.attrib['concept:name']) not in directly_follows_abs:
              directly_follows_abs[(ev1.attrib['concept:name'], ev2.attrib['concept:name'])] = 0
              directly_follows_abs[(ev2.attrib['concept:name'], ev1.attrib['concept:name'])] = 0
            directly_follows_abs[(ev1.attrib['concept:name'], ev2.attrib['concept:name'])]+=1
            break
    directly_follows_rel = dict()
    for key in directly_follows_abs:
      if(key[0]==key[1]):
        directly_follows_rel[key]= float(directly_follows_abs[key])/(directly_follows_abs[key]+1)
      else:
        x = directly_follows_abs[key]
        directly_follows_rel[key]= float(x - directly_follows_abs[(key[1],key[0])])/(directly_follows_abs[key]+directly_follows_abs[(key[1],key[0])]+1)
    self.directly_follows_abs = directly_follows_abs
    self.directly_follows_rel = directly_follows_rel

  def create_graph(self,ab_th,rel_th):
    d_graph = dict()
    for key in self.directly_follows_abs:
      if(self.directly_follows_abs[key]>=ab_th and self.directly_follows_rel[key]>=rel_th):
        d_graph[key]=self.directly_follows_abs[key]
    dot = Digraph(name='cluster_'+self.logname)
    keys1 = set()
    keys2 = set()
    for key in d_graph:
      keys1.add(key[0])
      keys2.add(key[1])
    keys = keys1.union(keys2)
    start = self.start_events
    end = self.end_events
    for s in start:
      dot.node(str(s))
      dot.edge('start_'+self.logname,str(s))
    for e in end:
      dot.node(str(e))
      dot.edge(str(e), 'end_'+self.logname)
    for key in keys:
      dot.node(str(key))
    for key in d_graph:
      dot.edge(str(key[0]),str(key[1]), label = ' '+'('+repr(self.directly_follows_abs[key])+') '+repr(round(self.directly_follows_rel[key], 3)))
    return dot
