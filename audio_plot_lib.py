from bokeh import events
from bokeh.io import output_file, show
from bokeh.layouts import column, row
from bokeh.models import Button, CustomJS, Div, CustomJSHover, HoverTool
from bokeh.plotting import figure, output_notebook, show
from IPython.display import HTML, display


def setup():
	def set_context():
	  display(HTML('''
	  <script>
		context = new (window.AudioContext || window.webkitAudioContext)();
	  </script>
	  '''))

	output_notebook()
	get_ipython().events.register('pre_run_cell', set_context)


def speak_enter():
    return CustomJS(code="""
        var msg = new SpeechSynthesisUtterance('Enter image');
        window.speechSynthesis.speak(msg);
        """)


def speak_leave():
    return CustomJS(code="""
        var msg = new SpeechSynthesisUtterance('Leave image');
        window.speechSynthesis.speak(msg);
        """)


def scatter(x, y):
	p = figure(tools="pan,wheel_zoom,zoom_in,zoom_out,reset")

	radius = np.random.random(size=len(x)) * 1.5
	p.scatter(x, y, radius=radius, fill_alpha=0.6, line_color=None)

	code = """
	var indices = cb_data.index.indices;

	if(indices.length != 0) {
		var ind = x[indices[0]];

		var osc = context.createOscillator(); // instantiate an oscillator
		osc.type = 'sine'; // this is the default - also square, sawtooth, triangle
		//osc.frequency.value = 440; // Hz
		osc.frequency.value = 440 + ind / 5; // Hz
		osc.connect(context.destination); // connect it to the destination

		//console.log(osc.frequency.value)
		osc.start(); // start the oscillator
		osc.stop(context.currentTime + 0.1); // stop X seconds after the current time
	}
	"""
	callback = CustomJS(args={"x": x, "y": y}, code=code)
	p.add_tools(HoverTool(tooltips=None, callback=callback))

	p.js_on_event(events.MouseEnter, speak_enter())
	p.js_on_event(events.MouseLeave, speak_leave())

	output_file("js_events.html", title="JS Events Example")
	show(p)

