#!/usr/bin/python3
import sys
import json
import time
import collections
import dateutil
import datetime
from dateutil.parser import *
from dateutil.relativedelta import *
from datetime import timedelta
import statistics
import numpy as np
import numbers
np.seterr(divide='ignore',invalid='ignore')
import math
import os.path
import pickle
from classes.ISCObject import *
from classes.Trace import *
from sklearn import preprocessing
from sklearn import tree
from sklearn.tree import _tree
from sklearn.impute import SimpleImputer
from collections import OrderedDict
from classes.EventPair import *
from classes.SetEncoder import*
from operator import attrgetter

class Algorithm:
  def __init__(self,args):
    self.args = args
    self.results = None
    
  def calc(self,iscobj):
    print("calc")
    
  def filter(self,params):
    print("filter")
    
  def write(self,fn,data):
    new_data = dict()
    if(type(data) != list):
      for k,v in data.items():
        if(type(k) == tuple):
          new_data[str.join("/",k)]=v
        else:
          new_data[k] = v
    with open(fn,'w') as f:
      f.write(json.dumps(new_data,cls=SetEncoder,sort_keys=True,indent=4))
    f.closed
    
  def get_start_complete_events(self,mt):
    result = collections.defaultdict(list)
    for trname,events in mt:
      for idx1,ev1 in enumerate(events):
        for idx2 in range(idx1+1,len(events)):
          ev2 = events[idx2]
          if ev1.lb() == ev2.lb() and ev1.lc() == "start" and ev2.lc() == "complete":
            result[trname].append(EventPair(ev1,ev2))
            break
    return result


# simultaneous execution
class Algorithm_1(Algorithm):
  def __init__(self,args,iscobj):
    super().__init__(args)
    self.result = self.calc(iscobj)
    
  def calc(self,iscobj):
    ret = collections.defaultdict(list)
    events = []
    abs_event_occurences = collections.defaultdict(int)
    for logname,traces in iscobj.logs.items():
      for tracename,trace in traces.items():
        for ev in trace.events:
          if (iscobj.lifecycle_options['lifecycle_exists']==0 or len(iscobj.lifecycle_options['lifecycle_options'])==1 or (iscobj.lifecycle_options['lifecycle_exists']==1 and ev.lc() == "start")):
            events.append(ev)
            abs_event_occurences[ev.lb()]+=1
    events.sort(key=lambda event: event.ts())
    event_occurences = abs_event_occurences.copy()
    hit = False
    for idx,ev1 in enumerate(events):
      if idx<len(events)-1:
        j = idx+1
        for j in range(idx+1,len(events)):
          if (abs(parse(events[j].ts())-parse(ev1.ts())) <= datetime.timedelta(seconds=self.args.eps1)):
            if events[j].trace!=ev1.trace:
              hit = True
              break
          else:
            if hit:
              hit =False
            else:
              event_occurences[ev1.lb()]-=1
            break
    filtered_events = self.filter({"p1":abs_event_occurences,"p2":event_occurences})
    for i,ev in enumerate(events):
      if ev.lb() not in filtered_events:
        continue
      x = [ev]
      for j in range(i+1,len(events)):
        if events[j].lb() not in filtered_events:
          continue
        if (abs(parse(events[j].ts())-parse(ev.ts())) <= datetime.timedelta(seconds=self.args.eps1)):
          if(events[j].trace!=ev.trace):
            x.append(events[j])
        else:
          break
      if len(x)>1:
        foo = tuple({y.lb() for y in x})
        if len(foo) == 1:
          foo = foo[0]
        ret[foo].append(x.copy())
    return ret

  def filter(self,params):
    ret = []
    for key in params['p1'].keys():
      absolut_value = params['p1'][key]
      current_value = params['p2'][key]
      if (float(current_value)/absolut_value)>=self.args.g1:
        ret.append(key)
    return ret
    
  def write(self,fn):
    super().write(fn+".json",self.result)
    

