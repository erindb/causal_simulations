/**
 * jspsych-html-keyboard-response
 * Josh de Leeuw
 *
 * plugin for displaying a stimulus and getting a keyboard response
 *
 * documentation: docs.jspsych.org
 *
 **/

 var keycode_to_letter_map = {70: "F", 74: "J"};


jsPsych.plugins["exp01-gif-keyboard-response"] = (function() {

  var plugin = {};

  plugin.info = {
    name: 'exp01-gif-keyboard-response',
    description: '',
    parameters: {
      stimulus: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Stimulus',
        default: undefined,
        description: 'The HTML string to be displayed'
      },
      choices: {
        type: jsPsych.plugins.parameterType.KEYCODE,
        array: true,
        pretty_name: 'Choices',
        default: jsPsych.ALL_KEYS,
        description: 'The keys the subject is allowed to press to respond to the stimulus.'
      },
      stimulus_duration: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Stimulus duration',
        default: null,
        description: 'How long to hide the stimulus.'
      },
      response_ends_trial: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Response ends trial',
        default: true,
        description: 'If true, trial will end when subject makes a response.'
      },
    }
  }

  plugin.trial = function(display_element, trial) {

    var new_html = '<div id="exp01-gif-keyboard-response-stimulus">'+trial.stimulus+'</div>';

    // draw
    display_element.innerHTML = new_html;

    $(".f_prompt").css({"background-color": "none"});
    $(".j_prompt").css({"background-color": "none"});

    // store response
    var final_response_allowed = trial.response_ends_trial;
    var response = {
      rt: null,
      key: null
    };
    var history = [];

    // function to end trial when it is time
    var end_trial = function() {

      // kill any remaining setTimeout handlers
      jsPsych.pluginAPI.clearAllTimeouts();

      // kill keyboard listeners
      if (typeof keyboardListener !== 'undefined') {
        jsPsych.pluginAPI.cancelKeyboardResponse(keyboardListener);
      }

      var key_press = response.key;
      var letter_response = keycode_to_letter_map[key_press];

      if (letter_response == "F") {
        $(".f_prompt").css({"background-color": "gray"});
      } else {
        $(".j_prompt").css({"background-color": "gray"});
      }

      // gather the data to store for the trial
      var trial_data = _.extend(trial, {
        "rt": response.rt,
        "key_press": key_press,
        "letter_response": letter_response,
        "response": key_mapping[letter_response],
        "history": history
      });
      // console.log(trial_data);

      // move on to the next trial
      setTimeout(function() {

        // clear the display
        display_element.innerHTML = '';

        jsPsych.finishTrial(trial_data);
      }, 100);
    };

    // function to handle responses by the subject
    var after_response = function(info) {

      // after a valid response, the stimulus will have the CSS class 'responded'
      // which can be used to provide visual feedback that a response was recorded
      display_element.querySelector('#exp01-gif-keyboard-response-stimulus').className += ' responded';

      response = info;
      history.push(JSON.stringify(response));

      if (final_response_allowed) {
        end_trial();
      }
    };

    // start the response listener
    if (trial.choices != jsPsych.NO_KEYS) {
      var keyboardListener = jsPsych.pluginAPI.getKeyboardResponse({
        callback_function: after_response,
        valid_responses: trial.choices,
        rt_method: 'date',
        persist: true,
        allow_held_key: false
      });
    }

    // Things that happen after the video is finished playing the first time:
    jsPsych.pluginAPI.setTimeout(function() {
      // The video will have the CSS class 'presented' which can be used to
      // provide visual feedback that the video was presented
      display_element.querySelector('.physics_video').className += ' presented';

      // // The replay button will become visible
      // $("#replay").css({"visibility": "visible"})

      $(".after_video_finishes").css({"visibility": "visible"});

      // The response listener will allow the user to continue.
      final_response_allowed = true;
    }, trial.stimulus_duration);

  };

  return plugin;
})();
