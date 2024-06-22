from calendar import isleap, monthrange
from datetime import date

import numpy as np
import pandas as pd

from utils.tax import income_tax, monthly, national_insurance, tax

PLANS = {
    "Plan 1": {"threshold": 22_015, "percentage": 0.09},
    "Plan 2": {"threshold": 27_295, "percentage": 0.09},
    "Plan 4": {"threshold": 27_660, "percentage": 0.09},
    "Plan 5": {"threshold": 25_000, "percentage": 0.09},
    "Postgraduate": {"threshold": 21_000, "percentage": 0.06},
}


def student_loan_repayment(gross_income: float, plan: str):
    """
    Calculates the student loan repayment amount based on the provided income and repayment plan.

    Parameters:
    gross_income (float): The gross income of the student.
    plan (str): The repayment plan of the student. It must be one of the following: "Plan 1", "Plan 2", "Plan 4", "Plan 5", "Postgraduate".

    Returns:
    float: The loan repayment amount.

    Raises:
    AssertionError: If the provided plan does not exist in the predetermined plans.
    """
    assert plan in PLANS, f"`plan` must be one of: {list(PLANS.keys())}"
    return tax(gross_income, PLANS[plan]["percentage"], PLANS[plan]["threshold"])


def simulate_repayment(
    initial_salary: float,
    salary_growth: float,
    loan: float,
    graduation_year: int,
    interest_rate: float,
    salary_sacrifice: float,
    plan: str = "Plan 2",
    instant_repayment: float = None,
    extra_repayments: float | dict[int:float] = None,
) -> pd.DataFrame:
    """
    Simulates the repayment of a student loan.

    Parameters:
    initial_salary (float): The initial salary of the student.
    salary_growth (float): The annual growth rate of the salary.
    loan (float): The initial amount of the loan.
    graduation_year (int): The year of graduation.
    interest_rate (float): The annual interest rate of the loan.
    salary_sacrifice (float): The proportion of the salary to be sacrificed to things such as pension contributions.
    plan (str): The repayment plan. Default is "Plan 2".
    instant_repayment (float): Additional repayment to be made immediately.
    extra_repayments (float | dict[int:float]): Additional repayments to be made. Can be a constant amount (float) or a dictionary mapping from month number to repayment amount.

    Returns:
    pandas.DataFrame: A dataframe containing the simulation results. The columns are:
        - "gross": Gross monthly income.
        - "net": Net monthly income after tax and loan repayments.
        - "loan": Remaining loan balance.
        - "interest": Interest accrued in the current month.
        - "salary repayment": Repayment amount from the salary in the current month.
        - "extra repayment": Additional repayment amount in the current month.
    """
    start_date = date.today()
    end_date = date(graduation_year + 31, 4, 1)
    periods = pd.date_range(start=start_date, end=end_date, freq="m")

    num_preiods = len(periods)
    columns = [
        "gross",
        "net",
        "loan",
        "interest",
        "salary repayment",
        "extra repayment",
    ]

    data = {
        "active": np.zeros((num_preiods, len(columns))),
        "passive": np.zeros((num_preiods, len(columns))),
    }

    for mode in data:
        # Initial gross monthly income
        data[mode][0, 0] = initial_salary / 12
        # Initial loan amount
        data[mode][0, 2] = loan

    if instant_repayment:
        data["active"][0, 2] -= min(instant_repayment, loan)

    if extra_repayments:
        if isinstance(extra_repayments, float):
            data["active"][:, 5] = extra_repayments
        else:
            for k, v in extra_repayments.items():
                if k < num_preiods:
                    data["active"][k, 5] = v

    def calculate_monthly_interest(current_loan, current_period):
        days_in_month = monthrange(current_period.year, current_period.month)[1]
        days_in_year = 365 + isleap(current_period.year)
        monthly_interest_rate = (1 + interest_rate) ** (
            days_in_month / days_in_year
        ) - 1
        return current_loan * monthly_interest_rate

    for i in range(1, num_preiods):
        current_period = periods[i - 1]

        for mode in data:
            # Gross income growth and adjustment for salary sacrifice
            data[mode][i, 0] = data[mode][i - 1, 0]
            if current_period.month == 12:
                data[mode][i, 0] *= 1 + salary_growth
            gross = data[mode][i, 0] * (1 - salary_sacrifice)

            # Interest calculation and loan update
            if data[mode][i - 1, 2] >= 0:
                data[mode][i - 1, 3] = calculate_monthly_interest(
                    data[mode][i - 1, 2], current_period
                )
                data[mode][i, 2] = data[mode][i - 1, 2] + data[mode][i - 1, 3]

                # Salary repayment
                data[mode][i - 1, 4] = monthly(student_loan_repayment, gross, plan)
                data[mode][i, 2] -= data[mode][i - 1, 4]

                if data[mode][i, 2] < 0:
                    data[mode][i - 1, 4] += data[mode][i, 2]
                    data[mode][i - 1 :, 5] = 0
                    data[mode][i, 2] = 0

                # Extra repayment
                if mode == "active":
                    data[mode][i, 2] -= data[mode][i - 1, 5]
                    if data[mode][i, 2] < 0:
                        data[mode][i - 1, 5] += data[mode][i, 2]
                        data[mode][i:, 5] = 0
                        data[mode][i, 2] = 0

            # Net income after tax and repayments
            data[mode][i - 1, 1] = (
                gross - monthly(income_tax, gross) - monthly(national_insurance, gross)
            ) - (data[mode][i - 1, 4] + data[mode][i - 1, 5])

    df_active = pd.DataFrame(data["active"], index=periods, columns=columns)
    df_passive = pd.DataFrame(data["passive"], index=periods, columns=columns)

    # Merge the passive and active data
    df = pd.merge(
        left=df_passive,
        right=df_active,
        how="outer",
        left_index=True,
        right_index=True,
        suffixes=(" passive", " active"),
    )

    # Trim the dataframe to only include periods where the loan is being repaid
    if df["loan passive"].iloc[-1] == 0:
        df = df[: df["loan passive"].argmin() + 1]
    return df