# constrained execution
class Algorithm_2(Algorithm):
  def __init__(self,args,iscobj): 
    super().__init__(args)
    self.result = self.calc(iscobj)

  def create_pairs(self,pre):
    begin_end = collections.defaultdict(list)
    for trname, events in pre.mt.items():
      begin_end[(events[0].lb(), events[-1].lb())].append((events[0], events[-1], abs(parse(events[0].ts())-parse(events[-1].ts())).total_seconds()))
    start_start = collections.defaultdict(list)
    start_complete = collections.defaultdict(list)
    if pre.lifecycle_options['lifecycle_exists']==0 or pre.lifecycle_options['lifecycle_exists']==1 and len(pre.lifecycle_options['lifecycle_options'])==1:
        for trname,events in pre.mt.items():
          for i in range(0,len(events)-1):
            ev1 = events[i]
            ev2 = events[i+1]
            start_start[(ev1.lb(),ev2.lb())].append((ev1, ev2, abs(parse(ev1.ts())-parse(ev2.ts())).total_seconds()))
    else:
      for trname,events in pre.mt.items():
        for i in range(0,len(events)):
          ev1 = events[i]
          if ev1.lc() != 'start':
            continue
          for j in range(i+1,len(events)):
            ev2 = events[j]
            if ev1.lb() == ev2.lb() and ev2.lc() == 'complete':
              start_complete[(ev1.lb(), ev2.lb())].append((ev1, ev2, abs(parse(ev1.ts())-parse(ev2.ts())).total_seconds()))
              break
          for j in range(i+1,len(events)):
            ev2 = events[j]
            if ev2.lc() == 'start':
              delta = abs(parse(ev1.ts())-parse(ev2.ts())).total_seconds()
              start_start[(ev1.lb(),ev2.lb())].append((ev1, ev2, abs(parse(ev1.ts())-parse(ev2.ts())).total_seconds()))
              break
    return [begin_end, start_start, start_complete]


  def detectRegularities(self,pairs):
    if(self.args.limit2 is None and self.args.g2 is None):
      raise RuntimeError("Gamma and limit may not both be None.")
    if (self.args.limit2 is None and self.args.g2 is not None ):
      deltas = dict()
      for k,v in pairs.items():
        lim = math.floor(len(v) - float(self.args.g2) * len(v))
        deltas[k]= sorted(v,key=lambda event: event[2])[-lim]
    elif(self.args.limit2 is not None and self.args.g2 is None):
      deltas = collections.defaultdict(float)
      for key,val in pairs.items():
        count = 0
        for event in val:
          if(event[2] <= float(self.args.limit2)):
            count +=1
        deltas[key] = float(count)/len(val)
    else:
      deltas = dict()
      for key, val in pairs.items():
        count = 0
        for event in val:
          if(event[2] <= float(self.args.limit2)):
            count +=1
        if(count != 0 and float(count)/len(val) >= float(self.args.g2)):
          deltas[key] = True
        else:
          deltas[key] = False
    return deltas


  def detectExecutionConstraint(self,traces):
    result = collections.defaultdict(list)
    inter_day = collections.defaultdict(int)
    inter_day_res = collections.defaultdict(int)
    inter_event = collections.defaultdict(int)
    inter_event_res = collections.defaultdict(int)
    for trname, trace in traces.items():
      inter_day[parse(trace[0].ts()).date()] += 1
      if(trace[0].rs() is not None):
        inter_day_res[(parse(trace[0].ts()).date(), trace[0].rs())] +=1
      for event in trace:
        if(event.lc() is None or event.lc() == "start"):
          inter_event[(parse(event.ts()).date(), event.lb())] +=1
          if(event.rs() is not None):
            inter_event_res[(parse(event.ts()).date(), event.lb(), event.rs())] +=1
    result["day"] = self.filter({"p1":inter_day, "p2":self.args.g2}) #k=number of instances started, v=number of days on which k-times instances were started
    result["day_resource"] = self.filter({"p1":inter_day_res,"p2": self.args.g2})
    result["event"] = self.filter({"p1":inter_event, "p2":self.args.g2})
    result["event_resource"] = self.filter({"p1":inter_event_res, "p2":self.args.g2})
    return result


  def detectOutliers(self,pairs):
    outli = list()
    for k,v in pairs.items():
      deltas = list()
      # durch lambda ersetzen. TODO
      for x in v:
        deltas.append(x[2])
      if len(deltas)<2:
        continue
      m = statistics.mean(deltas)
      stdev = statistics.stdev(deltas)
      z_sc = list()
      for x in deltas:
        if stdev != 0:
          z_sc.append((x-m)/stdev)
        else:
          z_sc.append(float('nan'))
      for i in range(0,len(deltas)):
        if abs(z_sc[i])>3:
          outli.append(v[i])
    return outli


  def detectDataLimitation(self,pairs, outliers):
    rules = dict()
    for key, value in pairs.items():
      instances = list()
      for pair in value:
        if pair in outliers:
          instances.append([pair[0], pair[1],True,pair[2]])
        else:
          instances.append([pair[0], pair[1],False,pair[2]])
      res = self.computeRules(instances)
      if(res):
        rules[key] = res
    return rules


  def get_paths(self,val,l,c):
    for k,v in val.items():
      if(type(v) == dict):
        self.get_paths(val['left'],l,c + [(val['feature'], "<=", val['threshold'])])
        self.get_paths(val['right'],l,c + [(val['feature'], ">", val['threshold'])])
        return
    if val['class']==1:
      l.append(c)


  def get_set(self,val):
    s = set()
    for k,v in val.items():
      if(type(v) == dict):
        s = s.union(self.get_set(v))
    s.add(val['class'])
    return s

  def export_dict(self,tree, feature_names = None, max_depth = None):
    tree_ = tree.tree_
    def recur(i, depth=0):
      val = None
      if(max_depth is not None and depth > max_depth):
        return None
      if(i == _tree.TREE_LEAF):
        return None
      feature = int(tree_.feature[i])
      threshold = float(tree_.threshold[i])
      if(feature == _tree.TREE_UNDEFINED):
        feature = None
        threshold = None
        value = (map(float, l) for l in tree_.value[i].tolist())
        val = tree_.value[i]
      else:
        value = None
        if(feature_names):
          feature = feature_names[feature]
      return {'feature' : feature, 'threshold' : threshold,'impurity' : float(tree_.impurity[i]),'n_node_samples' : int(tree_.n_node_samples[i]),'left'  : recur(tree_.children_left[i],  depth + 1),'right' : recur(tree_.children_right[i], depth + 1), 'value' : value , 'class' : tree.classes_[np.argmax(val)]}
    return recur(0)

  def computeRules(self,instances):
    le_dict = collections.defaultdict(preprocessing.LabelEncoder)
    attr = OrderedDict();
    target_v = set();   #move to target []
    for pair in instances:
      target_v.add(pair[2])
      for akey,aval in pair[0].attrib.items():
        if (self.args.classifier and akey not in self.args.classifier) or (not self.args.classifier and akey == self.args.mergeattribute or "concept:" in akey or "lifecycle" in akey or "time:" in akey or "trace:" in akey or "uuid" in akey):
          continue
        akey += "1"
        if akey not in attr:
          attr[akey] = set()
        attr[akey].add(aval)
      for akey,aval in pair[1].attrib.items():
        if (self.args.classifier and akey not in self.args.classifier) or (not self.args.classifier and akey == self.args.mergeattribute or "concept:" in akey or "lifecycle" in akey or "time:" in akey or "trace:" in akey or "uuid" in akey):
          continue
        akey += "2"
        if akey not in attr:
          attr[akey] = set()
        attr[akey].add(aval)
    if not attr:
      return None
    for k,v in attr.items():
      t = list(v)
      if not isinstance(t[0], numbers.Number):
        le_dict[k].fit(list(v))
    target_names = list(target_v)
    le_dict['outlier'].fit(target_names)
    traces = list()
    targets = list()
    fn = str.join("_",[instances[0][0].lb(),instances[0][1].lb()]).replace(" ","")
    for pair in instances:
      targets.append(le_dict['outlier'].transform([pair[2]])[0])
      trace = []
      for k in attr:
        if (self.args.classifier and k not in self.args.classifier) or (not self.args.classifier and k == "outlier" or k == "delta" or k == self.args.mergeattribute or "concept:" in k or "lifecycle:" in k or "time:" in k):
          continue
        pair_id = k[-1]
        uid = k[:-1]
        if pair_id == "1":
          if uid not in pair[0].attrib:
            trace.append(np.nan);
          else:
            if k in le_dict:
              trace.append(le_dict[k].transform([pair[0].attrib[uid]])[0])
            else:
              trace.append(pair[0].attrib[uid])
        else:
          if uid not in pair[1].attrib:
            trace.append(np.nan);
          else:
            if k in le_dict:
              trace.append(le_dict[k].transform([pair[1].attrib[uid]])[0])
            else:
              trace.append(pair[1].attrib[uid])
      traces.append(trace)
    imp = SimpleImputer(missing_values=np.nan, strategy='mean')
    traces=imp.fit_transform(traces)
    clf = tree.DecisionTreeClassifier(max_depth=3, criterion='entropy')     #len(attr.keys()))
    clf = clf.fit(traces,targets)
    restree = self.export_dict(clf, list(attr.keys()))
    ll = list()
    if (len(target_names) > 1 and len(self.get_set(restree)) > 1):
      self.get_paths(restree,ll,[])
    return ll


  def calc(self,iscobj):
    limEvents = dict()
    pairs = self.create_pairs(iscobj) #pairs[0] = begin end; pairs[1] = start start; pairs[2] = start complete
    limEvents["regularities_instance_level"] = self.detectRegularities(pairs[0])
    limEvents["regularities_event_level_start_start"] = self.detectRegularities(pairs[1])
    limEvents["regularities_event_level_start_complete"] = self.detectRegularities(pairs[2])
    limEvents["execution_constraint"] = self.detectExecutionConstraint(iscobj.mt)
    outliers_start_start = self.detectOutliers(pairs[1])
    outliers_start_complete = self.detectOutliers(pairs[2])
    limEvents["data_constraint_start_start"] = self.detectDataLimitation(pairs[1], outliers_start_start)
    limEvents["data_constraint_start_complete"] = self.detectDataLimitation(pairs[2], outliers_start_complete)
    return limEvents
  

  def filter(self,params):
    result = list()
    count_same = collections.defaultdict(int)
    count_total = collections.defaultdict(int)
    for k1, v1 in params['p1'].items():
      for k2, v2 in params['p1'].items():
        #if(k1==k2):
        #  continue
        if(type(k1) == datetime.date and v1==v2):
          count_same[v1] +=1
          break
        elif(type(k1) == tuple and len(k1) == 2 and k1[1]==k2[1]):
          count_total[k1[1]] +=1
          if(v1==v2):
            count_same[(v1,k1[1])] +=1
          break
        elif(type(k1) == tuple and len(k1) == 3 and k1[1]==k2[1] and k2[2]==k2[2]):
          count_total[(k1[1],k1[2])] +=1
          if v1==v2:
            count_same[(v1,k1[1],k1[2])] +=1
          break
    for k, v in count_same.items():
      if(type(k) != tuple and float(v)/len(params['p1']) >=float(params['p2'])):
        result.append((k,v))
      elif(type(k) == tuple and len(k) == 2 and float(v)/count_total[k[1]] >= float(params['p2'])):
        result.append((k,v)) #k=number of instances started, v=number of days on which k-times instances were started
      elif(type(k) == tuple and len(k) == 3 and float(v)/count_total[(k[1], k[2])] >= float(params['p2'])):
        result.append((k,v)) #k=number of instances started, v=number of days on which k-times instances were started
    return result

  def write(self,fn):
    for key, val in self.result.items():
      super().write(fn+"_"+key+".json",val)

