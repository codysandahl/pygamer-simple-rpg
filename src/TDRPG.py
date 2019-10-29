import ugame
import stage
import utils

GAME = None

#######################################################
# Game

class Game(stage.Stage):
  """Base class for a game and its display"""

  # TODO: add game state machine
  # TODO: make each screen a state, and make a transition between them when player overlaps with trigger zones
  # TODO: have a combat state

  def __init__(self, display=None, fps=12):
    # require singleton
    global GAME
    if GAME:
      raise ValueError("Only one Game is allowed at a time")
    GAME = self
    # NOTE: PyGamer display is 160x128
    if display:
      super().__init__(display, fps)
    else:
      super().__init__(ugame.display, fps)
    self.midX = int(self.width*0.5)
    self.midY = int(self.height*0.5)
    self.spriteSize = 16 # static size of sprites in pixels using the stage library
    self.bounceX = self.width-self.spriteSize
    self.bounceY = self.height-self.spriteSize
    self.tilesX = int(self.width/self.spriteSize) # number of tiles that will fit in game
    self.tilesY = int(self.height/self.spriteSize)
    self.map = None
    self.updaters = []
    self.sprites = []
    self.forceRefresh = False # force a refresh on the next frame
    self._pauseObject = None # object that receives updates while game is paused
    self.framesToWaitAfterPause = 2
    self._curFramesWaiting = 0

  def addToUpdates(self, obj):
    if isinstance(obj, list):
      self.updaters.extend(obj)
    else:
      self.updaters.append(obj)

  def removeFromUpdates(self, obj):
    if not isinstance(obj, list):
      obj = list(obj)
    for o in obj:
      self.updaters.remove(o)

  def addToSprites(self, obj, updater=True):
    if isinstance(obj, list):
      self.sprites.extend(obj)
    else:
      self.sprites.append(obj)
    if updater:
      self.addToUpdates(obj)

  def removeFromSprites(self, obj, updater=True):
    if not isinstance(obj, list):
      obj = list(obj)
    for o in obj:
      self.sprites.remove(o)
    if updater:
      self.removeFromUpdates(obj)

  def pause(self, pauseObject):
    self._pauseObject = pauseObject

  def resume(self):
    self._pauseObject = None
    self._curFramesWaiting = 0

  def gameLoop(self):
    while True:
      if self._pauseObject:
        self._pauseObject.update()
      elif self._curFramesWaiting < self.framesToWaitAfterPause:
          ugame.buttons.get_pressed() # clear out button press cache
          self._curFramesWaiting += 1
      else:
        for obj in self.updaters:
          obj.update()
        if not self.forceRefresh:
          self.render_sprites(self.sprites)
        else:
          self.render_block(0, 0)
          self.forceRefresh = False
      self.tick()

#######################################################
# Map

class TileMap(stage.Grid):
  """A tile map for the whole screen, utilizing a tile set from the given bank"""

  def __init__(self, bank, width=8, height=8, palette=None, buffer=None):
    super().__init__(bank, width, height, palette, buffer)
    self.shaking = 0
    self.framesToShake = 4
    self._curShakeFrame = 0
    self.solidTypes = [] # tile types that should be treated as solid walls for collision
    self.triggerTypes = [] # tile types that should trigger some action when overlapped

  def fromHexList(self, tileList):
    """
    Given a list of hex codes, update the tile map
    Example:
    tileList = [
        "0123456789ABCDEF", # row 0
        "0123456790ABCDEF", # row 1
        ...
    ]
    """
    # validate input
    if len(tileList) != self.height:
      raise ValueError("Length of tileList is {} but expected {}".format(len(tileList), self.height))
    # iterate through tile list
    x = 0
    y = 0
    for row in tileList:
      if len(row) != self.width:
        raise ValueError("Length of row {} is {} but expected {}".format(y, len(row), self.width))
      for tileValue in row:
        self.tile(x, y, int(tileValue, 16))
        x += 1
      y += 1
      x = 0

  def shake(self, amount=4):
    self.shaking = amount
    self._curShakeFrame = 0

  def handleTrigger(self, sprite, x, y, tileType):
    """Handle special actions based on the tile type"""
    pass

  def update(self):
    if self.shaking != 0:
      GAME.forceRefresh = True
      if self._curShakeFrame % 2 == 0:
        self.move(self.shaking, 0)
      else:
        self.move(-self.shaking, 0)
      self._curShakeFrame += 1
      if self._curShakeFrame >= self.framesToShake:
        self._curShakeFrame = 0
        self.shaking = 0

