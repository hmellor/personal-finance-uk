import inspect
import os
from datetime import date

import ipywidgets as widgets
import plotly.graph_objects as go
from ipywidgets import Widget
from plotly.subplots import make_subplots


class Inputs:
    def __init__(self):
        style = {"description_width": "22%"}
        layout = widgets.Layout(width="auto")
        slider_kwargs = dict(style=style, layout=layout, continuous_update=False)

        self.widgets = dict(
            plan=widgets.ToggleButtons(
                value=os.getenv("PLAN", "Plan 2"),
                options=["Plan 1", "Plan 2", "Plan 4", "Plan 5", "Postgraduate"],
                tooltips=[
                    "If you started your course before 1 September 2012",
                    "If you started your course between 1 September 2012 and 31 July 2023",
                    "If you applied to Student Awards Agency Scotland",
                    "If you started your course on or after 1 August 2023",
                    "If you studdied a postgraduate master's or doctoral course",
                ],
                layout=layout,
            ),
            graduation_year=widgets.IntSlider(
                description="Graduation year",
                value=int(os.getenv("GRADUATION_YEAR", date.today().year)),
                min=2000,
                max=2050,
                **slider_kwargs,
            ),
            loan=widgets.FloatSlider(
                description="Loan (£)",
                value=float(os.getenv("LOAN", 45000)),
                max=150000,
                step=100,
                **slider_kwargs,
            ),
            interest_rate=widgets.FloatSlider(
                description="Interest rate (%/year)",
                value=float(os.getenv("INTEREST_RATE", 0.071)),
                max=0.2,
                step=0.001,
                readout_format=".1%",
                **slider_kwargs,
            ),
            initial_salary=widgets.FloatSlider(
                description="Initial salary (£)",
                value=float(os.getenv("INITIAL_SALARY", 30000)),
                max=150000,
                step=100,
                **slider_kwargs,
            ),
            salary_sacrifice=widgets.FloatSlider(
                description="Salary sacrifice (%/month)",
                value=float(os.getenv("SALARY_SACRIFICE", 0.0)),
                max=0.5,
                step=0.01,
                readout_format=".0%",
                **slider_kwargs,
            ),
            salary_growth=widgets.FloatSlider(
                description="Salary growth (%/year)",
                value=float(os.getenv("SALARY_GROWTH", 0.08)),
                max=0.5,
                step=0.01,
                readout_format=".0%",
                **slider_kwargs,
            ),
            inflation_rate=widgets.FloatSlider(
                description="Inflation rate (%/year)",
                value=float(os.getenv("INFLATION_RATE", 0.04)),
                max=0.2,
                step=0.001,
                readout_format=".1%",
                **slider_kwargs,
            ),
            instant_repayment=widgets.FloatSlider(
                description="Instant repayment (£)",
                value=float(os.getenv("INSTANT_REPAYMENT", 0)),
                max=150000,
                step=10,
                readout_format=".2f",
                **slider_kwargs,
            ),
            extra_repayments=widgets.FloatSlider(
                description="Extra repayments (£/month)",
                value=float(os.getenv("EXTRA_REPAYMENTS", 0)),
                max=2000,
                step=10,
                readout_format=".2f",
                **slider_kwargs,
            ),
        )

        self.widgets["instant_repayment"].max = self.widgets["loan"].value

    def get_widgets(self, widgets: list[str]) -> dict[str, Widget]:
        return {k: v for k, v in self.widgets.items() if k in widgets}


def observe_children(widget: widgets.Widget, callback: callable) -> None:
    """
    This function recursively observes changes in the 'value' attribute of the given widget and its children.
    When a change is observed, the provided callback function is triggered.

    Args:
        widget (widgets.Widget): The widget to observe.
        callback (callable): The function to be called when the 'value' attribute of the widget or its children changes.
    """
    for child in widget.children:
        if hasattr(child, "children"):
            observe_children(child, callback)
        else:
            child.observe(callback, names="value")


class InteractiveFigure:
    def __init__(self, plot: callable, update: callable, x_title=None, y_title=None):
        self.update = update
        self.plot = plot
        self.process_kwargs = list(inspect.signature(self.update).parameters.keys())
        self.plot_kwargs = list(inspect.signature(self.plot).parameters.keys())

        # Create inputs
        kwargs = self.process_kwargs + self.plot_kwargs
        self.inputs = Inputs().get_widgets(kwargs)

        # Create figure
        self.figure = make_subplots(
            rows=1,
            cols=2,
            shared_xaxes="all",
            horizontal_spacing=0.1,
            x_title=x_title,
            y_title=y_title,
        )
        self.figure.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
        )

        # Initialise the figure
        self.on_change()

        # Create the inputs and figure widgets
        self.inputs_widget = widgets.VBox(tuple(self.inputs.values()))
        self.figure_widget = go.FigureWidget(self.figure)
        # Add callback when change in value is observed for any of the inputs
        observe_children(widget=self.inputs_widget, callback=self.on_change)

        # Package the inputs and the figure into the app
        self.app = widgets.VBox((self.inputs_widget, self.figure_widget))

    # Callback that re-runs the data processing medhot and updates plots
    def on_change(self, *args):
        # Extract kwargs from widgets
        kwargs = {k: v.value for k, v in self.inputs.items()}
        process_kwargs = {k: kwargs[k] for k in self.process_kwargs if k in kwargs}
        plot_kwargs = {k: kwargs[k] for k in self.plot_kwargs if k in kwargs}
        # Update and plot the new data
        data = self.update(**process_kwargs)
        self.plot(getattr(self, "figure_widget", self.figure), data, **plot_kwargs)