# ordered execution
class Algorithm_3(Algorithm):
  def __init__(self,args,iscobj):
    super().__init__(args)
    self.result = self.calc(iscobj)
    
  def calc(self,iscobj):
    if(self.args.eps3 >= 0.5):
      raise RuntimeError("Epsilon for Algorithm 3 must be smaller than 0.5")
    ret = collections.defaultdict(dict)
    if len(iscobj.logs.keys()) < 2 or (iscobj.lifecycle_options['lifecycle_exists']==1 and len(iscobj.lifecycle_options['lifecycle_options']) > 1 and  "start" not in iscobj.lifecycle_options['lifecycle_options']):
      raise RuntimeError("Algorithm 3 only works with at least 2 log files and without any lifecycles or at least lifecycle transition start")
    count = collections.defaultdict(int)
    for trname,events in iscobj.mt.items():
      for idx,ev1 in enumerate(events):
        if iscobj.lifecycle_options['lifecycle_exists']==1 and len(iscobj.lifecycle_options['lifecycle_options']) > 1 and ev1.lc()!='start':
          continue
        count[ev1.lb()]+=1
        j = 1
        while(idx+j<len(events)):
          ev2 = events[idx+j]
          if ev1.log == ev2.log or (iscobj.lifecycle_options['lifecycle_exists']==1 and len(iscobj.lifecycle_options['lifecycle_options']) > 1 and ev2.lc()!='start') or ev1.ts() == ev2.ts():
            j+=1
            continue
          tupl = (ev1.lb(),ev2.lb())
          if tupl not in ret:
            ret[tupl]['pairs']=[]
            ret[tupl]['count']=0
          ret[tupl]['pairs'].append(EventPair(ev1,ev2))
          ret[tupl]['count']+=1
          break
    return self.filter({"p1":ret,"p2":count})

  def filter(self,params):
    ret = collections.defaultdict(list)
    #k is tuple of eventpair names
    for k in params['p1']:
      if(float(params['p1'][k]['count'])/min(params['p2'][k[0]], params['p2'][k[1]]) > self.args.g3):
        count_good = params['p1'][k]['count']
        if k[::-1] not in params['p1']:
          ret[tuple(k)]=params['p1'][k]['pairs']
          continue
        count_total = params['p1'][k[::-1]]['count'] + count_good
        if (float(count_good)/count_total <= self.args.eps3):
          ret[tuple(k)]=params['p1'][k]['pairs']
    return ret
    
  def write(self,fn):
    super().write(fn+".json",self.result)
    

