import copy
import numpy as np
from bokeh import events
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
    }
    oscTarget = 0;
    </script>
    '''))



def __speak_js(utterance):
    return f"""
        window.speechSynthesis.cancel();
        let msg = new SpeechSynthesisUtterance({utterance});
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
    if(label[idx] != oscTarget) {
        return;
    }
    diff[idx] = Math.abs(mouseX - val);
    nearestIdx = (diff[nearestIdx] < diff[idx]) ? nearestIdx : idx;
});

let nearestX = x[nearestIdx];
let nearestY = y[nearestIdx];
"""


__COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf']


def plot(x, y=None, label=None, width=400, height=400, margin_x=1, title="graph"):
    assert type(x) == list, "x must be list type data."
    if label:
        assert max(label) < len(__COLORS), "max label must be lower {}".format(len(__COLORS))

    __set_context()
    output_notebook()

    p = figure(plot_width=width, plot_height=height, tools="", toolbar_location=None)

    if y == None:
        y = copy.copy(x)
        x = np.arange(len(x)).tolist()

    if label == None:
        label = np.zeros_like(y).tolist()

    colors = [__COLORS[c] for c in label]
    p.scatter(x, y, line_color=colors, fill_color=colors)

    hover_code = """
    let mouseX = cb_data.geometry.x;
    %s
    const marginX = %s;

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
    """ % (__COMMON_JS, margin_x)

    callback = CustomJS(args={"x": x, "y": y, "label": label}, code=hover_code)
    p.add_tools(HoverTool(tooltips=None, callback=callback))

    tap_code = """
    let mouseX = cb_obj.x;
    %s
    %s
    """ % (__COMMON_JS, __speak_js("`X is ${nearestX}. Y is ${nearestY}`"))
    p.js_on_event(events.Tap, CustomJS(args={"x": x, "y": y, "label": label},
                                       code=tap_code))

    double_tap_code = """
    oscTarget = (oscTarget + 1) %% (maxLabel + 1);
    %s
    """ % (__speak_js("`label ${oscTarget} is selected`"))
    p.js_on_event(events.DoubleTap, CustomJS(args={"maxLabel": max(label)},
                                             code=double_tap_code))

    p.js_on_event(events.MouseEnter, __speak_enter(title))
    p.js_on_event(events.MouseLeave, __speak_leave(title))

    show(p)
