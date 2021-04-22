#!/usr/bin/python3
from graphviz import Digraph
from graphviz import Source
from classes.ISCObject import *
from classes.Heuristics import *

class ISCGraph:
  def __init__(self, name, subgraphs, algo_res,graph_name):
    self.name = name
    self.subgraphs = subgraphs
    self.algo_res = algo_res
    self.graph_name = graph_name
    
  def draw(self, ab_th, rel_th, optionarrow):
    d_graph = Digraph(name=self.graph_name)
    d_graph.graph_attr.update(newrank="true")
    for sub in self.subgraphs:
      d_graph.subgraph(sub.create_graph(ab_th, rel_th))
    edges = set()
    for key, val in self.algo_res.items():
      if type(key) == tuple:
        for idx,k in enumerate(key):
          for idx2 in range(idx+1,len(key)):
            edges.add((k, key[idx2]))
      else:
        d_graph.node(key, style = "filled")
    already_seen = []
    for e in edges:
      if(not optionarrow):
        if([e[1], e[0]] not in already_seen):
          d_graph.edge(e[0], e[1], color = "red", style = "dashed", arrowhead= "none")
          already_seen.append([e[0], e[1]])
      else:
        d_graph.edge(e[0], e[1], color = "red", style = "dashed")
      d_graph.node(e[0], style = "filled")
      d_graph.node(e[1], style = "filled")
    testi=d_graph.source[:-1]
    samerank = "{rank=same;"+" ".join(["\"start_"+x.logname+"\";" for x in self.subgraphs])+"}"
    testi+=samerank+"\n}";
    src = Source(testi)
    src.render(self.name, format='pdf', cleanup=False)  #option cleanup: keep dot file

  def draw_algo2(self, ab_th, rel_th):
    d_graph = Digraph(name=self.name)
    d_graph.graph_attr.update(newrank="true")
    for sub in self.subgraphs:
      d_graph.subgraph(sub.create_graph(ab_th, rel_th))
    edges = set()
    res = ""
    for key, val in self.algo_res.items():
      if type(key) == tuple:
        if(key[0] != key[1]):
          for idx,k in enumerate(key):
            for idx2 in range(idx+1,len(key)):
              if(type(val) == float):
                d_graph.edge(key[idx], key[idx2], color = "red", style = "dashed", arrowhead = "none", xlabel = repr(round(val, 3)))
                d_graph.node(key[idx], style = "filled")
                d_graph.node(key[idx2], style = "filled")
              elif(type(val) == bool):
                if(val == True):
                  d_graph.node(key[idx2], style = "filled")
                  d_graph.node(key[idx], style = "filled")
                  d_graph.edge(key[idx], key[idx2], color = "red", style = "dashed", arrowhead = "none")
              else:
                if(type(val[0]) == Event):
                  d_graph.node(key[idx2], style = "filled")
                  d_graph.node(key[idx], style = "filled")
                  d_graph.edge(key[idx], key[idx2], color = "red", style = "dashed", arrowhead = "none")
                else:
                  rules = str.join("\\n|| ",[str.join(" && ",[str.join("",[str(x[0])[:-1:]+" of " + (key[0] if int(str(x[0])[-1])==1 else key[1])]+ [str(y) for y in x[1::]]) for x in c]) for c in val])
                  d_graph.edge(key[idx], key[idx2], color = "red", style = "dashed", arrowhead = "none", xlabel=rules)
                  d_graph.node(key[idx2], style = "filled")
                  d_graph.node(key[idx], style = "filled")
        else:
          if(type(val) == float):
            d_graph.node(key[0], style = "filled", xlabel = repr(round(val, 3)))
          elif(type(val) == bool):
            if( val == True):
              d_graph.node(key[0], style = "filled")
          else:
            if(type(val[0]) == Event):
              d_graph.node(key[0], style = "filled")
            else:
              rules = str.join("\\n|| ",[str.join(" && ",[str.join("",[str(x[0])[:-1:]+" of " + ("start" if int(str(x[0])[-1])==1 else "complete")]+[str(y) for y in x[1::]]) for x in c]) for c in val])
              d_graph.node(key[0], style = "filled", xlabel = rules)
      if(isinstance(key, str) and val):
        for v in val:
          if(type(v[0]) == int):
            res += " on " + str(v[1]) + " days " + str(v[0]) + " instances were started\n"
          elif(type(v[0]) == tuple and len(v[0]) == 2):
            res += "on " + str(v[1]) + " days " + str(v[0][0]) + " instances with <" + str(v[0][1]) + "> were started\n"
          else:
            res += "on " + str(v[1]) + " days " + str(v[0][0]) + " instances with <" + str(v[0][1]) + "> were started by <" + str(v[0][2]) +">\n"
    d_graph.attr(label = res)
    testi=d_graph.source[:-1]
    samerank = "{rank=same;"+" ".join(["\"start_"+x.logname+"\";" for x in self.subgraphs])+"}"
    testi+=samerank+"\n}";
    src = Source(testi)
    src.render(self.name, format='pdf', cleanup=False)  #option cleanup: keep dot file
