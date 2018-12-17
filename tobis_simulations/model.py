import sys
import pygame
from pygame.locals import *
import pymunk
import pymunk.pygame_util
import itertools
import json
import numpy as np
import math
from pymunk import Vec2d
import collections #for keeping the order in which dictionaries were created

# TODO LIST: 

# - replicate the clips as specified in /code/flash/PhysicsLanguage.as 

class World():
	"""
	Sets up world and simulates a particular trial
	- note: y-coordinates are flipped compared to javascript or flash implementation
	- run python window in low resolution mode: /usr/local/Cellar/python@2/2.7.15_1/Frameworks/Python.framework/Versions/2.7/Resources/Python.app
	- counterfactual tests could be made more efficient by only running the actual situation once
	- apply noise for each model the first time it participates in a collision 
	"""

	def __init__(self):
		pass 

	def pymunk_setup(self,experiment,start_step=0,pre_def=None):
		# Initialize space and set gravity for space to do simulation over
		self.width = 800
		self.height = 600
		self.ball_size = 60
		self.box_size = (70,70)
		self.speed = 200 # scales how fast balls are moving 
		self.step_size = 1/50.0
		self.step_max = 300 # step at which to stop the animation
		self.step = start_step # used to record when events happen 
		self.space = pymunk.Space()
		self.events = [] # used to record events 
		# containers for bodies and shapes
		self.bodies = collections.OrderedDict()
		self.shapes = collections.OrderedDict()	
		self.sprites = collections.OrderedDict()
		
		self.collision_types = {
			'static': 0,
			'dynamic': 1,
			'teleport': 2
		}		
		self.experiment = experiment

		if self.experiment == '3ball':
			self.target_ball = 'E'
		else:
			self.target_ball = 'B'
	
		# add walls 
		self.add_wall(position = (400, 590), length = 800, height = 20, name = 'top_wall', space = self.space)
		self.add_wall(position = (400, 10), length = 800, height = 20, name = 'bottom_wall', space = self.space)
		self.add_wall(position = (10, 100), length = 20, height = 200, name = 'top_left_wall', space = self.space)
		self.add_wall(position = (10, 500), length = 20, height = 200, name = 'bottom_left_wall', space = self.space)

		# read in trial info

		if pre_def == None:
			self.read_trials()
			self.balls = self.trials[self.trial]['balls']
			if 'boxes' in self.trials[self.trial]:
				self.boxes = self.trials[self.trial]['boxes']
			else:
				self.boxes = []
		else:
			# remove all obstacles from the world?
			self.trials = pre_def
			self.balls = self.trials[0]['balls']
			self.boxes = []

		# add objects 
		if self.experiment == 'teleport':
			self.objects = self.trials[self.trial]['objects']
			for object in self.objects: 
				if object['name'] == 'brick':
					body, shape = self.add_brick(position = object['position'], name = object['name'], rotation = object['rotation'], space = self.space)
				if object['name'] == 'teleport_entrance':
					body, shape = self.add_teleport_entrance(position = object['position'], name = object['name'], rotation = object['rotation'], status = object['status'], space = self.space)
				if object['name'] == 'teleport_exit':
					body, shape = self.add_teleport_exit(position = object['position'], name = object['name'], status = object['status'], space = self.space)
				self.bodies[object['name']] = body
				self.shapes[object['name']] = shape		

		# add balls 
		for ball in self.balls:
			body, shape = self.add_ball(position = ball['position'], name = ball['name'], velocity = ball['velocity'], size = self.ball_size, space = self.space) 
			self.bodies[ball['name']] = body
			self.shapes[ball['name']] = shape

		for box in self.boxes:
			body, shape = self.add_box(position = box['position'], name = box['name'], size = self.box_size, space = self.space)
			self.bodies[box['name']] = body
			self.shapes[box['name']] = shape

	# read in trial information 
	def read_trials(self):
		self.trials = json.load(open('trialinfo/' + self.experiment + '_trials.json', 'r'))

	# setup collision handlers 
	def collision_setup(self):	
		handler_dynamic = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['dynamic'])
		handler_dynamic.begin = self.collisions
		
		if self.experiment == 'teleport':		
			handler_teleport = self.space.add_collision_handler(self.collision_types['teleport'], self.collision_types['dynamic'])
			if self.bodies['teleport_entrance'].status == 'on':
				handler_teleport.begin = self.teleport

	# handle dynamic events
	def collisions(self,arbiter,space,data):
		# print arbiter.is_first_contact #checks whether it was the first contact between the shapes 
		event = {
			'balls': [arbiter.shapes[0].body.name,arbiter.shapes[1].body.name],
			'step': self.step,
			'type': 'collision'
		}
		self.events.append(event)
		return True

	# handle teleport
	def teleport(self,arbiter,space,data):
		objects = [arbiter.shapes[0].body,arbiter.shapes[1].body]
		for object in objects: 
			if object.name == 'B':
				object.position = self.bodies['teleport_exit'].position 
		return False	

	def add_wall(self, position, length, height, name, space):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		wall = pymunk.Poly.create_box(body, size = (length, height))
		wall.elasticity = 1
		wall.name = name 
		wall.collision_type = self.collision_types['static']
		space.add(wall)
		return wall	

	def add_ball(self, position, velocity, size, name, space):
		mass = 1
		radius = size/2
		moment = pymunk.moment_for_circle(mass, 0, radius)
		body = pymunk.Body(mass, moment)
		body.position = position
		body.size = (size,size)
		body.angle = 0
		velocity = map(lambda x: x*self.speed,velocity) 
		body.apply_impulse_at_local_point(velocity) #set velocity
		body.name = name 
		shape = pymunk.Circle(body, radius)
		shape.elasticity = 1.0
		shape.friction = 0
		shape.collision_type = self.collision_types['dynamic']
		space.add(body, shape)
		return body, shape

	def add_box(self, position, size, name, space):
		mass = 1
		moment = pymunk.moment_for_box(mass, size)
		body = pymunk.Body(mass, moment)
		body.position = position
		body.size = size
		body.angle = 0
		velocity = (0,0)

		# Create custom velocity update and override standard
		def update_velocity(body, gravity, damping, dt):
			pymunk.cp.cpBodyUpdateVelocity(body._body, tuple(gravity), .96, dt)
		body._set_velocity_func(update_velocity)


		body.name = name
		shape = pymunk.Poly.create_box(body, size)
		shape.elasticity = 1.0
		# I don't think this friction parameter has desired effect
		# worth further investigation
		# shape.friction = 1.0
		shape.collision_type = self.collision_types['dynamic']
		space.add(body, shape)
		return body, shape


	def add_brick(self, position, rotation, name, space):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		body.name = name 
		body.size = (35, 100)
		body.angle = math.radians(rotation)
		shape = pymunk.Poly.create_box(body, size = body.size)
		shape.elasticity = 1
		shape.collision_type = self.collision_types['static']
		space.add(body, shape)
		return body, shape

	def add_teleport_entrance(self, position, rotation, name, status, space):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		body.name = name 
		body.size = (35, 100)
		body.angle = math.radians(rotation)
		body.status = status
		shape = pymunk.Poly.create_box(body, size = body.size)
		shape.sensor = True
		shape.collision_type = self.collision_types['teleport']
		space.add(body, shape)
		return body, shape

	def add_teleport_exit(self, position, name, status, space):
		# take out of physics later ... 
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		body.name = name 
		# body.size = (40,40)
		body.angle = 0
		body.status = status
		shape = pymunk.Circle(body, 20)
		shape.sensor = True
		# space.add(body, shape)
		return body, shape

	def remove(self,ball,step,animate):
		if self.step == step:
			self.space.remove(self.shapes[ball]) #remove body from space 
			self.space.remove(self.bodies[ball]) #remove body from space 
			del self.bodies[ball] #remove body 
			del self.shapes[ball] #remove shape
			if animate: 		
				del self.sprites[ball] #remove sprite 

	def perturb(self,ball,step,magnitude=0):
		if self.step == step:
			b = self.bodies[ball]
			b.position = (b.position.x+self.gaussian_noise()*magnitude,
				b.position.y+self.gaussian_noise()*magnitude)

	def perturb_vel(self,ball,step,magnitude=0):
		if self.step == step:
			b = self.bodies[ball]
			x = b.velocity.x
			y = b.velocity.y

			# linear manipulations
			if not (x==0 and y==0):
				x_pert = x + np.random.normal(loc=1,scale=.01)*magnitude
				y_pert = y + np.random.normal(loc=1,scale=.01)*magnitude
				b.velocity = (x_pert, y_pert)
			

			# Polar manipulations
			# If x is not zero, regardless of y the following works
			# if x != 0.0:
			# 	pert_ang = np.arctan(y/x) + np.random.normal()*magnitude
			# 	pert_mag = np.sqrt(x**2 + y**2) * np.random.normal(loc=1.0)*magnitude
			# 	b.velocity = (np.cos(pert_ang)/pert_mag, np.sin(pert_ang)/pert_mag)
			# # If x is zero and y is not, then we must do the following
			# elif x == 0.0 and y != 0.0:
			# 	pert_ang = np.pi/2 + np.random.normal() * magnitude
			# 	pert_mag = y * np.random.normal(loc=1.0) * magnitude
			# 	b.velocity = (np.cos(pert_ang)/pert_mag, np.sin(pert_ang)/pert_mag)
			# in the case where x and y both equal zero, we simply move on without making a change

	def apply_noise(self,ball,step,noise):
		if not noise == 0:
			b = self.bodies[ball]
			if self.step > step:
				x_vel = b.velocity[0]
				y_vel = b.velocity[1]
				perturb = self.gaussian_noise()*noise
				cos_noise = np.cos(perturb*np.pi/180)
				sin_noise = np.sin(perturb*np.pi/180)
				x_vel_noise = x_vel * cos_noise - y_vel * sin_noise
				y_vel_noise = x_vel * sin_noise + y_vel * cos_noise
				b.velocity = x_vel_noise,y_vel_noise

	def end_clip(self,animate):
		# bx = self.bodies[self.target_ball].position[0]
		# dist_cond = bx < -500 or bx > 1300
		if self.step > self.step_max: #or dist_cond:
			b = self.bodies[self.target_ball]
			event = {
					'ball': self.target_ball,
					'step': self.step,
					'type': 'outcome',
				}
			if b.position[0] > -self.ball_size/2:
				event['outcome'] = 0
			else:
				event['outcome'] = 1
			event['outcome_fine'] = b.position
			self.events.append(event)
			pygame.display.quit()
			return True

	def simulate(self, experiment = '3ball', animate=True, trial=0, noise = 0, save=False, info=[], rec_paths=False, start_step=0, pre_def=None):
		# Initialization 
		self.trial = trial
		self.pymunk_setup(experiment,start_step=start_step,pre_def=pre_def)
		self.collision_setup()
		pic_count = 0 # used for saving images 
		done = False # pointer to say when animation is done 
		self.info = info
		self.noise = noise
		
		# If animating, initialize pygame animation
		if animate:
			pygame.init()
			clock = pygame.time.Clock()

			# Set size/title of display
			screen = pygame.display.set_mode((self.width, self.height))
			pygame.display.set_caption("Animation")

			# Load sprites
			for body in self.bodies:
				b = self.bodies.get(body)
				if  b.name == 'teleport_entrance' or b.name == 'teleport_exit':
					name = b.name + "_" + b.status
				else: 
					name = b.name
				sprite = pygame.image.load('figures/' + name + '.png')
				self.sprites[body] = sprite

		# Run the simulation forever, until exit

		paths = {b:[[],[]] for b in self.bodies}
		steps_after = 0
		while not done:
			if animate:
				# Lets you exit the animation loop by clicking escape on animation
				for event in pygame.event.get():
					if event.type == QUIT:
							sys.exit(0)
					elif event.type == KEYDOWN and event.key == K_ESCAPE:
							sys.exit(0)

				# Draw static elements 
				screen.fill((255,255,255)) #background 
				pygame.draw.rect(screen, pygame.color.THECOLORS['red'], [0,200,20,200]) #goal
				pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,0,800,20]) #top wall
				pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,580,800,20]) #bottom wall
				pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,0,20,200]) #top left
				pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,400,20,200]) #bottom left
				
				# update object positions over time
				for body in self.bodies:
					self.update_sprite(body = self.bodies.get(body), sprite = self.sprites.get(body),screen = screen)

				# Draw the space
				pygame.display.flip()
				pygame.display.update()
				clock.tick(100)
				
				if save:
					pygame.image.save(screen, 'figures/frames/animation'+'{:03}'.format(pic_count)+'.png')
					pic_count += 1

			# manipulations 
			if self.info:
				for action in self.info:
					if action['action'] == 'remove':
						self.remove(ball = action['ball'], step = action['step'], animate = animate)
					if action['action'] == 'perturb':
						self.perturb(ball = action['ball'], step = action['step'], magnitude = action['magnitude'])
					if action['action'] == 'perturb_vel':
						self.perturb_vel(ball=action['ball'], step=action['step'], magnitude=action['magnitude'])
					if action['action'] == 'noise':
						self.apply_noise(ball = action['ball'], step = action['step'], noise = self.noise)

			# Take a step in the simulation, update clock/ticks
			done = self.end_clip(animate = animate)

			self.space.step(self.step_size)
			self.step += 1
			if rec_paths:
				for name,body in self.bodies.items():
					b_pos, b_vel = paths[name]
					b_pos.append(body.position)
					b_vel.append(body.velocity)

			target_x = self.bodies[self.target_ball].position[0]
			# if target_x < -50:
			# 	break
				# if steps_after < 50:
				# 	steps_after += 1
				# else:
				# 	break


		# Double check that events are in temporal order
		assert all([self.events[i]['step'] <= self.events[i+1]['step'] for i in range(len(self.events) - 1)])
		# Return events and paths as requested
		if not rec_paths:
			return self.events
		else:
			return self.events, paths

	def flipy(self, y):
	    """Small hack to convert chipmunk physics to pygame coordinates"""
	    return -y+600

	def update_sprite(self,body,sprite,screen):
		p = body.position
		p = Vec2d(p.x, self.flipy(p.y))
		angle_degrees = math.degrees(body.angle)
		rotated_shape = pygame.transform.rotate(sprite, angle_degrees)
		offset = Vec2d(rotated_shape.get_size()) / 2.
		p = p - offset
		screen.blit(rotated_shape, p)

	def gaussian_noise(self):
		u = 1 - np.random.random()
		v = 1 - np.random.random()
		return np.sqrt(-2*np.log(u)) * np.cos(2 * np.pi * v)

	# Assumes points are pymunk 2d vectors. May make sense to change this to numpy at some point
	def distance(self, p1, p2):
		return (p2 - p1).get_length()

	def exp_pdf(self, val, lamb):
		assert val >= 0
		return lamb*np.exp(-lamb*val)

	def euclid_distance(self, path1, path2, weight):
		assert len(path1) == len(path2)
		# print 'lambda:', weight
		# print 'exp_pdf:', [self.exp_pdf(i/100.0, weight) for i in range((len(path1)))]
		print [self.exp_pdf(i/100.0, weight)*self.distance(path1[i], path2[i]) for i in range(len(path1))]
		return np.mean([self.exp_pdf(i/100.0, weight)*self.distance(path1[i], path2[i]) for i in range(len(path1))])
		# return np.mean([self.distance(path1[i], path2[i]) for i in range(len(path1))])

	##############################
	# define counterfactual operations
	##############################

	def difference_cause(self, w, experiment, noise, trial, cause, alternatives, df, n_simulations, animate):
		# same as the global version
		# run actual world 
	 	events = w.simulate(experiment = experiment, trial = trial, animate=animate)	

		# record actual outcome, records first collision in which ball participated 
		collision_time = float("inf")
		for event in events:
			if event['type'] == 'collision':
				for ball in event['balls']:
					if ball == cause:
						if event['step'] < collision_time:
							collision_time = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome_fine']

		# remove candidate cause 
		info = [{
			'action': 'remove',
			'ball': cause,
			'step': collision_time-1
		}]

		# noise in alternative causes 
		for alternative in alternatives: 
				info.append({
					'action': 'noise',
					'ball': alternative,
					'step': collision_time-1
				})

		outcomes = []
		for x in range(0, n_simulations):
			events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)
			for event in events:
				if event['type'] == 'outcome':
					outcome_counterfactual = event['outcome_fine']
			outcomes.append(outcome_actual != outcome_counterfactual)
		
		return any(outcomes)

	def whether_cause(self, experiment, noise, w, trial, cause, df, n_simulations, animate):
		# run actual world 
		events = w.simulate(experiment = experiment, trial = trial, animate=animate)	
		# print("events", events)
		
		# first collision between balls 		
		first_collision = {'AB': float("inf"), 'AE': float("inf"), 'BE': float("inf"), 'Abox': float("inf"), 'Bbox': float("inf"), 'Ebox': float("inf")}
		for event in events:
			if event['type'] == 'collision':
				event['balls'].sort()
				balls = ''.join(event['balls'])
				if first_collision[balls] == float("inf"):
					first_collision[balls] = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome']
		
		#first collision involving the cause 
		cause_collision = {'step': float("inf"), 'ball': ''}
		for collision in first_collision:
			if cause in collision and first_collision[collision] != float("inf") and first_collision[collision] <cause_collision['step']:
				cause_collision['step'] = first_collision[collision]
				cause_collision['ball'] = collision.replace(cause,"")

		# remove candidate cause (maybe remove right at the beginning)
		info = [{
			'action': 'remove',
			'ball': cause,
			'step': cause_collision['step']
		}
		]

		# add noise to the non-cause ball that was involved in the first collision
		if cause_collision['step'] != float("inf"):
			info.append({
				'action': 'noise',
				'ball': cause_collision['ball'],
				'step': cause_collision['step']
				})
		
		outcomes = []
		for x in range(0, n_simulations):
			events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)
			for event in events:
				if event['type'] == 'outcome':
					outcomes.append(event['outcome'] != outcome_actual)
		
		return sum(outcomes)/float(n_simulations)
	
	def how_cause(self, w, experiment, noise, trial, cause, df, animate):
		# same as the global version
		# run actual world 
		events = w.simulate(experiment = experiment, trial = trial, animate=animate)	
				
		# record actual outcome, records first collision in which ball participated 
		collision_time = float("inf")
		for event in events:
			if event['type'] == 'collision':
				for ball in event['balls']:
					if ball == cause:
						if event['step'] < collision_time:
							collision_time = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome_fine']

		# perturb candidate cause 
		info = [{
			'action': 'perturb',
			'ball': cause,
			'step': collision_time-1,
			'magnitude': 0.0001
		}]

		events = w.simulate(experiment = experiment, trial = trial, animate = animate, info = info)
		for event in events:
			if event['type'] == 'outcome':
				outcome_counterfactual = event['outcome_fine']
		
		return (outcome_counterfactual != outcome_actual)

	def cont_how(self, experiment, perturb, trial, cause, target, num_comp, lamb, animate):
		# run the actual world
		act_events, act_path = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		act_pos = act_path[target][0]

		target_first_col = 0
		for event in act_events:
			if event['type'] == 'collision' and target in event['balls'] and target_first_col == 0:
				target_first_col = event['step']

		# perturb candidate cause
		info = [{
			'action': 'perturb',
			'ball': cause,
			'step': 0,
			'magnitude': perturb
		},
		{
			'action': 'perturb_vel',
			'ball': cause,
			'step': 0,
			'magnitude': perturb
		}]

		comparisons = []
		for i in range(num_comp):
			cf_events, cf_path = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True, info=info)
			cf_pos = cf_path[target][0]
			comparisons.append(self.euclid_distance(act_pos[target_first_col+1:], cf_pos[target_first_col+1:], lamb))

		return np.mean([x for x in comparisons])

		# return np.mean(comparisons)

	def chain_check(self, chain, cause, target):
		closure = set(chain + [(y,x) for x,y in chain])
		closure_until_now = set()
		while True:
			new_relations = set((x,w) for x,y in closure for q,w in closure if q == y)

			closure_until_now = closure | new_relations

			if closure_until_now == closure:
				break

			closure = closure_until_now

		return (cause, target) in closure or (target, cause) in closure

	def balls_in_chain(self, collisions, cause):
		cols = [tuple(ev['balls']) for ev in collisions]
		closure = set(cols + [(y,x) for x,y in cols])
		closure_until_now = set()
		while True:
			new_relations = set((x,w) for x,y in closure for q,w in closure if q == y)

			closure_until_now = closure | new_relations

			if closure_until_now == closure:
				break

			closure = closure_until_now

		balls = set()
		for a,b in closure:
			if a == cause:
				balls.add(b)
			elif b == cause:
				balls.add(a)

		return balls


	def polar_convert(self, xvel, yvel):
		if xvel == 0.0 and yvel == 0.0:
			mag = 0.0
			theta = 0.0
		elif xvel == 0.0 and yvel != 0.0:
			mag = np.abs(yvel)
			theta = math.pi/2 if yvel > 0 else 3*math.pi/2
		elif xvel != 0.0 and yvel == 0.0:
			mag = np.abs(xvel)
			theta = 0 if xvel < 0 else math.pi
		else:
			mag = np.sqrt(xvel**2 + yvel**2)
			theta = np.arctan(yvel/xvel)

		return np.array([mag, theta])


	def cont_how2(self, experiment, trial, cause, target, animate):
		act_events, act_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		act_vel = act_paths[target][1]

		target_last_col = 0
		for ev in act_events:
			if ev['type'] == 'collision' and target in ev['balls']:
				target_last_col = ev['step']

		if target_last_col != 0:
			pre_vel = np.array(act_vel[target_last_col - 1])
			post_vel = np.array(act_vel[target_last_col + 1])

			print act_paths[target][0][target_last_col]

			# pre_vel = self.polar_convert(pre_x, pre_y)
			# post_vel = self.polar_convert(post_x, post_y)
			# print 'pre_vel:', pre_vel
			# print 'post_vel:', post_vel

			change = post_vel - pre_vel
			# print 'change:', change

			return np.dot(change, change)

		else: 
			return 0.0

		# act_events, act_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		# act_vel = act_paths[target][1]

		# target_last_col = 0
		# for ev in act_events:
		# 	if ev['type'] == 'collision' and target in ev['balls']:
		# 		target_last_col = ev['step']

		# print 'Collison pos:', act_paths[target][0][target_last_col]

		# if target_last_col != 0:
		# 	# This is maybe too naive
		# 	pre_x, pre_y = act_vel[target_last_col - 1]
		# 	post_x, post_y = act_vel[target_last_col + 1]

		# 	pre = np.absolute(pre_x) + np.absolute(pre_y)
		# 	post = np.absolute(post_x) + np.absolute(post_y)

		# 	x_change = float(np.absolute(pre_x - post_x))
		# 	y_change = float(np.absolute(pre_y - post_y))

		# 	if x_change != 0.0:
		# 		x_ratio = x_change/max(np.absolute(pre_x), np.absolute(post_x))
		# 	else:
		# 		x_ratio = 0.0

		# 	if y_change != 0.0:
		# 		y_ratio = y_change/max(np.absolute(pre_y), np.absolute(post_y))
		# 	else:
		# 		y_ratio = 0.0

		# 	# print 'pre_vel: ', (pre_x, pre_y)
		# 	# print 'post_vel: ', (post_x, post_y)
		# 	# print 'x_change: ', x_change			
		# 	# print 'y_change: ', y_change
		# 	# print 'x_ratio: ', x_ratio
		# 	# print 'y_ratio: ', y_ratio
		# 	# print


		# 	return (x_change + y_change)/max(pre, post)

		# 	# pre = np.absolute(pre_x) + np.absolute(pre_y)
		# 	# post = np.absolute(post_x) + np.absolute(post_y)

		# 	# change = np.absolute(pre - post)

		# 	# print 'pre_vel: ', (pre_x, pre_y)
		# 	# print 'pre_sum: ', pre
		# 	# print 'post_vel: ', (post_x, post_y)			
		# 	# print 'post_sum: ', post
		# 	# print 'change: ', change

		# 	# return float(change)/max(pre,post)

		# else:
		# 	return 0.0

		# Do we need noise or num simulations?
	def cont_how3(self, experiment, trial, cause, target, lamb, animate):
		act_events, act_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		act_pos = act_paths[target][0]

		target_first_col = 0
		for event in act_events:
			if event['type'] == 'collision' and target in event['balls'] and target_first_col == 0:
				target_first_col = event['step']

		chain = [tuple(ev['balls']) for ev in act_events if ev['type'] == 'collision']
		check = self.chain_check(chain, cause, target)

		info = [{
		'action': 'remove',
		'ball': cause,
		'step': 0
		}]

		if check:
			cf_events, cf_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, info=info, rec_paths=True)
			cf_pos = cf_paths[target][0]
			end1 = len(act_pos)
			end2 = len(cf_pos)
			for i in range(len(act_pos)):
				x_act = act_pos[i][0]
				x_cf = cf_pos[i][0]
				if x_act < 0 and end1 == len(act_pos):
					end1 = i
				elif x_cf < 0 and end2 == len(cf_pos):
					end2 = i

			# print end1 == len(act_pos)
			# print end2 == len(cf_pos)
			# print cf_pos
			comp = self.frechet(act_pos[target_first_col+1:end1], cf_pos[target_first_col+1:end2])#, lamb)

			# will need some normalization scheme. Tanh probably fine
			return comp

		else:
			return 0.0



		# run the actual world
		# act_events, act_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		# # act_vel = [x[2] for x in act_path]

		# # Get all collision events
		# collisions = [ev for ev in act_events if ev['type'] == 'collision']
		# # col_balls = balls_in_chain(collisions, cause)

		# # reverse sort events in time
		# rev_ev = sorted(collisions, key=lambda x: x['step'], reverse=True)

		# tar_found = False
		# for ev in rev_ev:
		# 	# Check whether the target is in the collision
		# 	# if it is save the change in target velocity.
		# 	# If the target is in multiple collisions, resets.
		# 	if target in ev['balls']:
		# 		tar_found = True

		# 		step = ev['step']
		# 		pre_x, pre_y = act_paths[target][1][step-1]
		# 		print 'pre:', (pre_x, pre_y)
		# 		post_x, post_y = act_paths[target][1][step+1]
		# 		print 'post:', (post_x, post_y)
		# 		change = np.abs(post_x - pre_x) + np.abs(post_y - pre_y)
		# 		print 'change:', change

		# 		in_chain = set(ev['balls'])

		# 	# If the collision takes place after the target collision ignore it
		# 	if tar_found:
		# 		ball1, ball2 = ev['balls']
		# 		if ball1 in in_chain:
		# 			in_chain.add(ball2)
		# 		elif ball2 in in_chain:
		# 			in_chain.add(ball1)
		# 		# check whether the cause is in the event. If it is calculate
		# 		# the total velocity prior to the current collision to normalize.
		# 		if cause in ev['balls']:
		# 			step = ev['step']
		# 			print 'in_chain:', in_chain
		# 			velocities = [act_paths[body][1][step-1] for body in in_chain]
		# 			print 'velocities:', velocities
		# 			total = sum([np.abs(x) + np.abs(y) for x,y in velocities])
		# 			print 'total:', total
		# 			return change/total
		# 		# Otherwise check whether each of the balls in the collision
		# 		# is a part of the chain. If it is, add the other to the chain
				

		# # If the target was not in any collisions that it is not part of the causal chain
		# # Return 0 how cause
		# if not tar_found:
		# 	return 0.0



		# collisions = {tuple(sorted(ev['balls'])):ev for ev in act_events if ev['type'] == 'collision'}

		# Will need to develop this for cases where the target collides multiple times
		# cause_col = []
		# target_col = []
		# for event in act_events:
		# 	if event['type'] == 'collision':
		# 		if cause in event['balls']:
		# 			cause_col.append(event)
		# 		if target in event['balls']:
		# 			target_col.append(event)

		# construct a graph representing the causal chain
		# causal_chain = [tuple(ev['balls']) for ev in collisions]
		# right now causal chain is undirected. May want to change that in future work because
		# causality is directed
		# in_chain = chain_check(causal_chain, cause, target)
		# direct = any([cause in col and target in col for col in causal_chain])

		# actors = tuple(sorted([cause, target]))

		# if in_chain:
		# 	if direct:
		# 		event = collisions[actors]
		# 		step = event['step']

		# 		pre_x, pre_y = act_vel[step - 1]
		# 		post_x, post_y = act_vel[step + 1]

		# 		x_change = float(np.absolute(pre_x - post_x))
		# 		y_change = float(np.absolute(pre_y - post_y))

		# 		change = x_change + y_change



		# if len(target_col) == 0:
		# 	return 0.0
		# else:
		# 	pass

		# if target_first_col != 0:
			# This is maybe too naive
			# pre_x, pre_y = act_vel[target_first_col - 1]
			# post_x, post_y = act_vel[target_first_col + 1]

			# pre = np.absolute(pre_x) + np.absolute(pre_y)
			# post = np.absolute(post_x) + np.absolute(post_y)

			# x_change = float(np.absolute(pre_x - post_x))
			# y_change = float(np.absolute(pre_y - post_y))

			# if x_change != 0.0:
			# 	x_ratio = x_change/max(np.absolute(pre_x), np.absolute(post_x))
			# else:
			# 	x_ratio = 0.0

			# if y_change != 0.0:
			# 	y_ratio = y_change/max(np.absolute(pre_y), np.absolute(post_y))
			# else:
			# 	y_ratio = 0.0

			# print 'pre_vel: ', (pre_x, pre_y)
			# print 'post_vel: ', (post_x, post_y)
			# print 'x_change: ', x_change			
			# print 'y_change: ', y_change
			# print 'x_ratio: ', x_ratio
			# print 'y_ratio: ', y_ratio

			# return (x_change + y_change)/max(pre, post)

			# pre = np.absolute(pre_x) + np.absolute(pre_y)
			# post = np.absolute(post_x) + np.absolute(post_y)

			# change = np.absolute(pre - post)

			# print 'pre_vel: ', (pre_x, pre_y)
			# print 'pre_sum: ', pre
			# print 'post_vel: ', (post_x, post_y)			
			# print 'post_sum: ', post
			# print 'change: ', change

			# return float(change)/max(pre,post)

		# else:
		# 	return 0.0




	def sufficient_cause(self, w, experiment, noise, trial, cause, alternatives, target, df, n_simulations, animate):
		# run actual world 
		events = w.simulate(experiment = experiment, trial = trial, animate = animate)	

		# first collision between balls 		
		first_collision = {'AB': float("inf"), 'AE': float("inf"), 'BE': float("inf")}
		for event in events:
			if event['type'] == 'collision':
				event['balls'].sort()
				balls = ''.join(event['balls'])
				if first_collision[balls] == float("inf"):
					first_collision[balls] = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome']
		print("first_collision", first_collision)
		
		#first collision involving the alternative cause 
		alternative = alternatives[0]
		alternative_collision = {'step': float("inf"), 'ball': ''}
		for collision in first_collision:
			if alternative in collision and first_collision[collision] != float("inf") and first_collision[collision] <alternative_collision['step']:
				alternative_collision['step'] = first_collision[collision]
				alternative_collision['ball'] = collision.replace(alternative,"")
		print("alternative_collision", alternative_collision)

		#first collision involving the effect
		effect = target
		effect_collision = {'step': float("inf")}
		for collision in first_collision:
			if effect in collision and first_collision[collision] != float("inf") and first_collision[collision] <effect_collision['step']:
				effect_collision['step'] = first_collision[collision]
		print("effect_collision", effect_collision)
		
		outcomes = []
		for x in range(0, n_simulations):
			info = []
			# remove alternative cause 
			info = [{
				'action': 'remove',
				'ball': alternative,
				'step': 0 # might be ok to remove shortly before first collision
			}
			]

			# add noise to the ball that was involved in the first collision with the alternative cause
			if alternative_collision['step'] != float("inf"):
				info.append({
					'action': 'noise',
					'ball': alternative_collision['ball'],
					'step': alternative_collision['step']
					})

			events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)		
			
			# record outcome in the counterfactual contingency 
			for event in events:
				if event['type'] == 'outcome':
					outcome_counterfactual = event['outcome']

			info = []
			# remove alternative cause 
			info.append({
				'action': 'remove',
				'ball': alternative,
				'step': 0 
			})

			# remove candidate cause 
			info.append({
				'action': 'remove',
				'ball': cause,
				'step': 0	 
				})

			# apply noise to ball E (from when the first collision happens in the actual situation)
			info.append({
				'action': 'noise',
				'ball': 'E',
				'step': effect_collision['step']
				})

			events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)
			
			for event in events:
				if event['type'] == 'outcome':
					outcome_counterfactual_contingency = event['outcome']
			 
			outcomes.append((outcome_actual == outcome_counterfactual) and (outcome_counterfactual != outcome_counterfactual_contingency))
		
		return sum(outcomes)/float(n_simulations)

	def robust_cause(self, w, experiment, noise, perturb, trial, cause, alternatives, target, df, n_simulations, animate):
			# run actual world 
			events = w.simulate(experiment = experiment, trial = trial, animate=animate)	

			# first collision between balls 		
			first_collision = {'AB': float("inf"), 'AE': float("inf"), 'BE': float("inf")}
			for event in events:
				if event['type'] == 'collision':
					event['balls'].sort()
					balls = ''.join(event['balls'])
					if first_collision[balls] == float("inf"):
						first_collision[balls] = event['step']
				if event['type'] == 'outcome':
					outcome_actual = event['outcome']

			#first collision involving the effect
			effect = target
			effect_collision = {'step': float("inf")}
			for collision in first_collision:
				if effect in collision and first_collision[collision] != float("inf") and first_collision[collision] <effect_collision['step']:
					effect_collision['step'] = first_collision[collision]

			outcomes = []
			for x in range(0, n_simulations):
				info = []
				
				# perturb alternative cause 
				for alternative in alternatives: 
					info.append({
						'action': 'perturb',
						'ball': alternative,
						'step': 0,
						'magnitude': perturb
					})

				events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)
				
				# record outcome in counterfactual
				for event in events:
					if event['type'] == 'outcome':
						outcome_counterfactual = event['outcome']

				info = []
				# perturb and apply noise to alternative cause 
				
				for alternative in alternatives: 
					# apply perturbation
					info.append({
						'action': 'perturb',
						'ball': alternative,
						'step': 0,
						'magnitude': perturb
					})

				# remove cause 
				info.append({
					'action': 'remove',
					'ball': cause,
					'step': 0
					})

				# apply noise to ball E (from when the first collision happens in the actual situation)
				info.append({
					'action': 'noise',
					'ball': 'E',
					'step': effect_collision['step']
					})

				events = w.simulate(experiment = experiment, trial = trial, animate = animate, noise = noise, info = info)
				for event in events:
					if event['type'] == 'outcome':
						outcome_counterfactual_contingency = event['outcome']
				 
				outcomes.append((outcome_actual == outcome_counterfactual) and (outcome_counterfactual != outcome_counterfactual_contingency))
			
			return sum(outcomes)/float(n_simulations)


	def alt_robust(self, experiment, noise, trial, cause, target, n_simulations, animate):
		# run the actual world
		events = self.simulate(experiment=experiment, trial=trial, animate=animate)

		cause_first_col = float('inf')
		objects = {target}

		for event in events:
			if event['type'] == 'collision' and cause in event['balls'] and cause_first_col == float('inf'):
				objects = objects | set(event['balls'])
				cause_first_col = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome']

		outcomes = []
		for i in range(n_simulations):
			info = [{'action': 'noise', 'ball': obj, 'step': cause_first_col} for obj in objects]
			cf_help = self.simulate(experiment=experiment, trial=trial, animate=animate, noise=noise, info=info)
			for event in cf_help:
				if event['type'] == 'outcome':
					help_outcome = event['outcome']

			info = [{'action': 'remove', 'ball': cause, 'step': cause_first_col}] + [{'action': 'noise', 'ball': obj, 'step': cause_first_col} for obj in objects.difference({cause})]
			cf_nohelp = self.simulate(experiment=experiment, trial=trial, animate=animate, noise=noise, info=info)
			for event in cf_nohelp:
				if event['type'] == 'outcome':
					nohelp_outcome = event['outcome']

			outcomes.append(help_outcome != nohelp_outcome)

		return sum(outcomes)/float(n_simulations)

	def calc_ideal(self, step, start_pos, start_vel, animate):
		center_exit = (0, self.height/2)

		ideal_dir = Vec2d(center_exit[0] - start_pos[0], center_exit[1] - start_pos[1])
		# In order to ensure the new vector has the same linear velocity as the actual,
		# we need a scale factor
		scale_factor = np.sqrt(start_vel.get_length_sqrd()/ideal_dir.get_length_sqrd())/self.speed

		ideal_v = scale_factor*ideal_dir

		trial = [{'trial': 0, 'balls': [{'name': self.target_ball, 'position': start_pos, 'velocity': ideal_v}]}]
		# info = [{'action': 'noise', 'ball': self.target_ball, 'step': step}]
		_, ideal_paths = self.simulate(experiment='ideal',animate=animate,trial=trial,rec_paths=True,start_step=step,pre_def=trial)
		ideal_path = ideal_paths['B']

		return ideal_path

	def hausdorff(self, path, ideal):
		table = np.array([[self.distance(p1, p2) for p1 in ideal] for p2 in path])
		return max([np.amax(np.amin(table, axis=1)), np.amax(np.amin(table, axis=0))])

	# def frechet(self, path, ideal, table):
	# 	i = len(path) - 1
	# 	j = len(ideal) - 1

	# 	if table[i][j] > -1:
	# 		return table[i][j]
	# 	if i == 0 and j == 0:
	# 		table[i][j] = self.distance(path[0], ideal[0])
	# 		return table[i][j]
	# 	elif i > 0 and j == 0:
	# 		table[i][j] = max(self.frechet(path[1:], ideal, table), self.distance(path[0], ideal[0]))
	# 		return table[i][j]
	# 	elif i == 0 and j > 0:
	# 		table[i][j] = max(self.frechet(path, ideal[1:], table), self.distance(path[0], ideal[0]))
	# 		return table[i][j]
	# 	elif i > 0 and j > 0:
	# 		table[i][j] = max(min(self.frechet(path[1:], ideal, table), self.frechet(path[1:], ideal[1:], table), self.frechet(path, ideal[1:], table)), self.distance(path[0], ideal[0]))
	# 		return table[i][j]
	# 	else:
	# 		table[i][j] = float('inf')


	# def run_frechet(self, path, ideal):
	# 	table = np.ones((len(path), len(ideal)))*-1
	# 	return self.frechet(path, ideal, table)

	def frechet(self, path, ideal, backtrack=False):
		table = np.ones((len(path), len(ideal)))*-1

		for i in range(len(path)):
			for j in range(len(ideal)):
				path_point = path[i]
				ideal_point = ideal[j]

				if i == 0 and j == 0:
					table[i][j] = self.distance(path_point, ideal_point)
				elif i == 0 and j > 0:
					table[i][j] = max(self.distance(path_point, ideal_point), table[i][j-1])
				elif i > 0 and j == 0:
					table[i][j] = max(self.distance(path_point, ideal_point), table[i-1][j])
				else:
					table[i][j] = max(self.distance(path_point, ideal_point), min(table[i][j-1], table[i-1][j-1], table[i-1][j]))

		if backtrack:
			parameterization = []
			i = len(path) - 1
			j = len(ideal) - 1
			while i > -1 and j > -1:
				parameterization.append((i,j))
				if i > 0 and j > 0:
					arg = np.argmin([table[i-1][j],table[i-1][j-1],table[i][j-1]])
					new_i, new_j = [(i-1,j),(i-1,j-1),(i,j-1)][arg]
					i = new_i
					j = new_j
				elif i > 0 and j == 0:
					i -= 1
				elif i == 0 and j > 0:
					j -= 1
				else:
					i = -1
					j = -1

			return table[len(path)-1][len(ideal)-1], parameterization


		return table[len(path)-1][len(ideal)-1]

	def help_assess(self, experiment, noise, trial, cause, target, n_simulations, lamb, animate):
		# simulate the actual event
		events_actual, actual_paths = self.simulate(experiment=experiment, trial=trial, animate=animate, rec_paths=True)
		path_actual = actual_paths[target]

		# find the time of the first collision for the cause and effect ball if they exist
		# also record the outcome
		cause_first_col = float('inf')
		target_first_col = 0


		for event in events_actual:
			if event['type'] == 'collision' and cause in event['balls'] and cause_first_col == float('inf'):
				cause_first_col = event['step']
			if event['type'] == 'collision' and target in event['balls'] and target_first_col == 0:
				target_first_col = event['step']
			if event['type'] == 'outcome':
				outcome_actual = event['outcome']


		# simulate the counterfactual scenario where the cause ball is removed
		info = [{'action': 'remove', 'ball': cause, 'step':cause_first_col - 1}]
		events_cf, cf_paths = self.simulate(experiment=self.experiment, trial=trial, animate=animate, rec_paths=True, info=info)
		path_cf = cf_paths[target]

		# if the effect ball took place in a collision, calculate the ideal path to the goal from the position of that first collision. Otherwise calculate the ideal path from the ball's starting place
		if target_first_col != 0:
			start_pos = path_actual[0][target_first_col]
			start_vel = path_actual[1][target_first_col]
			ideal = self.calc_ideal(target_first_col, start_pos, start_vel, animate)
		else:
			start_pos = path_actual[0][0]
			start_vel = path_actual[1][0]
			ideal = self.calc_ideal(0, start_pos, start_vel, animate)

		comp_actual = [x for x in path_actual[0][target_first_col:]]
		comp_cf = [x for x in path_cf[0][target_first_col:]]
		id_loc = [x for x in ideal[0]]

		d1 = self.euclid_distance(comp_actual, id_loc, lamb)
		d2 = self.euclid_distance(comp_cf, id_loc, lamb)
		# d1, pars1 = self.frechet(comp_actual, id_loc, True)
		# d2, pars2 = self.frechet(comp_cf, id_loc, True)
		# print 'actual path:', d1
		# print 'cf path:', d2
		# print 'cf parameterization', pars2
		# print 'cf distances:', [self.distance(comp_cf[i],id_loc[j]) for i,j in pars2]

		return (d2 - d1)/d2


# w = World()
# path = [Vec2d(0,0), Vec2d(1,1), Vec2d(2,2)]
# ideal = [Vec2d(0,0), Vec2d(1,0)]

# path = [Vec2d(0, x) for x in range(10)]
# ideal = [Vec2d(x,0) for x in range(10)]

# print w.run_frechet(path, ideal)

# ans = w.help_assess('clang', 1, 7, 'A', 'B', 1, False)
# print 'helped:', ans
