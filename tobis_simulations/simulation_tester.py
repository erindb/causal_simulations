# A module for testing and building simulations without running them through causal inference

from model import World
import sys


##############################
# parameters
##############################
# trial = int(sys.argv[1])
# To play a single video make trial an int. To play a series of videos make trial a tuple with the range
trial = (0,19)
# A string signifying the experiment file to draw from. The experiment name is the portion of the file string that comes before "_trials"
# Make sure the trial numbers in trial correspond to the actual number of trials in the experiment file
experiment = '2ball'
animate = True


##############################
# run simulations 
##############################

w = World()

if isinstance(trial, int):
	w.simulate(experiment, animate, i)
else:
	for i in range(trial[0], trial[1]):
		w.simulate(experiment, animate, i)
