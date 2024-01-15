import os
from datetime import date

import ipywidgets as widgets
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.tax import net_present_value


def create_inputs():
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


def create_figure():
    fig = make_subplots(
        rows=1,
        cols=2,
        shared_xaxes="all",
        horizontal_spacing=0.1,
        # vertical_spacing=0,
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


def observe_children(widget, callback):
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
