import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.apply_dark_theme()

    def apply_dark_theme(self):
        # Charcoal grey color (matches WHITE token in styles.py)
        bg_color = "#1e1e1e"
        text_color = "#d4d4d8"   # grey-300
        border_color = "#2c2c2c" # border grey
        
        self.fig.patch.set_facecolor(bg_color)
        self.axes.set_facecolor(bg_color)
        
        self.axes.xaxis.label.set_color(text_color)
        self.axes.yaxis.label.set_color(text_color)
        self.axes.title.set_color("#f8fafc")  # slate-50
        
        self.axes.tick_params(colors=text_color, which="both")
        
        for spine in self.axes.spines.values():
            spine.set_color(border_color)

    def clear(self):
        self.axes.clear()
        self.apply_dark_theme()
