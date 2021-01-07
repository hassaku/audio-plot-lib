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


def __speak_inout(title="image", enter=True, read_label=False):
    if read_label and enter:
        label_message = ". Label ${oscTarget} is selected. Double click to change."
    else:
        label_message = ""


    if enter:
        inout_message = f"Enter {title}"

    else:
        inout_message = f"Leave {title}"

    return CustomJS(code=__speak_js(f"`{inout_message + label_message}`"))


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


def plot(y: list, x: list=None, label: list=None, width: int=400, height: int=400,
        margin_x: int=1, title: str="graph", notebook: bool=True):
    """Plots that represent data with sound and can be checked interactively

    You can interactively check the data in graph form by moving the mouse cursor.
    When you enter or leave the graph image, you will be notified by voice.
    Also, when you move the mouse left or right on the graph image,
    the y-axis value corresponding to that location will be expressed with a high or low tone.
    A single click will read out the value corresponding to that location.
    Also, double-clicking switches the group according to the label specified as an option.

    Parameters
    ----------
    y : list
        A list of values to be graphed.
    x : list
        A list of x-axis values corresponding to y-axis values.
        If not specified, it is substituted by the value of the equal interval. Optional.
    label : list
        A list of grouping numbers for each value, which must start with zero.
        You can compare the graph data by sound, switching between each number. Optional.
    width : int
        Width of the graph image (in pixels). Optional.
    height : int
        Height of the graph image (in pixels). Optional.
    title: str
        Graph name to be read out. Optional.

    Examples
    --------
    >>> plot([0, 1, 2])
    <IPython.core.display.HTML object>
    >>> plot(x=[0, 1, 2], y=[4, 5, 6], label=[0, 0, 1])
    <IPython.core.display.HTML object>
    """

    assert type(y) == list, "y must be list type data."

    if label:
        assert max(label) < len(__COLORS), "max label must be lower {}".format(len(__COLORS))
        assert max(label) + 1 == len(set(label)), "label should be in {} because max label is {}.".format(
                    list(range(max(label) + 1)), max(label))

    if type(y) == np.ndarray:
        y = y.tolist()

    if x == None:
        x = np.arange(len(y)).tolist()
    elif type(x) == np.ndarray:
        x = x.tolist()

    if label == None:
        label = np.zeros_like(y).astype(int).tolist()
    elif type(label) == np.ndarray:
        label = label.astype(int).tolist()

    if notebook:
        __set_context()
        output_notebook()

    p = figure(plot_width=width, plot_height=height, tools="", toolbar_location=None)

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

    if len(set(label)) > 1:
        double_tap_code = """
        oscTarget = (oscTarget + 1) %% (maxLabel + 1);
        %s
        """ % (__speak_js("`label ${oscTarget} is selected`"))
        p.js_on_event(events.DoubleTap, CustomJS(args={"maxLabel": max(label)},
                                                 code=double_tap_code))


    read_label = (max(label) > 0)
    p.js_on_event(events.MouseEnter, __speak_inout(title, True, read_label))
    p.js_on_event(events.MouseLeave, __speak_inout(title, False, read_label))

    show(p)


if __name__ == "__main__":
    plot(x=[0, 1, 2], y=[4, 5, 6], label=[0, 0, 1], notebook=False)

    from bs4 import BeautifulSoup

    HTML = """
    <button id="unmuteButton">Push here to unmute graph</button>
    <script>
      document.getElementById('unmuteButton').addEventListener('click', function() {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        audioGain = audioContext.createGain();
        panNode = audioContext.createStereoPanner();
        osc = audioContext.createOscillator();
        osc.connect(panNode);
        panNode.connect(audioGain);
        audioGain.connect(audioContext.destination);
        osc.start(audioContext.currentTime);
        audioGain.gain.setValueAtTime(0, audioContext.currentTime);
        oscTarget = 0;
      })
    </script>
    """

    html_filename = __file__.replace(".py", ".html")

    soup = BeautifulSoup(open(html_filename), 'html.parser')
    soup.body.insert(0, BeautifulSoup(HTML, "html.parser")) # after body

    with open(html_filename, "w") as file:
        file.write(str(soup))

