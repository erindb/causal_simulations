var worlds_to_evaluate = [
  {
    "a_velocity": -2,
    "a_position": 0,
    "b_velocity": -2,
    "b_position": 1,
    "gloss": "B follows A"
  },
  {
    "a_velocity": -2,
    "a_position": 0,
    "b_velocity": -1,
    "b_position": 1,
    "gloss": "B follows A"
  },
  {
    "a_velocity": -2,
    "a_position": 0,
    "b_velocity": 0,
    "b_position": 1,
    "gloss": "A moves away from B"
  },
  {
    "a_velocity": -2,
    "a_position": 0,
    "b_velocity": 1,
    "b_position": 1,
    "gloss": "opposite directions"
  },
  {
    "a_velocity": -2,
    "a_position": 0,
    "b_velocity": 2,
    "b_position": 1,
    "gloss": "opposite directions"
  },
  {
    "a_velocity": -1,
    "a_position": 0,
    "b_velocity": -2,
    "b_position": 1,
    "gloss": "B hits A"
  },
  {
    "a_velocity": -1,
    "a_position": 0,
    "b_velocity": -1,
    "b_position": 1,
    "gloss": "B follows A"
  },
  {
    "a_velocity": -1,
    "a_position": 0,
    "b_velocity": 0,
    "b_position": 1,
    "gloss": "A moves away from B"
  },
  {
    "a_velocity": -1,
    "a_position": 0,
    "b_velocity": 1,
    "b_position": 1,
    "gloss": "opposite directions"
  },
  {
    "a_velocity": -1,
    "a_position": 0,
    "b_velocity": 2,
    "b_position": 1,
    "gloss": "opposite directions"
  },
  {
    "a_velocity": 0,
    "a_position": 0,
    "b_velocity": -2,
    "b_position": 1,
    "gloss": "B hits A"
  },
  {
    "a_velocity": 0,
    "a_position": 0,
    "b_velocity": -1,
    "b_position": 1,
    "gloss": "B hits A"
  },
  {
    "a_velocity": 0,
    "a_position": 0,
    "b_velocity": 0,
    "b_position": 1,
    "gloss": "no movement"
  },
  {
    "a_velocity": 0,
    "a_position": 0,
    "b_velocity": 1,
    "b_position": 1,
    "gloss": "B moves away from A"
  },
  {
    "a_velocity": 0,
    "a_position": 0,
    "b_velocity": 2,
    "b_position": 1,
    "gloss": "B moves away from A"
  },
  {
    "a_velocity": 1,
    "a_position": 0,
    "b_velocity": -2,
    "b_position": 1,
    "gloss": "symmetric collision"
  },
  {
    "a_velocity": 1,
    "a_position": 0,
    "b_velocity": -1,
    "b_position": 1,
    "gloss": "symmetric collision"
  },
  {
    "a_velocity": 1,
    "a_position": 0,
    "b_velocity": 0,
    "b_position": 1,
    "gloss": "A hits B"
  },
  {
    "a_velocity": 1,
    "a_position": 0,
    "b_velocity": 1,
    "b_position": 1,
    "gloss": "A follows B"
  },
  {
    "a_velocity": 1,
    "a_position": 0,
    "b_velocity": 2,
    "b_position": 1,
    "gloss": "A follows B"
  },
  {
    "a_velocity": 2,
    "a_position": 0,
    "b_velocity": -2,
    "b_position": 1,
    "gloss": "symmetric collision"
  },
  {
    "a_velocity": 2,
    "a_position": 0,
    "b_velocity": -1,
    "b_position": 1,
    "gloss": "symmetric collision"
  },
  {
    "a_velocity": 2,
    "a_position": 0,
    "b_velocity": 0,
    "b_position": 1,
    "gloss": "A hits B"
  },
  {
    "a_velocity": 2,
    "a_position": 0,
    "b_velocity": 1,
    "b_position": 1,
    "gloss": "A hits B"
  },
  {
    "a_velocity": 2,
    "a_position": 0,
    "b_velocity": 2,
    "b_position": 1,
    "gloss": "A follows B"
  }
]

try{ 
  module.exports = {
    worlds_to_evaluate: worlds_to_evaluate
  }
} catch(err) {
}