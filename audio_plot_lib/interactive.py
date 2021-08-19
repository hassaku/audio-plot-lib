import copy
import numpy as np
from bokeh import events
from bokeh.models import CustomJS, HoverTool, Slider, Div
from bokeh.plotting import figure, output_notebook, show
from bokeh.layouts import column, row
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
    return """
        window.speechSynthesis.cancel();
        let msg = new SpeechSynthesisUtterance({});
        msg.lang = "en-US";
        window.speechSynthesis.speak(msg);
        """.format(utterance)


def __speak_inout(title="image", enter=True, read_label=False):
    if read_label and enter:
        label_message = ". Label ${oscTarget} is selected. Double click to change."
    else:
        label_message = ""


    if enter:
        inout_message = "Enter {}".format(title)

    else:
        inout_message = "Leave {}".format(title)

    return CustomJS(code=__speak_js("`{}`".format(inout_message + label_message)))


__FIND_NEAREST_JS = """
let minX = Math.min(...x);
let maxX = Math.max(...x);
let minY = Math.min(...y);
let maxY = Math.max(...y);

if((position == Infinity) || (position < minX) || (position > maxX)) {
    return;
}

var diff = [];
var nearestIdx = 0;
x.forEach(function(val, idx){
    if(label[idx] != oscTarget) {
        return;
    }
    diff[idx] = Math.abs(position - val);
    nearestIdx = (diff[nearestIdx] < diff[idx]) ? nearestIdx : idx;
});

let nearestX = x[nearestIdx];
let nearestY = y[nearestIdx];
"""


__COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
        '#bcbd22', '#17becf']


def plot(y: list, x: list=None, label: list=None, width: int=400, height: int=400, gain: float=0.4,
        margin_x: int=1, title: str="graph", script_name: str="", slider_partitions: int=None):
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

    if label:
        assert max(label) < len(__COLORS), "max label must be lower {}".format(len(__COLORS))
        assert max(label) + 1 == len(set(label)), "label should be in {} because max label is {}.".format(
                    list(range(max(label) + 1)), max(label))

    if type(y) == np.ndarray:
        y = y.tolist()

    if type(x) == np.ndarray:
        x = x.tolist()
    elif x == None:
        x = np.arange(len(y)).tolist()

    if type(label) == np.ndarray:
        label = label.astype(int).tolist()
    elif label == None:
        label = np.zeros_like(y).astype(int).tolist()

    if script_name == "":
        __set_context()
        output_notebook()

    plot = figure(plot_width=width, plot_height=height, tools="", toolbar_location=None)

    colors = [__COLORS[c] for c in label]
    plot.scatter(x, y, line_color=colors, fill_color=colors)

    sound_js = """
    %s
    if(diff[nearestIdx] > marginX) {
        return;
    }

    const gain = %s; // max: 1.0
    osc.type = 'triangle'; // sine, square, sawtooth, triangle
    osc.frequency.value = 261.626 + (nearestY - minY) / (maxY - minY) * 261.626 // Hz
    audioGain.gain.linearRampToValueAtTime(gain, audioContext.currentTime + 0.2); // atack
    audioGain.gain.setTargetAtTime(0, audioContext.currentTime + 0.2, 0.5); // decay, sustain

    let pan = (nearestX - minX) / (maxX - minX) * 2 - 1;
    panNode.pan.value = pan;  // left:-1 ~ right:1
    """ % (__FIND_NEAREST_JS, gain)

    # Mouse hover on plot
    hover_code = """
    let marginX = %s;
    let position = cb_data.geometry.x;
    %s
    """ % (margin_x, sound_js)

    callback = CustomJS(args={"x": x, "y": y, "label": label}, code=hover_code)
    plot.add_tools(HoverTool(tooltips=None, callback=callback))

    # Single tap on plot
    tap_code = """
    let position = cb_obj.x;
    %s
    %s
    """ % (__FIND_NEAREST_JS, __speak_js("`X is ${nearestX}. Y is ${nearestY}`"))

    plot.js_on_event(events.Tap, CustomJS(args={"x": x, "y": y, "label": label},
                                       code=tap_code))

    if len(set(label)) > 1:
        # Double tap on plot
        double_tap_code = """
        oscTarget = (oscTarget + 1) %% (maxLabel + 1);
        %s
        """ % (__speak_js("`label ${oscTarget} is selected`"))
        plot.js_on_event(events.DoubleTap, CustomJS(args={"maxLabel": max(label)},
                                                 code=double_tap_code))

    # Enter or leave on plot
    read_label = (max(label) > 0)
    plot.js_on_event(events.MouseEnter, __speak_inout(title, True, read_label))
    plot.js_on_event(events.MouseLeave, __speak_inout(title, False, read_label))

    # slider for keyboard interaction
    slider_code = """
    oscTarget = target;
    let marginX = %s;
    let position = slider.value;
    %s
    setTimeout(function(){%s}, 3000);
    """ % (margin_x, sound_js, __speak_js("`X is ${nearestX}. Y is ${nearestY}`"))

    if slider_partitions is None:
        slider_partitions = np.min([len(x)-1, 30])

    slider_start = np.min(x)
    slider_end = np.max(x)
    if slider_start == slider_end:
        slider_end += 1
    slider_step = (slider_end - slider_start) / slider_partitions

    sliders = []
    for l in range(max(label)+1):
        slider = Slider(start=slider_start, end=slider_end, value=slider_start, step=slider_step, title="label %d" % (l+1))
        slider.js_on_change('value', CustomJS(args={"x": x, "y": y, "label": label, "slider": slider, "target": l}, code=slider_code))
        sliders.append(slider)

    # layout
    message1 = Div(text="""<h2>output of audio plot lib</h2>""")
    message2 = Div(text="""<p>There is a graph and a series of sliders to check the values. If you have a mouse, you can check the values by hovering over the graph. If you are using only a keyboard, you can move the slider to move the horizontal axis of the graph to check the value of the graph as a pitch according to the location.</p>""")
    show(column(message1, message2, row(plot, column(sliders))))

    if script_name != "":
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

        html_filename = script_name.replace(".py", ".html")
        soup = BeautifulSoup(open(html_filename), 'html.parser')
        soup.body.insert(0, BeautifulSoup(HTML, "html.parser")) # after body

        with open(html_filename, "w") as file:
            file.write(str(soup))

