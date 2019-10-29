TESTING = False # set to False to disable traces

def log(s):
  """Print the argument if testing/tracing is enabled."""
  if TESTING:
    print(s)

#######################################################
# Collision

class Rectangle(object):
  def __init__(self, x, y, width, height):
    self.x = x
    self.y = y
    self.width = width
    self.height = height

  def setTopLeft(self, x, y):
    self.x = x
    self.y = y

  def setCenterPoint(self, x, y):
    self.x = x - self.width//2
    self.y = y - self.height//2

  def getTopLeft(self):
    return [self.x, self.y]

  def getTopRight(self):
    return [self.x+self.width, self.y]

  def getBtmLeft(self):
    return [self.x, self.y+self.height]

  def getBtmRight(self):
    return [self.x+self.width, self.y+self.height]

class BoundingBox(Rectangle):
  """An axially-aligned bounding box"""
  def __init__(self, parent, dx, dy, width, height):
    super().__init__(parent.x+dx, parent.y+dy, width, height)
    self.parent = parent
    self.dx = dx
    self.dy = dy

  def update(self):
    self.setTopLeft(self.parent.x+self.dx, self.parent.y+self.dy)

#######################################################
# State Machine

class StateMachine(object):
  """
  Base class for a state machine that tracks states, transitions, and can be paused
  """

  def __init__(self):
    self.state = None
    self.states = {}

  def addState(self, state):
    self.states[state.name] = state

  def goToState(self, stateName, forceIfSame=False):
    """Exit out of the previous state and enter into the new state"""
    if self.state:
      if not forceIfSame and self.state.name == stateName:
        return
      log('Exiting %s' % (self.state.name))
      self.state.exit(self)
    self.state = self.states[stateName]
    log('Entering %s' % (self.state.name))
    self.state.enter(self)

  def update(self):
    if self.state:
      #log('Updating %s' % (self.state.name))
      self.state.update(self)

  def pause(self):
    """Pause the machine without exiting the previous state. Requires a state to be added with the name 'paused'."""
    if not 'paused' in self.states:
      raise ValueError("Cannot pause without adding a state with the name 'paused'")
    self.state = self.states['paused']
    log('Pausing')
    self.state.enter(self)

  def resumeState(self, stateName):
    """Unpause, resuming the previous state without re-entering it"""
    if self.state:
      log('Exiting %s' % (self.state.name))
      self.state.exit(self)
    self.state = self.states[stateName]
    log('Resuming %s' % (self.state.name))

  def reset(self, stateName):
    """Reset the machine to default state and reset any other tracking variables"""
    self.goToState(stateName)

class State(object):
  """
  Abstract base class for all states in a state machine
  """
  def __init__(self, name):
    self._name = name

  @property
  def name(self):
    return self._name

  def enter(self, machine):
    pass

  def exit(self, machine):
    pass

  def update(self, machine):
    """Update the state"""
    return True