#######################################################
# Entities

class Moveable(stage.Sprite):
  """Base class for moveable sprites like a player or enemy"""

  def __init__(self, bank, x, y):
    super().__init__(bank, 0, x, y)
    self.x = x
    self.y = y
    self.collider = utils.BoundingBox(self,2, 2, 12, 12)
    self.animations = utils.StateMachine()

  def getTilesInCollider(self, dx=0, dy=0):
    """Calculate the grid tiles that are underneath each corner of this sprite's bounding box"""
    tiles = []
    rect = utils.Rectangle(self.collider.x+dx, self.collider.y+dy, self.collider.width, self.collider.height)
    # top left
    point = rect.getTopLeft()
    point[0] >>= 4 # divide by 16
    point[1] >>= 4 # divide by 16
    if point[0] >= 0 and point[1] >= 0 and point[0] < GAME.tilesX and point[1] < GAME.tilesY:
      tiles.append(point)
    # top right
    point = rect.getTopRight()
    point[0] >>= 4
    point[1] >>= 4
    if (point[0] >= 0 and point[1] >= 0 and point[0] < GAME.tilesX and point[1] < GAME.tilesY) and not point in tiles:
      tiles.append(point)
    # bottom left
    point = rect.getBtmLeft()
    point[0] >>= 4
    point[1] >>= 4
    if (point[0] >= 0 and point[1] >= 0 and point[0] < GAME.tilesX and point[1] < GAME.tilesY) and not point in tiles:
      tiles.append(point)
    # bottom right
    point = rect.getBtmRight()
    point[0] >>= 4
    point[1] >>= 4
    if (point[0] >= 0 and point[1] >= 0 and point[0] < GAME.tilesX and point[1] < GAME.tilesY) and not point in tiles:
      tiles.append(point)
    # return list of tiles
    return tiles

  def getMovement(self):
    """
    Determine desired movement (whether AI or player controls) and return dx, dy for this frame
    NOTE: tile collision currently only supports moving in one direction at a time (no diagonal)
    """
    return 0, 0

  def applyMovementAndAnims(self, dx, dy):
    """Apply the desired movement and animations to this sprite"""
    # handle movement and constrain to the stage
    self.x = max(min(self.x + dx, GAME.bounceX), 0)
    self.y = max(min(self.y + dy, GAME.bounceY), 0)
    # finish movement
    self.move(self.x, self.y)
    self.collider.update()
    self.animations.update()

  def checkTileCollision(self, dx, dy):
    """Check the game map for collisions with tiles. Works best by checking one axis at a time"""
    if dx != 0:
      # check map for impassable OR special handler tiles
      tiles = self.getTilesInCollider(dx, 0)
      for t in tiles:
        tileType = GAME.map.tile(x=t[0], y=t[1])
        if tileType in GAME.map.solidTypes:
          if dx > 0:
            self.x = ((t[0]-1) << 4) + self.collider.dx - 1
          else:
            self.x = ((t[0]+1) << 4) - self.collider.dx + 1
          dx = 0
          break
        elif tileType in GAME.map.triggerTypes:
          GAME.map.handleTrigger(self, x=t[0], y=t[1], tileType=tileType)
    if dy != 0:
      # check map for impassable OR special handler tiles
      tiles = self.getTilesInCollider(0, dy)
      for t in tiles:
        tileType = GAME.map.tile(x=t[0], y=t[1])
        if tileType in GAME.map.solidTypes:
          if dy > 0:
            self.y = ((t[1]-1) << 4) + self.collider.dy - 1
          else:
            self.y = ((t[1]+1) << 4) - self.collider.dy + 1
          dy = 0
          break
        elif tileType in GAME.map.triggerTypes:
          GAME.map.handleTrigger(self, x=t[0], y=t[1], tileType=tileType)
    return dx, dy

  def getAnimation(self, dx, dy):
    """Update the animation based on the movement and state"""
    pass

  def update(self):
    super().update()
    dx, dy = self.getMovement()
    dx, dy = self.checkTileCollision(dx, dy)
    self.getAnimation(dx, dy)
    self.applyMovementAndAnims(dx, dy)

#######################################################
# Animation Helpers

