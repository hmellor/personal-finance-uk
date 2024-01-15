import os
from datetime import date

import ipywidgets as widgets
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs._figure import Figure
from plotly.subplots import make_subplots

from utils.tax import net_present_value


def create_inputs() -> dict[str, widgets.Widget]:
    """
    This function creates and returns a dictionary of widgets that will be used to get user inputs for the calculation.
    The widgets created include ToggleButtons, IntSlider, and FloatSlider, each representing different parameters needed for the calculation.

    Returns:
        dict: A dictionary of widgets for user inputs.
    """
    inputs = {}
    style = {"description_width": "22%"}
    layout = widgets.Layout(width="auto")
    slider_kwargs = dict(style=style, layout=layout, continuous_update=False)

    inputs["plan"] = widgets.ToggleButtons(
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
    )

    inputs["graduation_year"] = widgets.IntSlider(
        description="Graduation year",
        value=int(os.getenv("GRADUATION_YEAR", date.today().year)),
        min=2000,
        max=2050,
        **slider_kwargs,
    )

    inputs["loan"] = widgets.FloatSlider(
        description="Loan (£)",
        value=float(os.getenv("LOAN", 45000)),
        max=150000,
        step=100,
        **slider_kwargs,
    )

    inputs["interest_rate"] = widgets.FloatSlider(
        description="Interest rate (%/year)",
        value=float(os.getenv("INTEREST_RATE", 0.071)),
        max=0.2,
        step=0.001,
        readout_format=".1%",
        **slider_kwargs,
    )

    inputs["initial_salary"] = widgets.FloatSlider(
        description="Initial salary (£)",
        value=float(os.getenv("INITIAL_SALARY", 30000)),
        max=150000,
        step=100,
        **slider_kwargs,
    )

    inputs["salary_sacrifice"] = widgets.FloatSlider(
        description="Salary sacrifice (%/month)",
        value=float(os.getenv("SALARY_SACRIFICE", 0.0)),
        max=0.5,
        step=0.01,
        readout_format=".0%",
        **slider_kwargs,
    )

    inputs["salary_growth"] = widgets.FloatSlider(
        description="Salary growth (%/year)",
        value=float(os.getenv("SALARY_GROWTH", 0.08)),
        max=0.5,
        step=0.01,
        readout_format=".0%",
        **slider_kwargs,
    )

    inputs["inflation_rate"] = widgets.FloatSlider(
        description="Inflation rate (%/year)",
        value=float(os.getenv("INFLATION_RATE", 0.04)),
        max=0.2,
        step=0.001,
        readout_format=".1%",
        **slider_kwargs,
    )

    inputs["extra_repayments"] = widgets.FloatSlider(
        description="Extra repayments (£/month)",
        value=float(os.getenv("EXTRA_REPAYMENTS", 0)),
        max=2000,
        step=10,
        readout_format=".2f",
        **slider_kwargs,
    )

    return inputs


def create_figure() -> Figure:
    """
    This function creates a subplot figure with two columns using the Plotly library. Both plots share the same x-axis.
    The x-axis represents the date and the y-axis represents the amount in pounds. The function also sets the layout
    and updates the y-axis properties.

    Returns:
        fig: A Plotly figure with two subplots.
    """
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_xaxes="all",
        horizontal_spacing=0.1,
        x_title="Date",
        y_title="Amount (£)",
    )
    fig.update_layout(
        margin=dict(l=60, r=20, t=80, b=60),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
    )
    fig.update_yaxes(tickprefix="£", nticks=10, rangemode="nonnegative")
    return fig


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


def plot(
    fig: go.FigureWidget,
    data: pd.DataFrame,
    inflation_rate: float = 0.05,
):
    """
    This function plots the loan repayment data on a Plotly figure widget.

    Args:
        fig (go.FigureWidget): The Plotly figure widget to plot the data on.
        data (pd.DataFrame): The data to plot. The DataFrame should have columns for the loan, salary repayment, and extra repayment.
        inflation_rate (float, optional): The inflation rate to use for calculating the net present value. Defaults to 0.05.

    The function first calculates the net present value of the final loan and the total repayment. It then creates a title text
    for the plot with these values. Afterward, it plots the data on the figure widget. If the figure already has data, the function
    updates the existing data with the new data. Finally, it updates the title of the figure.
    """
    # Create title
    final_loan_npv = net_present_value(data["loan"], discount_rate=inflation_rate / 12)[
        -1
    ]
    monthly_repayments = data[["salary repayment", "extra repayment"]].sum("columns")
    annual_repayments = monthly_repayments.groupby(data.index.year).sum()
    total_repayment_npv = net_present_value(
        annual_repayments, discount_rate=inflation_rate
    ).sum()
    title_text = f"Outstanding balance NPV: £{final_loan_npv:,.2f}, Repayment months: {len(data)}, Repayment NPV: £{total_repayment_npv:,.2f}"

    # Plot lines
    lines = px.line(data, x=data.index, y=data.columns)
    with fig.batch_update():
        # Add/update data
        if not fig.data:
            fig.add_traces(lines.data, rows=[1, 1, 1, 1, 1, 1], cols=[1, 1, 1, 2, 2, 2])
        else:
            for old_data, new_data in zip(fig.data, lines.data):
                old_data.x = new_data.x
                old_data.y = new_data.y
        # Update title
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
            )
        )
