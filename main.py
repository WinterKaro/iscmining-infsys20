#!/usr/bin/python3
import argparse
import re
import yaml
import os
import shutil
import json
import datetime
from classes.ISCObject import *
from classes.Heuristics import *
from classes.ISCGraph import *

parser = argparse.ArgumentParser()
parser.add_argument('-c','--config',help="Path to Config File.")
args = parser.parse_args()

with open(args.config, 'r') as stream:
    try:
        conf = yaml.full_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

for k,v in conf.items():
  vars(args)[k]=v

if not args.xesfiles:
  print("At least one xesfile needed")
  quit()

if not (args.a1 or args.a2 or args.a3 or args.a4):
  args.a1 = True
  args.a2 = True
  args.a3 = True
  args.a4 = True

fn = args.collection
if args.respath:
  fn = os.path.join(args.respath,fn)

paths = args.xesfiles

if not os.path.exists(os.path.join(fn,'pickle')):
  os.makedirs(os.path.join(fn,'pickle'))
if not os.path.exists(os.path.join(fn,'json')):
  os.makedirs(os.path.join(fn,'json'))
if not os.path.exists(os.path.join(fn,'pdf')):
  os.makedirs(os.path.join(fn,'pdf'))

try:
  iscobj = ISCObject(fn,paths,args)
  iscobj.write_results()
except ValueError as ve:
  print("Caught the culprit")
  x = dict()
  x['error']  = str(ve)
  with open(os.path.join(fn,'json','algo_1.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_3.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_4.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_data_constraint_start_complete.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_data_constraint_start_start.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_execution_constraint.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_regularities_event_level_start_complete.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_regularities_event_level_start_start.json'),'w') as f:
    json.dump(x,f) 
  with open(os.path.join(fn,'json','algo_2_regularities_instance_level.json'),'w') as f:
    json.dump(x,f) 
  f.closed
