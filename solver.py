import copy
import importlib
import logging
import math
import pprint
import random
import time

import scene
import sound
import ui


importlib.reload(logging)  # revert existing config, if any
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
# logger.debug('%s:\n%s', 'dir(scene)', pprint.pformat(dir(scene)))

"""
All nodes have position, rotation, scale, and alpha (opacity) attributes that 
determine how the node and its children are drawn. The default position is (0, 0) 
which corresponds to the lower-left corner of the screen.

By default, the position attribute of a SpriteNode corresponds to its center. In 
some cases it may be more convenient to set the position of one of the sprite’s 
corners instead – you can use the anchor_point attribute to change this behavior.
"""

ppu = 40  # pixels per unit distance or square edge
line_width = ppu / 10
mycolors = ('black', 'red')
unitsize = scene.Size(1, 1) * ppu  # in pixels
board_addrs = [(x, y) for x in range(8) for y in range(8)]


class Spotlight(scene.ShapeNode):
	"""A Spotlight is a yellow outline for a unit square."""
	def __init__(self):
		path = ui.Path.rect(line_width, line_width, ppu-2*line_width, ppu-2*line_width)
		path.line_width = line_width
		super(Spotlight, self).__init__(path=path, 
			fill_color='clear', stroke_color='yellow')
		
				
def leftmost_lowest(addrs):
	"""Return the leftmost address from the lowest row of addresses."""
	ymin = min([y for x, y in addrs])
	xmin = min([x for x, y in addrs if y == ymin])
	return (xmin, ymin)
	
	
def normalize_piece(addrs, origin_color):
	"""Return coordinate pairs and origin color, where origin is leftmost lowest."""
	assert (0, 0) in addrs
	ll = leftmost_lowest(addrs)
	new_pairs = [(x-ll[0], y-ll[1]) for x, y in addrs]
	new_origin_color = mycolors[(mycolors.index(origin_color) + ll[0] + ll[1]) % 2]
	return new_pairs, new_origin_color

def rotate_addrs(addrs):
	new_addrs = [(y, -x) for x, y in addrs]
	offset_addr = leftmost_lowest(new_addrs)
	offset_addr = (-offset_addr[0], -offset_addr[1])
	new_addrs = [(x+offset_addr[0], y+offset_addr[1]) for x, y in new_addrs]
	return new_addrs, offset_addr
	
# new_addrs, offset_addr = rotate_addrs([(0, 0), (0, 1), (0, 2), (1, 2)])
# logger.debug('%s: %r', '(new_addrs, offset_addr)', (new_addrs, offset_addr))