class AnimState(utils.State):
  """
  Base class for animation states in a state machine
  Expects all the frames to be consecutive in the sprite sheet
  Can delay a number of game frames between each animation frame (ex: delay of 1 with 12 fps means delay 1/12 sec between animation frames)
  """
  LOOP_FOREVER = -1
  ROTATE_MIRROR = 4
  ROTATE_90CW = 1
  ROTATE_90CCW = 2

  def __init__(self, name, sprite, frameStart, frameEnd, delay=0, numTimes=-1, nextState='idle', rotate=0):
    """
    Create the new state. By default, the animation will advance each game frame, and it will loop forever.
    """
    super().__init__(name)
    self.sprite = sprite
    self.frameStart = frameStart
    self.frameEnd = frameEnd
    self._curFrame = frameStart
    self.delay = delay
    self._curDelay = 0
    self.numTimes = numTimes
    self._curTimes = 0
    self.nextState = nextState
    self.rotate = rotate

  def enter(self, machine):
    utils.log("Entering {} and setting frame to {}. Will repeat {} times and then go to state {}".format(self.name, self.frameStart, self.numTimes, self.nextState))
    self.sprite.set_frame(self.frameStart, self.rotate)
    self._curFrame = self.frameStart
    self._curDelay = 0

  def update(self, machine):
    # handle delay in the animation
    if self.delay > 0:
      if self._curDelay < self.delay:
        self._curDelay += 1
        return
    # advance the frame in the animation
    self._curFrame += 1
    self._curDelay = 0
    # handle looping/exiting animation
    if self._curFrame > self.frameEnd:
      self._curFrame = self.frameStart
      self._curTimes += 1
      if self.numTimes != self.LOOP_FOREVER and self._curTimes > self.numTimes:
        self.goToNextState(machine)
        return
    self.sprite.set_frame(self._curFrame, self.rotate)

  def goToNextState(self, machine):
    machine.goToState(self.nextState)


class AnimLoop(AnimState):
  """
  Loop an animation for a sprite. Expects all the frames to be consecutive in the sprite sheet.
  """
  def __init__(self, name, sprite, frameStart, frameEnd, delay=0, rotate=0):
    super().__init__(name, sprite, frameStart, frameEnd, delay, rotate=rotate)

class AnimRepeatN(AnimState):
  """
  Repeat an animation N times. Expects all the frames to be consecutive in the sprite sheet.
  """
  def __init__(self, name, sprite, frameStart, frameEnd, delay=0, numTimes=-1, nextState='idle', rotate=0):
    super().__init__(name, sprite, frameStart, frameEnd, delay, numTimes, nextState, rotate)

#######################################################
# GUI

class Dialog(TileMap):
  """A modal text dialog built using a tile map"""

  def __init__(self, bank, width=8, height=2, text1=None, text2=None, sprite1=None, palette=None, buffer=None):
    super().__init__(bank, width, height, palette, buffer)
    self.showing = False
    # first line of text
    self.marginX = 4
    self.marginY = 4
    self.text = None
    if text1:
      self.text1 = stage.Text(width=len(text1), height=1)
      self.text1.text(text1)
    # second line of text
    self.marginX2 = self.marginX
    self.marginY2 = self.marginY + 15
    self.text2 = None
    if text2:
        self.text2 = stage.Text(width=len(text2), height=1)
        self.text2.text(text2)
    # extra sprite
    self.sprite1 = None
    if sprite1:
        self.sprite1 = sprite1
    # frames to wait at start (avoids accidental button presses)
    self.framesToWait = 2
    self._curFramesWaiting = 0

  def move(self, x, y, z=None):
    if self.text1:
      self.text1.move(x+self.marginX, y+self.marginY, z)
    if self.text2:
      self.text2.move(x+self.marginX2, y+self.marginY2, z)
    super().move(x, y, z)

  def show(self):
    """Display this dialog on top of all the other layers and pause the game"""
    if self.showing:
      return
    GAME.layers.insert(0, self)
    if self.text1:
      GAME.layers.insert(0, self.text1)
    if self.text2:
      GAME.layers.insert(0, self.text2)
    if self.sprite1:
      GAME.layers.insert(0, self.sprite1)
    GAME.forceRefresh = True
    GAME.pause(self)
    self.showing = True
    self._curFramesWaiting = 0

  def hide(self):
    """Hide this dialog and unpause the game"""
    if not self.showing:
      return
    GAME.layers.remove(self)
    if self.text1:
      GAME.layers.remove(self.text1)
    if self.text2:
      GAME.layers.remove(self.text2)
    if self.sprite1:
      GAME.layers.remove(self.sprite1)
    GAME.forceRefresh = True
    GAME.resume()
    self.showing = False

  def update(self):
    """Update function called while the game is paused"""
    if self._curFramesWaiting < self.framesToWait:
        self._curFramesWaiting += 1
        return
