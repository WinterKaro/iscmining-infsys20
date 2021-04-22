#!/usr/bin/python3
import xml.sax as SX
import collections
from classes.Event import *
from classes.Trace import *

class EHandler (SX.ContentHandler):
  def __init__(self,path,logs,start_events,end_events,lifecycle_options,ev_map):
    self.logs = logs
    self.log = path
    self.start_events = start_events
    self.end_events = end_events
    self.lifecycle_options = lifecycle_options
    self.tag = None
    self.attrib = None
    self.tracename = None
    self.event_start = None
    self.event_end = None
    self.event_start_start = None
    self.event_end_start = None
    self.trace = []
    self.mode = None
    self.event_map = ev_map
    
  def startElement(self,tag,attributes):
    self.tag = tag
    if tag == "trace":
      self.mode = "trace"
    elif tag == "event":
      self.mode ="event"
      self.attrib={}
    elif tag == "string" and self.mode=="trace" and attributes['key']=="concept:name":
      self.tracename = attributes['value']
    elif self.mode=="event" and tag != "event" and tag != "trace" and tag != "log":
      if tag == "int":
        self.attrib[attributes['key']]=int(attributes['value'])
      else:
        self.attrib[attributes['key']]=attributes['value']

  def endElement(self,tag):
    if tag == "trace":
      if self.log in self.logs:
        if self.tracename in self.logs[self.log]:
          print(self.log)
          print(self.tracename)
          raise RuntimeError("Trace already exists")
      else:
        self.logs[self.log] = {}
        self.start_events[self.log] = collections.defaultdict(int)
        self.end_events[self.log] = collections.defaultdict(int)
      if(self.lifecycle_options['lifecycle_exists'] == 0):
        self.start_events[self.log][self.event_start] += 1
        self.end_events[self.log][self.event_end] += 1
      elif (self.lifecycle_options['lifecycle_exists'] == 1 and len(self.lifecycle_options['lifecycle_options']) == 1):
        self.start_events[self.log][self.event_start] += 1
        self.end_events[self.log][self.event_end] += 1
      else:
        self.start_events[self.log][self.event_start_start] += 1
        self.end_events[self.log][self.event_end_start] += 1
      self.logs[self.log][self.tracename] = Trace(self.log,self.tracename,self.trace)
      self.event_start = None
      self.event_end = None
      self.event_start_start = None
      self.event_end_start = None
      self.tracename = None
      self.trace = []
    if tag == "event":
      self.event_map[self.attrib['concept:name']]+=1
      if 'lifecycle:transition' not in self.attrib:
        self.lifecycle_options['lifecycle_exists'] = 0  # if there is at least one event without a lifecycle transition, then we cannot use lifecycles.
      else:
        self.lifecycle_options['lifecycle_options'].add(self.attrib['lifecycle:transition'])
      if self.lifecycle_options['lifecycle_exists'] == 0 or self.lifecycle_options['lifecycle_exists'] == 1 and self.attrib['lifecycle:transition'] == "start":
        if not self.event_start_start:
          self.event_start_start =  self.attrib['concept:name']
        self.event_end_start = self.attrib['concept:name']
      if self.lifecycle_options['lifecycle_exists'] == 0 or self.lifecycle_options['lifecycle_exists'] == 1 and self.attrib['lifecycle:transition'] == "complete":
        if not self.event_start:
          self.event_start =  self.attrib['concept:name']
        self.event_end = self.attrib['concept:name']
      self.trace.append(Event(self.log,self.tracename,self.attrib))
      self.attrib = None
    self.tag = tag