class Piece(scene.SpriteNode):
	"""A Piece object represents a puzzle piece.
	
	A piece object's child nodes are squares, per orientation id 0 (no rotation)
	
	* square_addrs[oid] is a list of square addresses per the orientation id
	* offset_addr[oid] is the move reqd to translate ll[oid] to ll[0].  It's used to
	  (a) determine ll_color[oid], and (b) to determine a destination position.
	* ll_color[oid] is the color of the leftmost lowest square per the orientation id.
	  It's used to define a generator that is matched to the leftmost lowest space.
	"""

	def __init__(self, square_addrs, ll_color):	
		# square_addrs are relative to the leftmost lowest square
		assert leftmost_lowest(square_addrs) == (0, 0)
		
		# Build the piece sprite with outline, and a separate piece.outline sprite.
		# Why the piece.outline?  Because it remains parked in the pool sprite, visible 
		# after the piece sprite is moved/placed.
		
		# outline = scene.SpriteNode()
		# self.outline = outline  # retain access
		
		for x, y in square_addrs:
			k = (mycolors.index(ll_color) + x + y) % 2  
			# "Manhattan distance" from ll, or L1 norm, modulo 2
			square = scene.SpriteNode(
					color=mycolors[k],
					position=unitsize * (x, y),  # scene.Point(i, j)*ppu,
					size=unitsize
					)
			square.alpha = 0.5
			self.add_child(square)
			
			# clear_square = scene.SpriteNode(color='clear', 
			# 		position=unitsize * (x, y), size=unitsize)
			# clear_square.alpha = 0.5
			# outline.add_child(clear_square)
			
			# outline segments
			if (x, y+1) not in square_addrs:
				# top border
				path = ui.Path()
				path.line_to((1)*ppu, (0)*ppu)
				path.line_width = line_width
				
				border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				border_segment.position = scene.Point(0, 1)*ppu/2
				square.add_child(border_segment)
				
				# border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				# border_segment.position = scene.Point(0, 1)*ppu/2
				# clear_square.add_child(border_segment)
				
			if (x, y-1) not in square_addrs:
				# bottom border
				path = ui.Path()
				path.line_to((1)*ppu, (0)*ppu)
				path.line_width = line_width
				
				border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				border_segment.position = scene.Point(0, -1)*ppu/2
				square.add_child(border_segment)		
						
				# border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				# border_segment.position = scene.Point(0, -1)*ppu/2
				# clear_square.add_child(border_segment)
				
			if (x+1, y) not in square_addrs:
				# right border
				path = ui.Path()
				path.line_to((0)*ppu, (1)*ppu)
				path.line_width = line_width
				
				border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				border_segment.position = scene.Point(1, 0)*ppu/2
				square.add_child(border_segment)
				
				# border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				# border_segment.position = scene.Point(1, 0)*ppu/2
				# clear_square.add_child(border_segment)
				
			if (x-1, y) not in square_addrs:
				# left border
				path = ui.Path()
				path.line_to((0)*ppu, (1)*ppu)
				path.line_width = line_width
				
				border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				border_segment.position = scene.Point(-1, 0)*ppu/2
				square.add_child(border_segment)
								
				# border_segment = scene.ShapeNode(path=path, stroke_color='blue')
				# border_segment.position = scene.Point(-1, 0)*ppu/2
				# clear_square.add_child(border_segment)
				
		# spotlight = Spotlight()
		# ll = leftmost_lowest(square_addrs)
		# spotlight.position = unitsize * ll  # scene.Point(ll[0], ll[1]) * ppu
		# self.add_child(spotlight)	
		
		self.square_addrs = [square_addrs]
		self.offset_addr = [(0, 0)]
		self.ll_square_color = [ll_color]
		
		# rotate CW 90, 180, 270, and append to lists indexed by orientation id
		for oid in range(3):
			new_square_addrs, partial_offset_addr = rotate_addrs(self.square_addrs[oid])
			new_offset_addr = (
				self.offset_addr[oid][1]+partial_offset_addr[0], 
				-self.offset_addr[oid][0]+partial_offset_addr[1])
			new_ll_square_color = mycolors[(mycolors.index(self.ll_square_color[oid]) 
				+ sum(partial_offset_addr)) % 2]
			
			self.square_addrs.append(new_square_addrs)
			self.offset_addr.append(new_offset_addr)
			self.ll_square_color.append(new_ll_square_color)
		
		# orientation ids correspond to 90 deg CW rotations
		self.oid = 0
		
