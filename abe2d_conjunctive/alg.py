import numpy as np

def get_hh(prob_a, prob_b):

  stickiness = 0.53

  possible_angles = 13

  def angles(n):
    return float(n)/possible_angles

  def cf_prob(choice_prob, same_as_actual):
    if same_as_actual:
      return stickiness + (1-stickiness)*choice_prob
    else:
      return (1-stickiness)*choice_prob

  p_a_exists = cf_prob(0.5, True)
  p_b_exists = cf_prob(0.5, True)

  p_a_is_off = cf_prob(prob_a, True)
  p_b_is_off = cf_prob(prob_b, True)

  p_a_same_v = cf_prob(angles(1), True)
  p_b_same_v = cf_prob(angles(1), True)

  # There are 5 velocities that A can take that aren't the original velocity for which E could still go through.
  # For 2 of them, there are 2 different values of B for which E would still go through.
  p_a_diff_and_b_diff = cf_prob(angles(2), False) * cf_prob(angles(2), False)
  # For one of the, B could keep the same value as in the actual world and E would still go through
  p_a_diff_and_b_star = cf_prob(angles(1), False) * cf_prob(angles(1), True)
  # For that value of A and for two others, if B is equal to A, E would go through
  p_a_diff_and_b_same_as_a = cf_prob(angles(3), False) * cf_prob(angles(1), False)
  # so here's all the HH worlds:
  p_e_goes_thru_given_a_diff_and_b_is_off = p_a_diff_and_b_diff + p_a_diff_and_b_star + p_a_diff_and_b_same_as_a

  # if A exists and its velocity changes, the how premise is satisfied
  p_a_diff = p_a_exists * cf_prob(angles(possible_angles - 1), False)

  num = p_a_exists * p_b_exists * p_a_is_off * p_b_is_off * p_e_goes_thru_given_a_diff_and_b_is_off

  print(num / p_a_diff)

get_hh(0.8, 0.2)
get_hh(0.2, 0.8)