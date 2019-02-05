/*

- ☑ 25 within-Ss trials - 5 velocities per ball (-2, -1, 0, 1, 2)
- ☑ 3 between-Ss conditions - "A moved B", "A caused B to move", "A affected B"
- Keyboard responses
- ☑ Positions and colors of balls randomized trial-by-trial
- ☑ key mappings randomized between Ss

*/


// 3 between-Ss conditions - "A moved B", "A caused B to move", "A affected B"
var utterance = _.sample(["A moved B", "A caused B to move", "A affected B"]);
// key mappings randomized between Ss
var key_mapping = _.sample([{F: "yes", J: "no"}, {J: "yes", F: "no"}]);

// 25 within-Ss trials - 5 velocities per ball (-2, -1, 0, 1, 2)
// Positions and colors of balls randomized trial-by-trial
var get_trial_variables = function() {
  // 25 within-Ss trials - 5 velocities per ball (-2, -1, 0, 1, 2)
  var unique_velocity_values = [-2, -1, 0, 1, 2];
  var velocity_pairs = _.reduce(
    unique_velocity_values,
    function(all_velocity_pairs, ball_a_velocity) {
      var velocity_pairs_given_a = _.reduce(
        unique_velocity_values,
        function(velocity_pairs_given_a, ball_b_velocity) {
          return _.concat(
            velocity_pairs_given_a,
            [{a_velocity: ball_a_velocity, b_velocity: ball_b_velocity}]
          );
        },
        []
      );
      return _.concat(all_velocity_pairs, velocity_pairs_given_a);
    },
    []
  );

  // Positions and colors of balls randomized trial-by-trial
  var positions = function() {
    return _.sample([
      {a_position: 0, b_position: 1},
      {b_position: 0, a_position: 1}
    ]);
  };
  var colors = function() {
    return _.sample([
      {a_color: "red", b_color: "blue"},
      {a_color: "blue", b_color: "red"}
    ]);
  };
  var trial_parameters = _.map(velocity_pairs, function(vs) {
    return _.extend(
      _.extend(vs, positions()),
      colors()
    );
  });

  // Determine videos for each trial given positions and colors
  var trial_params_and_videos = _.map(trial_parameters, function(s) {
    var a_ball = s.a_color + "_" + s.a_velocity;
    var b_ball = s.b_color + "_" + s.b_velocity;
    var pos0_ball = s.a_position==0 ? a_ball : b_ball;
    var pos1_ball = s.a_position==1 ? a_ball : b_ball;
    var video_label = pos0_ball + "_" + pos1_ball;
    return _.extend(s, {
      video_label: video_label
    });
  });

  // Write useful strings for humans to parse the situations
  var all_trial_variables = _.map(trial_params_and_videos, function(s) {
    // A hits B ; B hits A ; no movement ; opposite directions ;
    // symmetric collision ; A moves away from B ; B moves away from A ;
    // B follows A ; A follows B

    var a_moves_towards_b = (
      (s.a_position==0 && s.a_velocity>0) ||
      (s.a_position==1 && s.a_velocity<0));
    var b_moves_towards_a = (
      (s.b_position==0 && s.b_velocity>0) ||
      (s.b_position==1 && s.b_velocity<0));
    var same_speed = (Math.abs(s.a_velocity) == Math.abs(s.b_velocity));
    var b_faster = (Math.abs(s.a_velocity) < Math.abs(s.b_velocity));

    var gloss = "";
    if (a_moves_towards_b) {
      if (b_moves_towards_a) {
        gloss = "symmetric collision";
      } else if (b_faster || same_speed) {
        gloss = "A follows B";
      } else {
        gloss = "A hits B";
      }
    } else if (s.a_velocity==0) {
      if (b_moves_towards_a) {
        gloss = "B hits A";
      } else if (s.b_velocity==0) {
        gloss = "no movement";
      } else {
        gloss = "B moves away from A";
      }
    } else {
      // A moves away from B
      if (b_moves_towards_a) {
        if (b_faster) {
          gloss = "B hits A";
        } else {
          gloss = "B follows A";
        }
      } else if (s.b_velocity==0) {
        gloss = "A moves away from B";
      } else {
        gloss = "opposite directions";
      }
    }

    return _.extend(s, {
      ball_a: "the <span class='" + s.a_color + "'>" + s.a_color + "</span> ball",
      ball_b: "the <span class='" + s.b_color + "'>" + s.b_color + "</span> ball",
      ball_a_caps: "The <span class='" + s.a_color + "'>" + s.a_color + "</span> ball",
      ball_b_caps: "The <span class='" + s.b_color + "'>" + s.b_color + "</span> ball",
      gloss: gloss,
      key_mapping_f: key_mapping.F,
      key_mapping_j: key_mapping.J
    });
  });

  return all_trial_variables;
};

$(document).ready(function() {
  var extras = $(".extras");

  var welcome = {
    type: "html-button-response",
    stimulus: $("#welcome").html(),
    choices: ["Start"],
    on_load: function() {
      extras.children().filter(".welcome").each(function() {
        $("#jspsych-content").append(this);
      });
    }
  };

  var trial = {
    type: "exp01-gif-keyboard-response",
    stimulus: $("#trial").html(),
    stimulus_duration: 1000,
    choices: ["f", "j"],
    timeline: get_trial_variables(),
    response_ends_trial: false,
    on_load: function() {
      $(".ball_a_caps").html(this.ball_a_caps);
      $(".ball_a").html(this.ball_a);
      $(".ball_b_caps").html(this.ball_b_caps);
      $(".ball_b").html(this.ball_b);
      $(".f_meaning").html(key_mapping.F);
      $(".j_meaning").html(key_mapping.J);
    }
  };

  // var demographics = {
  //   type: "html-button-response",
  //   stimulus: $("#demographics"),
  //   choices: ["Submit Responses"]
  // }

  var demographics = {
    type: 'survey-text',
    preamble: $("#demographics").html(),
    questions: [
      {
        prompt: "We would be interested in any comments you have about this study. Please type them here:",
        rows: 5,
        columns: 80
      }
    ],
    button_label: "Submit HIT Responses",
    on_load: function() {
      extras.children().filter(".demographics").each(function() {
        $("#jspsych-content").append(this);
      });
    }
  };

  var thanks = {
    type: "html-keyboard-response",
    stimulus: $("#thanks").html(),
    choices: jsPsych.NO_KEYS,
    on_start: function() {
      console.log(jsPsych.data.get().values())
      var data = _.map(jsPsych.data.get().values(), function(x) {
        x.stimulus = null;
        return x;
      });
      console.log(data);
      setTimeout(function() {
        $("#submitting").css({"display": "none"});
        $("#submitted").css({"display": "block"});
      }, 3000);
    }
  };

  jsPsych.init({
      timeline: [welcome, trial, demographics, thanks]
  });
});

// var trial = {
//   type: 'html-keyboard-response',
//   timeline: _.map(function(s) {
//     return _.extend(s, {
//       // Positions and colors of balls randomized trial-by-trial
//       positions: positions(),
//       colors: colors()
//     });
//   }, [{stimulus: 'gif here'}]),
//   randomize_order: true
// };

// var timeline = [trial];

// jsPsych.init({
//   timeline: timeline
// });