#######################################################################
# This file is part of Lyntin
# copyright (c) Free Software Foundation 2001, 2002
#
# Lyntin is distributed under the GNU General Public License license.  See the
# file LICENSE for distribution details.
# $Id: advanced.py,v 1.1 2003/05/05 05:56:02 willhelm Exp $
#######################################################################
"""
This module holds the magical python_cmd code.  It takes in code,
and attempts to execute it in the lyntinuser.py module.  If no such
module exists, it executes it in this module.

It also holds load_cmd which does a lot of other magic stuff.
"""
import sys
from lyntin import exported, __init__ 

usermodule = None
execdictglobals = None
execdictlocals = None

def _get_user_module():
  """
  Imports and returns the nicest user module it can find.  If we've
  already loaded a usermodule, then we use the cached one we
  loaded before so we're not doing this over and over again.

  @returns: the user module we just loaded or None
  @rtype: module
  """
  global usermodule
  if usermodule:
    return usermodule

  # this probably isn't exactly right since it'll look for the
  # first "lyntinuser" it finds and use that one.  i'm not sure how
  # we could implement a priority.
  for mem in sys.modules.keys():
    modname = "lyntinuser"
    if mem == modname or (len(mem) > len(modname) and mem[-1 * (len(modname) + 1):] == "." + modname):
      usermodule = sys.modules[mem]
      return usermodule

  return None


def python_cmd(ses, words, input):
  """
  #@ allows you to execute arbitrary Python code inside of Lyntin.
  It will first look for a module named "lyntinuser" and execute
  the code inside that module's __dict__ environment.  If no
  such module exists, it will execute the code inside 
  modules.advanced .  At present it can only handle one-line
  Python statements.

  examples:
    #@ print "hello"
    #@ print "\\n".join(exported.get_commands())

  category: commands
  """
  global execdictglobals, execdictlocals
  # NOTE: if we ever get to handling multiple-lines, we'll need
  # to change this function completely.
  try:
    my_usermodule = _get_user_module() 
    if execdictlocals == None:
      execdictlocals = {}
      
    execdictlocals["session"] = ses

    if my_usermodule == None:
      if execdictglobals == None:
        execdictglobals = {}
        exported.write_error("No lyntinuser module loaded--executing in advanced.py.")
      exec input[1:].lstrip() in execdictglobals, execdictlocals
    else:
      exec input[1:].lstrip() in usermodule.__dict__, execdictlocals
  except:
    exported.write_traceback("@: error in raw python stuff.")
    exported.tally_error()


def load_cmd(ses, args, input):
  """
  Loads/reloads a module.

  When reloading, it looks for an "unload" function and executes 
  it prior to reloading the module.  After reloading/loading, it 
  looks for a "load" function and executes it.

  Lyntin modules located in the modules package are safe to reload 
  in-game.  Lyntin core modules (engine, helpmanager, event...) are
  NOT safe to import in-game.

  examples:
    #load modules.action
    #load exportuser

  #load will look for the module on the sys.path.  So if your module
  is not on the sys.path, you should first add the directory using #@:

    #@ import sys
    #@ sys.path.append("/directory/where/my/module/exists")

  Directories specified by the moduledir command-line argument are
  added to the sys.path upon Lyntin startup.

  category: commands
  """
  mod = args["modulename"]
  reload = args["reload"]

  # if this module has previously been loaded, we try to reload it.
  if sys.modules.has_key(mod):

    _module = sys.modules[mod]
    _oldmodule = _module
    try:
      if _module.__dict__.has_key("lyntin_import"):
        # if we're told not to reload it, we toss up a message and then
        # do nothing
        if not reload:
          exported.write_message("load: module %s has already been loaded." % mod)
          return

        # if we loaded it via a lyntin_import mechanism and it has an
        # unload method, then we try calling that
        if _module.__dict__.has_key("unload"):
          try:
            _module.unload()
          except:
            exported.write_traceback("load: module %s didn't unload properly." % mod)
      del sys.modules[mod]
      exported.write_message("load: reloading %s." % mod)

    except:
      exported.write_traceback("load: had problems unloading %s." % mod)
      return
  else:
    _oldmodule = None


  # here's where we import the module
  try:
    _module = __import__( mod )
    _module = sys.modules[mod]

    if (_oldmodule and _oldmodule.__dict__.has_key("reload")):
      try:
        _oldmodule.reload()
      except:
        exported.write_traceback("load: had problems calling reload on %s." % mod)
    
    if (_module.__dict__.has_key("load")):
      _module.load()

    _module.__dict__["lyntin_import"] = 1
    exported.write_message("load successful.")
    if mod not in __init__.lyntinmodules:
      __init__.lyntinmodules.append(mod)

  except:
    exported.write_traceback("load: had problems with %s." % mod)

def unload_cmd(ses, args, input):
  """
  Unloads a module from Lyntin by calling the module's "unload" function
  and then removing references to it in the Python environment.

  examples:
    #unload wbgscheduler
    #unload modules.alias

  category: commands
  """
  mod = args["modulename"]

  if sys.modules.has_key(mod):
    _module = sys.modules[mod]

    if _module.__dict__.has_key("lyntin_import"):
      if _module.__dict__.has_key("unload"):
        try:
          _module.unload()
        except:
          exported.write_traceback("unload: module %s didn't unload properly." % mod)
      else:
        exported.write_error("unload: module %s doesn't have an unload function." % mod)

      del sys.modules[mod]
      exported.write_message("unload: module %s unloaded." % mod)
      return
    else:
      exported.write_error("unload: module %s cannot be unloaded." % mod)
      return

  exported.write_error("unload: module %s is not loaded." % mod)


def load():
  exported.add_command("@", python_cmd)
  exported.add_command("^load", load_cmd, "modulename reload:boolean=true")
  exported.add_command("^unload", unload_cmd, "modulename")

def unload():
  exported.remove_command("@")
  exported.remove_command("^load")
  exported.remove_command("^unload")

# Local variables:
# mode:python
# py-indent-offset:2
# tab-width:2
# End:
