import copy
import numpy as np
from bokeh import events
from bokeh.io import output_file
from bokeh.models import CustomJS, HoverTool
from bokeh.plotting import figure, output_notebook, show
from IPython.display import HTML, display


def __set_context():
    display(HTML('''
    <script>
        if (typeof osc === 'undefined') {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            audioGain = audioContext.createGain();
            panNode = audioContext.createStereoPanner();
            osc = audioContext.createOscillator();
            osc.connect(panNode);
            panNode.connect(audioGain);
            audioGain.connect(audioContext.destination);
            osc.start(audioContext.currentTime);
            audioGain.gain.setValueAtTime(0, audioContext.currentTime);
            console.log("set context!");
        }
    </script>
    '''))

    output_notebook()



def __speak_js(utterance):
	return f"""
		window.speechSynthesis.cancel();
		var msg = new SpeechSynthesisUtterance({utterance});
		msg.lang = "en-US";
		window.speechSynthesis.speak(msg);
		"""


def __speak_enter(title="image"):
	return CustomJS(code=__speak_js(f"\'Enter {title}\'"))


def __speak_leave(title="image"):
	return CustomJS(code=__speak_js(f"\'Leave {title}\'"))


__COMMON_JS = """
let minX = Math.min(...x);
let maxX = Math.max(...x);
let minY = Math.min(...y);
let maxY = Math.max(...y);

if((mouseX == Infinity) || (mouseX < minX) || (mouseX > maxX)) {
	return;
}

var diff = [];
var nearestIdx = 0;
x.forEach(function(val, idx){
	diff[idx] = Math.abs(mouseX - val);
	nearestIdx = (diff[nearestIdx] < diff[idx]) ? nearestIdx : idx;
});

var nearestX = x[nearestIdx];
var nearestY = y[nearestIdx];
"""


def plot(x, y=None, width=400, height=400, margin_x=1, title="graph"):
    __set_context()

    p = figure(plot_width=width, plot_height=height, tools="", toolbar_location=None)

    if y == None:
        y = copy.copy(x)
        x = np.arange(len(x)).tolist()

    p.scatter(x, y)

    hover_code = f"""
    let mouseX = cb_data.geometry.x;
    {__COMMON_JS}
    const marginX = {margin_x};

    if(diff[nearestIdx] > marginX) {
        return;
    }

    const gain = 0.4; // max: 1.0
    osc.type = 'triangle'; // sine, square, sawtooth, triangle
    osc.frequency.value = 261.626 + (nearestY - minY) / (maxY - minY) * 261.626 // Hz
    audioGain.gain.linearRampToValueAtTime(gain, audioContext.currentTime + 0.2); // atack
    audioGain.gain.setTargetAtTime(0, audioContext.currentTime + 0.2, 0.5); // decay, sustain

    let pan = (nearestX - minX) / (maxX - minX) * 2 - 1;
    panNode.pan.value = pan;  // left:-1 ~ right:1
    """

    callback = CustomJS(args={"x": x, "y": y}, code=hover_code)
    p.add_tools(HoverTool(tooltips=None, callback=callback))

    tap_code = f"""
    let mouseX = cb_obj.x;
    {__COMMON_JS}
    {__speak_js("`X is ${nearestX}. Y is ${nearestY}`"}
    """

    p.js_on_event(events.Tap, CustomJS(args={"x": x, "y": y}, code=tap_code))
    p.js_on_event(events.MouseEnter, speak_enter(title))
    p.js_on_event(events.MouseLeave, speak_leave(title))

    output_file("audio_plot_lib.html")
    show(p)

