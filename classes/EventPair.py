#!/usr/bin/python3
class EventPair:# {{{
  def __init__(self,ev1,ev2):
    self.ev1 = ev1
    self.ev2 = ev2
    
  def __repr__(self):
    return("%s\n%s\n" % (self.ev1,self.ev2))
# }}}
