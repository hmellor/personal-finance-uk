import os
from datetime import date

import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd

from utils.tax import net_present_value

plt.ioff()

style = {"description_width": "20%"}
layout = widgets.Layout(width="auto")


plan = widgets.ToggleButtons(
    description="Repayment plan",
    style=style,
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

graduation_year = widgets.IntSlider(
    description="Graduation year",
    style=style,
    value=int(os.getenv("GRADUATION_YEAR", date.today().year)),
    min=2000,
    max=2050,
    continuous_update=False,
    layout=layout,
)

loan = widgets.FloatSlider(
    description="Loan (£)",
    style=style,
    value=float(os.getenv("LOAN", 45000)),
    max=150000,
    step=100,
    continuous_update=False,
    layout=layout,
)

interest_rate = widgets.FloatSlider(
    description="Interest rate (%/year)",
    style=style,
    value=float(os.getenv("INTEREST_RATE", 0.071)),
    max=0.2,
    step=0.001,
    continuous_update=False,
    readout_format=".1%",
    layout=layout,
)

initial_salary = widgets.FloatSlider(
    description="Initial salary (£)",
    style=style,
    value=float(os.getenv("INITIAL_SALARY", 30000)),
    max=150000,
    step=100,
    continuous_update=False,
    layout=layout,
)

salary_sacrifice = widgets.FloatSlider(
    description="Salary sacrifice (%/month)",
    style=style,
    value=float(os.getenv("SALARY_SACRIFICE", 0.0)),
    max=0.5,
    step=0.01,
    continuous_update=False,
    readout_format=".0%",
    layout=layout,
)

salary_growth = widgets.FloatSlider(
    description="Salary growth (%/year)",
    style=style,
    value=float(os.getenv("SALARY_GROWTH", 0.08)),
    max=0.5,
    step=0.01,
    continuous_update=False,
    readout_format=".0%",
    layout=layout,
)

inflation_rate = widgets.FloatSlider(
    description="Inflation rate (%/year)",
    style=style,
    value=float(os.getenv("INFLATION_RATE", 0.04)),
    max=0.2,
    step=0.001,
    continuous_update=False,
    readout_format=".1%",
    layout=layout,
)

extra_repayments = widgets.FloatSlider(
    description="Extra repayments (£/month)",
    style=style,
    value=0,
    max=2000,
    step=10,
    continuous_update=False,
    readout_format=".2f",
    layout=layout,
)

inputs = {
    "plan": plan,
    "graduation_year": graduation_year,
    "loan": loan,
    "interest_rate": interest_rate,
    "inflation_rate": inflation_rate,
    "initial_salary": initial_salary,
    "salary_sacrifice": salary_sacrifice,
    "salary_growth": salary_growth,
    "extra_repayments": extra_repayments,
}


def get_plot(width: int = 800):
    px = 1 / plt.rcParams["figure.dpi"]
    plt.rcParams["axes.grid"] = True
    fig, axes = plt.subplots(1, 2, figsize=(width * px, width / 2 * px))
    fig.canvas.header_visible = False
    return fig, axes


def plot_update(
    fig,
    ax0,
    ax1,
    data: pd.DataFrame,
    inflation_rate: float = 0.05,
):
    # Remove anything that's currently on the axes
    ax0.clear()
    ax1.clear()
    # Plot lines
    data[["gross", "net", "loan"]].divide(1000).plot(ax=ax0)
    data[["interest", "salary repayment", "extra repayment"]].plot(ax=ax1)
    fig.supxlabel("Years")
    ax0.set_ylabel("Income (£k)")
    ax0.set_ylim(0)
    ax1.set_ylabel("Payments (£)")
    ax1.set_ylim(0)
    # Create title
    final_loan_npv = net_present_value(data["loan"], discount_rate=inflation_rate / 12)[
        -1
    ]
    monthly_repayments = data[["salary repayment", "extra repayment"]].sum("columns")
    annual_repayments = monthly_repayments.groupby(data.index.year).sum()
    total_repayment_npv = net_present_value(
        annual_repayments, discount_rate=inflation_rate
    ).sum()
    suptitle = f"Outstanding balance NPV: £{final_loan_npv:,.2f}, Repayment months: {len(data)}, Repayment NPV: £{total_repayment_npv:,.2f}"
    plt.suptitle(suptitle)
    plt.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()
    return fig, ax0, ax1


def plot(
    data: pd.DataFrame,
    inflation_rate: float = 0.05,
    title: str = "",
):
    fig, (ax0, ax1) = get_plot(800)
    return plot_update(fig, ax0, ax1, data, inflation_rate, title)
