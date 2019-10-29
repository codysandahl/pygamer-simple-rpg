#import board
import ugame
import stage
import utils
import TDRPG

#######################################################
# Game object

game = TDRPG.Game()

#######################################################
# Town

townBank = stage.Bank.from_bmp16("town1.bmp")
town = TDRPG.TileMap(townBank, width=game.tilesX, height=game.tilesY)
town.fromHexList([
  "0000ee0fff",
  "5555540ff8",
  "0000060088",
  "9abc060080",
  "73370600d0",
  "7727060fef",
  "0080045555",
  "008d88d000",
])
town.solidTypes = [2,3,7,9,10,11,12,13,14,15]
town.triggerTypes = []
game.map = town

#######################################################
# Player

class Player(TDRPG.Moveable):
  def __init__(self, x, y):
    bank = stage.Bank.from_bmp16("warrior.bmp")
    super().__init__(bank, x, y)
    self.collider = utils.BoundingBox(self, 2, 1, 12, 14)
    self.animations.addState(TDRPG.AnimLoop('idleRight', sprite=self, frameStart=0, frameEnd=0))
    self.animations.addState(TDRPG.AnimLoop('idleLeft', sprite=self, frameStart=0, frameEnd=0, rotate=TDRPG.AnimState.ROTATE_MIRROR))
    self.animations.addState(TDRPG.AnimLoop('walkRight', sprite=self, frameStart=0, frameEnd=2))
    self.animations.addState(TDRPG.AnimLoop('walkLeft', sprite=self, frameStart=0, frameEnd=2, rotate=TDRPG.AnimState.ROTATE_MIRROR))
    self.animations.addState(TDRPG.AnimRepeatN('attack', sprite=self, frameStart=3, frameEnd=6, numTimes=1, nextState='idleRight'))
    self.animations.goToState('idleRight')

  def getMovement(self):
    """
    Determine desired movement (whether AI or player controls) and return dx, dy for this frame
    NOTE: tile collision currently only supports moving in one direction at a time (no diagonal)
    """
    keys = ugame.buttons.get_pressed()
    dx = 0
    dy = 0
    # check for arrow keys - NOTE: currently tile collision only supports one direction of movement at a time (no diagonal)
    if keys & ugame.K_RIGHT:
      dx = 4
    elif keys & ugame.K_LEFT:
      dx = -4
    elif keys & ugame.K_UP:
      dy = -4
    elif keys & ugame.K_DOWN:
      dy = 4
    if keys & ugame.K_X:
      self.animations.goToState('attack') # TODO: prevent walking while attacking
    if keys & ugame.K_O:
      text.show()
    # return desired movement
    return dx, dy

  def getAnimation(self, dx, dy):
    # update animations
    if dx != 0 or dy != 0:
      if dx < 0 or (dy != 0 and self.animations.state.name == 'idleLeft'):
        self.animations.goToState('walkLeft')
      elif dx > 0 or (dy != 0 and self.animations.state.name == 'idleRight'):
        self.animations.goToState('walkRight')
    else:
      if self.animations.state.name == 'walkLeft':
        self.animations.goToState('idleLeft')
      elif self.animations.state.name == 'walkRight':
        self.animations.goToState('idleRight')

player = Player(x=8, y=8)

#######################################################
# Text dialog

class TextDialog(TDRPG.Dialog):
  def __init__(self, text1, text2=None):
    bank = stage.Bank.from_bmp16("gui.bmp")
    super().__init__(bank, width=game.tilesX, height=2, text1=text1, text2=text2)
    self.fromHexList([
      "0111111112",
      "3444444445"
    ])
    self.sprite1 = stage.Sprite(bank, 10, game.width-2*game.spriteSize, game.height-int(1.5*game.spriteSize))
    self.move(0, game.height-2*game.spriteSize)

  def update(self):
    keys = ugame.buttons.get_pressed()
    if self._curFramesWaiting < self.framesToWait:
        self._curFramesWaiting += 1
        return
    if keys & ugame.K_O:
      self.hide()

text = TextDialog("Meow Mix", "Delivers!")

#######################################################
# Finish setup and start game loop

game.addToSprites([player])
game.layers = [player, town]
game.render_block(0, 0, game.width, game.height)

game.gameLoop()