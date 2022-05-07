import copy
import numpy as np
from bokeh import events
from bokeh.models import CustomJS, HoverTool, Slider, Div
from bokeh.plotting import figure, output_notebook, show
from bokeh.layouts import column, row
from bokeh.models import LinearAxis, Range1d
from IPython.display import HTML, display

language = "en"


def set_language(lang: str):
    """Set language

    Parameters
    ----------
    longc: str
        'ja' or 'en', default is 'en'.
    """
    global language
    assert lang in ["ja", "en"], "lang must be ja or en."
    language = lang


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
    '''))


def __speak_js(utterance):
    return """
        window.speechSynthesis.cancel();
        let msg = new SpeechSynthesisUtterance({});
        msg.lang = '{}';
        window.speechSynthesis.speak(msg);
        """.format(utterance, "ja-JP" if language == "ja" else "en-US")


def __speak_inout(title="image", enter=True, read_label=False):
    if enter:
        if language == "ja":
            inout_message = "{}に入りました".format(title)
        else:
            inout_message = "Enter {}".format(title)
    else:
        if language == "ja":
            inout_message = "{}から出ました".format(title)
        else:
            inout_message = "Leave {}".format(title)

    if read_label and enter:
        if language == "ja":
            label_message = "。ラベル ${oscTarget} を選択中。ダブルクリックで変更できます。"
        else:
            label_message = ". Label ${oscTarget} is selected. Double click to change."
    else:
        label_message = ""

    return CustomJS(code=__speak_js("`{}`".format(inout_message + label_message)))


__FIND_NEAREST_JS = """
var minX, maxX, minY, maxY;
if(multiAxes) {
  var labeledX = [];
  var labeledY = [];
  x.forEach(function(val, idx){
      if(label[idx] != oscTarget) { return; }
      labeledX.push(x[idx]);
      labeledY.push(y[idx]);
  });
  minX = Math.min(...labeledX);
  maxX = Math.max(...labeledX);
  minY = Math.min(...labeledY);
  maxY = Math.max(...labeledY);
} else {
  minX = Math.min(...x);
  maxX = Math.max(...x);
  minY = Math.min(...y);
  maxY = Math.max(...y);
}

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
        margin_x: int=1, title: str="graph", script_name: str="", slider_partitions: int=None,
        multiple_axes=False):
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
    multiple_axes: bool
        Set to True if you want each label to have a separate y-axis. Optional.

    Examples
    --------
    >>> plot([0, 1, 2])
    <IPython.core.display.HTML object>
    >>> plot(x=[0, 1, 2], y=[4, 5, 6], label=[0, 0, 1])
    <IPython.core.display.HTML object>
    """

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

    if label:
        assert max(label) < len(__COLORS), "max label must be lower {}".format(len(__COLORS))
        assert max(label) + 1 == len(set(label)), "label should be in {} because max label is {}.".format(
                    list(range(max(label) + 1)), max(label))

    if script_name == "":
        __set_context()
        output_notebook()

    plot = figure(plot_width=width, plot_height=height, tools="", toolbar_location=None)
    colors = [__COLORS[c] for c in label]

    if multiple_axes:
        assert max(label) == 1, "The number of labels must be two kinds"

        multi_axes_str = "true"
        y_ranges = {}
        for l in range(max(label)+1):
            __x = np.array(x)[np.array(label) == l].tolist()
            __y = np.array(y)[np.array(label) == l].tolist()
            __c = np.array(colors)[np.array(label) == l].tolist()
            plot.scatter(__x, __y, line_color=__c, fill_color=__c, y_range_name=str(l))
            if l == 1:
                plot.add_layout(LinearAxis(y_range_name=str(l)), 'right')
            y_ranges[str(l)] = Range1d(start=min(__y) - 1, end=max(__y) + 1)

        plot.extra_y_ranges = y_ranges

    else:
        multi_axes_str = "false"
        plot.scatter(x, y, line_color=colors, fill_color=colors)

    sound_js = """
    const multiAxes = %s;
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
    """ % (multi_axes_str, __FIND_NEAREST_JS, gain)

    # Mouse hover on plot
    hover_code = """
    let marginX = %s;
    let position = cb_data.geometry.x;
    %s
    """ % (margin_x, sound_js)

    callback = CustomJS(args={"x": x, "y": y, "label": label}, code=hover_code)
    plot.add_tools(HoverTool(tooltips=None, callback=callback))

    # Single tap on plot
    if language == "ja":
        utterance = "`エックスは${nearestX}。ワイは${nearestY}`"
    else:
        utterance = "`X is ${nearestX}. Y is ${nearestY}`"

    tap_code = """
    let position = cb_obj.x;
    const multiAxes = %s;
    %s
    %s
    """ % (multi_axes_str, __FIND_NEAREST_JS, __speak_js(utterance))

    plot.js_on_event(events.Tap, CustomJS(args={"x": x, "y": y, "label": label},
                                       code=tap_code))

    if len(set(label)) > 1:
        # Double tap on plot
        if language == "ja":
            utterance = "`ラベル ${oscTarget} が選択されています。`"
        else:
            utterance = "`label ${oscTarget} is selected`"

        double_tap_code = """
        oscTarget = (oscTarget + 1) %% (maxLabel + 1);
        %s
        """ % (__speak_js(utterance))
        plot.js_on_event(events.DoubleTap, CustomJS(args={"maxLabel": max(label)},
                                                 code=double_tap_code))

    # Enter or leave on plot
    read_label = (max(label) > 0)
    plot.js_on_event(events.MouseEnter, __speak_inout(title, True, read_label))
    plot.js_on_event(events.MouseLeave, __speak_inout(title, False, read_label))

    # slider for keyboard interaction
    sliders = []
    for l in range(max(label)+1):
        __x = np.array(x)[np.array(label) == l].tolist()

        if slider_partitions is None:
            slider_partitions = np.min([len(__x)-1, 30])
            if slider_partitions == 30:
                if language == "ja":
                    print("30個以上のデータがあるため、それ以上の細かさが省略されています。"\
                          "もっと細かく分割するためにはslider_partitionsの引数の値を大きくしてください。")
                else:
                    print("The number of slider partitions has been reduced to 30 as the default limit. "\
                          "Please set slider_partitions as an argument if necessary.")

        slider_start = np.min(__x)
        slider_end = np.max(__x)
        if slider_start == slider_end:
            slider_end += 1
        slider_step = (slider_end - slider_start) / slider_partitions

        if language == "ja":
            utterance = "`エックスは${nearestX}。ワイは${nearestY}`"
        else:
            utterance = "`X is ${nearestX}. Y is ${nearestY}`"

        slider_code = """
        oscTarget = target;
        let marginX = %s;
        let position = slider.value;
        %s
        setTimeout(function(){%s}, 3000);
        """ % (slider_step, sound_js, __speak_js(utterance))

        slider = Slider(start=slider_start, end=slider_end, value=slider_start, step=slider_step,
                    title="{} {}".format("ラベル" if language == "ja" else "en", l))
        slider.js_on_change('value', CustomJS(args={"x": x, "y": y, "label": label, "slider": slider, "target": l}, code=slider_code))
        sliders.append(slider)

    # layout
    if language == "ja":
        message1 = Div(text="<h2>音声グラフ</h2>")
        message2 = Div(text="<p>ここにはグラフとスライダーが配置されています。"\
            "マウスをもっているのであれば、グラフ上をなぞることにより、グラフ上の値を音声で確認することができます。"\
            "マウスをもっていない場合でも、スライダーを動かすことにより、値を確認することができます。</p>")
    else:
        message1 = Div(text="<h2>output of audio plot lib</h2>")
        message2 = Div(text="<p>There is a graph and a series of sliders to check the values. "\
            "If you have a mouse, you can check the values by hovering over the graph. "\
            "If you are using only a keyboard, you can move the slider to move the horizontal axis "\
            "of the graph to check the value of the graph as a pitch according to the location.</p>")
    show(column(message1, message2, row(plot, column(sliders))))

    if script_name != "":
        from bs4 import BeautifulSoup

        if language == "ja":
            button = "<button id=\"unmuteButton\">このボタンを押して音声再生を有効化してください</button>"
        else:
            button = "<button id=\"unmuteButton\">Push here to unmute graph</button>"

        script = """
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
        soup.body.insert(0, BeautifulSoup(button + script, "html.parser")) # after body

        with open(html_filename, "w") as file:
            file.write(str(soup))