pieces = [
	Piece([(0, 0), (0, 1), (0, 2), (1, 2)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (1, 2), (0, 3)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (1, 2), (1, 3)], 'black'),
	
	Piece([(0, 0), (0, 1), (0, 2), (-1, 2), (-1, 3)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (0, 3), (-1, 2), (-1, 1)], 'black'),
	Piece([(0, 0), (0, 1), (0, 2), (-1, 2), (1, 0)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (0, 3), (-1, 3)], 'black'),

	Piece([(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (0, 3), (-1, 1), (-1, 2), (1, 1), (1, 2)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (0, 3), (1, 1)], 'red'),
	Piece([(0, 0), (0, 1), (0, 2), (-1, 2), (1, 0)], 'red'),
	]
	
for i, piece in enumerate(pieces):
	# logger.debug('%s: %r', 'piece', piece)
	piece.id = i

piece = pieces[0]
for oid in range(4):
	logger.debug('%s:\n  %r', 
		'(square_addrs[oid], offset_addr[oid], ll_square_color[oid])', 
		(piece.square_addrs[oid], piece.offset_addr[oid], piece.ll_square_color[oid]),
		)


class Puzzle(scene.Scene):
	"""A Puzzle object has a board, a pool of pieces, and a solution assembly.
	
	A piece placement attempt involves
	* piece id (provided by the freshest generator)
	* piece orientation id (provided by the freshest generator)
	* soln.ll -- addr of the leftmost lowest available board space
	* soln.space_addrs -- addrs of the available board spaces
	* move and rotate the piece sprite to the board space
	* assess, and update, or revert the sprite move
	"""
		
	# my action timing params (duration in seconds, timing_mode)
	# 0.07 seconds ~ 275 attempts/min
	# 0.007 second ~ 720 attempts/min
	# 0.001 second ~ 770
	mytiming_unit = 0.001  # in seconds
	mytiming = [mytiming_unit, scene.TIMING_SINODIAL]
	wait_duration = mytiming_unit * 10
	
	def setup(self):
		"""Prepare the board, the pool of unused pieces, and the solution assembly.
		
		The setup method is called just before the scene becomes visible on screen.
		"""
		self.background_color = '#dfdfff'
			
		#--------------------------------------------------------------------------
		# board
		#--------------------------------------------------------------------------
		board = scene.Node(parent=self)
		self.board = board  # retain access

		# the board's children are squares
		for i in range(8):
			for j in range(8):
				square = scene.SpriteNode(
					color=mycolors[(i+j) % 2], 
					position=unitsize*(i, j),
					size=unitsize,
					)
				board.add_child(square)
		
		# center the board in the scene by adding an offset to the position.
		board.offset = unitsize * -3.5
		board.position = self.size * (0.5, 0.75) + board.offset
		
		board.alpha = 0.33

		#--------------------------------------------------------------------------	
		# pool
		#--------------------------------------------------------------------------	
		pool = scene.Node(parent=self)
		self.pool = pool  # retain access
		
		pool.position = self.size * (0.5, 0.25)
		
		# the pool's children are its border and 12 Piece objects and outlines
		path = ui.Path.rect(0, 0, 6*(3.2*ppu), 2*(4.5*ppu))
		path.line_width = 4
		border = scene.ShapeNode(path=path, fill_color='clear', stroke_color='yellow')
		pool.add_child(border)
		
		pool.pieces = pieces
		offset = scene.Point(-2.5, -0.8) * (3.2, 4.5) * ppu
		for i, piece in enumerate(pieces): 
			# give piece a home or parking slip in the pool, and park it
			piece.home = scene.Point(i//2, (i+1)%2) * (3.2*ppu, 4.5*ppu) + offset
			piece.position = piece.home
			pool.add_child(piece)
			
			# outline = copy.copy(piece)
			# outline.position = piece.home
			# pool.add_child(outline)
			
		pool.generators = [((piece.id, oid) for piece in pieces for oid in range(4) 
			if piece.ll_square_color[oid] == self.soln.ll_space_color)]
		
		#--------------------------------------------------------------------------		
		# solution assembly
		#--------------------------------------------------------------------------	
		soln = scene.Node(parent=self)
		self.soln = soln  # retain access
		
		# initialize the list of placed pieces
		soln.pieces = []
		soln.piece_ids = []
		# initialize the list of coordinates or addresses of open spaces
		soln.space_addrs = [(i, j) for i in range(8) for j in range(8)]
		soln.occupied_addrs = []
		
		# put a spotlight on the leftmost space in the lowest unfilled row
		soln.spotlight = Spotlight()
		ll = leftmost_lowest(soln.space_addrs)
		soln.spotlight.position = scene.Point(*ll) * ppu
		soln.add_child(soln.spotlight)
		
		soln.ll_space_color = mycolors[sum(ll)]
		
		# align the solution assembly's origin, (0, 0), with the board's origin
		soln.position = board.position

		self.attempt_counter = 0
		self.busy_flag = False
		self.attempt_started_flag = False
		
	def clear_busy_flag(self):
		self.busy_flag = False
		
	# def set_attempt_started_flag(self):
	# 	self.attempt_started_flag = True
		
					
	def touch_began(self, touch):
		"""
		x, y = touch.location
		move_action = scene.Action.move_to(x, y, 0.7, scene.TIMING_SINODIAL)
		self.ship.run_action(move_action)

		laser = scene.SpriteNode('spc:LaserBlue9', 
			position=self.ship.position, z_position=-1, parent=self)
		laser.run_action(scene.Action.sequence(
			scene.Action.move_by(0, 1000), 
			scene.Action.remove(),
			))
		# sound.play_effect('arcade:Laser_1')
		"""
		
		soln = self.soln
		
		# if busy, disregard the touch
		if self.busy_flag:
			sound.play_effect('game:Ding_2')
			return
			
		# busy until move completion (placement attempt move or revert move)
		self.busy_flag = True
		
		
		# use the freshest generator to get params for this piece placement attempt
		while True:
			try:
				generator = self.pool.generators[-1]
				piece_id, orientation_id = next(generator)
				break
			except StopIteration:
				# the freshest generator is exhausted, so discard the generator and revert
				self.pool.generators.pop()
				
				piece = self.soln.pieces.pop()
				addrs = self.soln.occupied_addrs.pop()
				self.soln.space_addrs.extend(addrs)
				soln.piece_ids.pop()
				
								
				# update the spotlight
				ll_space_addr = leftmost_lowest(self.soln.space_addrs)
				self.soln.spotlight.position = unitsize * ll_space_addr
				soln.ll_space_color = mycolors[sum(ll_space_addr) % 2]
				
				# move the sprite home
				move_action = scene.Action.group(
					scene.Action.move_to(*piece.home, *self.mytiming),
					scene.Action.rotate_by(-math.pi/2 * -piece.oid, *self.mytiming),
					)
				# clear_busy_flag_action = scene.Action.call(self.clear_busy_flag)
				
				piece.run_action(scene.Action.sequence(
						move_action, 
						self.new_clear_busy_flag_action(),  # reenable touches
						scene.Action.wait(self.wait_duration),
						self.new_touch_began_dummy_action(),  # synthetic touch
						))
				
										
				sound.play_effect('game:Error')
				return
				
				
			
		piece = self.pool.pieces[piece_id]
		
		ll_space_addr = leftmost_lowest(self.soln.space_addrs)
		x, y = (self.board.position - self.pool.position 
			+ scene.Point(*ll_space_addr) * ppu)
		
		# move the selected piece/orientation to the spotlighted empty square, 
		# and set flag for the update method to assess and accept or reject the attempt
		
		
		# x, y = scene.Point(1, 2) * ppu
		# logger.debug('%s: %r', '(x, y)', (x, y))
		# p.remove_from_parent()
		# self.soln.add_child(p)
		new_position = (self.board.position - self.pool.position \
			+ scene.Point(*ll_space_addr) * ppu 
			+ unitsize * piece.offset_addr[orientation_id])
		move_action = scene.Action.group(
			scene.Action.move_to(*new_position, *self.mytiming),
			scene.Action.rotate_by(-math.pi/2 * orientation_id, *self.mytiming),
			)
		clear_busy_flag_action = scene.Action.call(self.clear_busy_flag)
		# set_attempt_started_flag_action = scene.Action.call(
		# 		self.set_attempt_started_flag)
		
		piece.run_action(scene.Action.sequence(
						move_action, 
						clear_busy_flag_action,
						# set_attempt_started_flag_action,
						))
		self.attempt_started_flag = True
						
		self.attempt_counter += 1
		logger.debug('%s: %r', 'attempt_counter', self.attempt_counter)
		self.soln.pieces.append(piece)
		
		piece.oid = orientation_id
		
	def is_viable(self):
		"""Return True if current piece placement attempt is viable."""
		piece = self.soln.pieces[-1]
		soln = self.soln
		
		square_addrs = piece.square_addrs[piece.oid]
		space_addrs = soln.space_addrs
		ll_space_addr = leftmost_lowest(space_addrs)
		new_addrs = [(addr[0]+ll_space_addr[0], addr[1]+ll_space_addr[1])
				for addr in square_addrs]
		
		return all(addr in space_addrs for addr in new_addrs)
		
	def update(self):
		if self.busy_flag:
			return
			
		if self.attempt_started_flag:
			self.attempt_started_flag = False
			self.busy_flag = True  # block touches
			
			# a piece placement attempt was started, and the piece sprite was moved		
			piece = self.soln.pieces[-1]
			soln = self.soln
		
			square_addrs = piece.square_addrs[piece.oid]
			space_addrs = soln.space_addrs
			ll_space_addr = leftmost_lowest(space_addrs)
			new_addrs = [(addr[0]+ll_space_addr[0], addr[1]+ll_space_addr[1])
					for addr in square_addrs]
		
			# for each piece square, remove coordinates from list of spaces

			if self.is_viable():
				# the current placement attempt is viable, so complete it
				# transplant new_addrs from space_addrs to occupied_addrs
				for addr in new_addrs:
					i = soln.space_addrs.index(addr)
					soln.space_addrs.pop(i)
				soln.occupied_addrs.append(new_addrs)
				
				soln.piece_ids.append(piece.id)
				
				sound.play_effect('game:Ding_1')
				
				# are there no more spaces?  then the soln assembly is complete
				
				# update the spotlight
				ll_space_addr = leftmost_lowest(soln.space_addrs)
				soln.spotlight.position = unitsize * ll_space_addr
				soln.ll_space_color = mycolors[sum(ll_space_addr) % 2]
				
				# stack on a new generator
				self.pool.generators.append(
					# (piece_id, orientation_id) 
					# for piece_id in range(12) if piece_id not in soln.piece_ids
					# for orientation_id in range(4)
					((piece.id, oid) for piece in pieces for oid in range(4) 
							if piece.ll_square_color[oid] == self.soln.ll_space_color
							and piece.id not in soln.piece_ids)
					)

				self.busy_flag = False  # reenable touches
				self.touch_began('dummy')  # synthetic touch
				
			else:
				# the current placement attempt is incompatible, so revert it
				move_action = scene.Action.group(
					scene.Action.move_to(*piece.home, *self.mytiming),
					scene.Action.rotate_by(-math.pi/2 * -piece.oid, *self.mytiming),
					)
				clear_busy_flag_action = scene.Action.call(self.clear_busy_flag)
		
				piece.run_action(scene.Action.sequence(
						move_action, 
						self.new_clear_busy_flag_action(),  # reenable touches
						self.new_touch_began_dummy_action(),  # synthetic touch
						))
						
				sound.play_effect('game:Error')
				
				piece.oid = 0
				self.soln.pieces.pop()
			
			
			
	def _clear_busy_flag(self):
		self.busy_flag = False
		
	def new_clear_busy_flag_action(self):
		return scene.Action.call(self._clear_busy_flag)
			
	def _touch_began_dummy(self):
		"""Call touch_began directly (without a genuine touch)."""
		self.touch_began('dummy')
		
	def new_touch_began_dummy_action(self):
		"""Return a new touch_began_dummy Action object.
		
		Example
			# move the piece, then call self.touch_began('dummy')
			piece.run_action(scene.Action.sequence(
						move_action, 
						self.new_touch_began_dummy_action(),
						))		
		"""
		return scene.Action.call(self._touch_began_dummy)
		
scene.run(Puzzle(), scene.PORTRAIT)
