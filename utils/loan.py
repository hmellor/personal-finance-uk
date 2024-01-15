from calendar import isleap, monthrange
from datetime import date

import pandas as pd

from utils.tax import income_tax, monthly, national_insurance, tax

plans = {
    "Plan 1": {"threshold": 22_015, "percentage": 0.09},
    "Plan 2": {"threshold": 27_295, "percentage": 0.09},
    "Plan 4": {"threshold": 27_660, "percentage": 0.09},
    "Plan 5": {"threshold": 25_000, "percentage": 0.09},
    "Postgraduate": {"threshold": 21_000, "percentage": 0.06},
}


def student_loan_repayment(gross_income: float, plan: str):
    assert plan in plans, f"`plan` must be one of: {list(plans.keys())}"
    return tax(gross_income, plans[plan]["percentage"], plans[plan]["threshold"])


def simulate_repayment(
    initial_salary: float,
    salary_growth: float,
    loan: float,
    graduation_year: int,
    interest_rate,
    salary_sacrifice: float,
    plan: str = "Plan 2",
    extra_repayments: float | dict[int:float] = None,
):
    # Create empty monthly dataframe
    today = date.today()
    repayment_end = date(graduation_year + 31, 4, 1)
    data = pd.DataFrame(
        0,
        index=pd.date_range(today, repayment_end, freq="m"),
        columns=[
            "gross",
            "net",
            "loan",
            "interest",
            "salary repayment",
            "extra repayment",
        ],
    )

    # Populate initial values
    data.loc[data.index[0], ["gross", "loan"]] = [initial_salary / 12, loan]

    # Parse monthly payment dictionary
    if extra_repayments:
        if isinstance(extra_repayments, float):
            data["extra repayment"] = extra_repayments
        else:
            for k, v in extra_repayments.items():
                if k < len(data.index):
                    data.loc[data.index[k], "extra repayment"] = v

    # Simulate monthly income, interest and repayments
    for i, current_period in enumerate(data.index[:-1]):
        # Adjust gross by salary sacrifice
        gross = data.loc[current_period, "gross"] * (1 - salary_sacrifice)

        # Populate next month's gross income
        next_period = data.index[i + 1]
        data.loc[next_period, "gross"] = data.gross.iloc[i]
        if current_period.month == 12:
            data.loc[next_period, "gross"] *= 1 + salary_growth

        # Apply repayments
        if data.loc[current_period, "loan"] > 0:
            # Calculate interest accrued this month and add it to next month's loan balance
            days_in_month = monthrange(current_period.year, current_period.month)[1]
            days_in_year = 365 + isleap(current_period.year)
            monthly_interest_rate = (1 + interest_rate) ** (
                days_in_month / days_in_year
            ) - 1
            data.loc[current_period, "interest"] = (
                data.loc[current_period, "loan"] * monthly_interest_rate
            )
            data.loc[next_period, "loan"] = (
                data.loc[current_period, "loan"] + data.loc[current_period, "interest"]
            )
            # Apply salary repayment
            data.loc[current_period, "salary repayment"] = monthly(
                student_loan_repayment, gross, plan
            )
            data.loc[next_period, "loan"] -= data.loc[
                current_period, "salary repayment"
            ]
            # If loan has been paid off, zero the appropriate columns
            if data.loc[next_period, "loan"] < 0:
                data.loc[current_period, "salary repayment"] += data.loc[
                    next_period, "loan"
                ]
                data.loc[current_period:, "extra repayment"] = 0
                data.loc[next_period, "loan"] = 0
            if data.loc[next_period, "loan"] > 0:
                # Apply extra repayment
                data.loc[next_period, "loan"] -= data.loc[
                    current_period, "extra repayment"
                ]
                # If loan has been paid off, zero the appropriate columns
                if data.loc[next_period, "loan"] < 0:
                    data.loc[current_period, "extra repayment"] += data.loc[
                        next_period, "loan"
                    ]
                    data.loc[next_period:, "extra repayment"] = 0
                    data.loc[next_period, "loan"] = 0

        # Calculate current month's net income after tax and loan repayments
        data.loc[current_period, "net"] = (
            gross - monthly(income_tax, gross) - monthly(national_insurance, gross)
        )
        data.loc[current_period, "net"] -= data.loc[
            current_period, ["salary repayment", "extra repayment"]
        ].sum()

    # Crop to only include time where the loan is being paid
    if data.loan[-1] == 0:
        data = data[: data.loan.argmin() + 1]
    return data