# non-concurrent execution
class Algorithm_4(Algorithm):
  def __init__(self,args,iscobj):
    super().__init__(args)
    self.result = self.calc(iscobj)
    
  def calc(self,iscobj):
    ret_pairs = collections.defaultdict(list)
    if len(iscobj.logs.keys()) < 2 or not(iscobj.lifecycle_options['lifecycle_exists']==1 and "start" in iscobj.lifecycle_options['lifecycle_options'] and "complete" in iscobj.lifecycle_options['lifecycle_options']):
      raise RuntimeError("Algorithm 4 only works with at least 2 log files and lifecycle transitions start and complete are mandatory")
    ret_pairs = self.get_start_complete_events(iscobj.mt.items())
    labels = collections.defaultdict(int)
    for trname,events in iscobj.mt.items():
      for idx1,ev1 in enumerate(events):
        if ev1.attrib['lifecycle:transition'] != "start":
          continue
        for idx2 in range(idx1+1,len(events)):
          ev2 = events[idx2]
          if(ev2.attrib['lifecycle:transition'] == "start"): #and ev2.log != ev1.log):
            labels[(ev1.attrib['concept:name'], ev2.attrib['concept:name'])]+=1
            break
    parallel = set()
    for l in labels:
      if((l[1],l[0]) in labels):
        parallel.add(l)
    ret = collections.defaultdict(list)
    for trname,events in ret_pairs.items():
      for idx1,ev1 in enumerate(events):
        for idx2 in range(idx1+1,len(events)):
          ev2 = events[idx2]
          if parse(ev2.ev1.ts()) < parse(ev1.ev1.ts()):
            event1 = events[idx2]
            event2 = events[idx1]
          else:
            event1 = events[idx1]
            event2 = events[idx2]
          if event1.ev2.log != event2.ev1.log and parse(event2.ev1.ts()) - parse(event1.ev2.ts()) >=  datetime.timedelta(seconds=self.args.eps4) and (parse(event2.ev1.ts()) - parse(event1.ev1.ts())) != 0:
            name = (event1.ev2.lb(),event2.ev1.lb())
            ret[name].append({'ev1':{'ev1start':event1.ev1,'ev1end':event1.ev2},'ev2' : {'ev2start':event2.ev1,'ev2end':event2.ev2}})
    return self.filter({"p1":parallel,"p2": ret})

  def filter(self,params):
    ret = collections.defaultdict(list)
    for key, value in params['p2'].items():
      if(key in params['p1']):
        ret[tuple(key)].append(value)
    return ret
    
  def write(self,fn):
    super().write(fn+".json",self.result)
