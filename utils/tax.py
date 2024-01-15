import pandas as pd


def tax(
    income: float, rate: float, lower: float = 0, upper: float = float("inf")
) -> float:
    """
    Calculates the tax based on the income, rate, lower and upper limit.

    Parameters:
    income (float): The income on which the tax is to be calculated.
    rate (float): The tax rate.
    lower (float, optional): The lower income limit for the tax bracket. Defaults to 0.
    upper (float, optional): The upper income limit for the tax bracket. Defaults to infinity.

    Returns:
    float: The calculated tax.
    """
    return max(0, min(upper - lower, income - lower)) * rate


def income_tax(gross_income: float) -> float:
    """
    Calculates the income tax based on the gross income.

    The tax is calculated as follows:
    - The personal allowance is initially set at 12,570.
    - If the gross income exceeds 100,000, the personal allowance is reduced by 0.5 for every pound over 100,000.
    - The tax is then calculated in three brackets:
        - Basic: 20% tax on income between the personal allowance and 50,270.
        - Higher: 40% tax on income between 50,270 and 125,140.
        - Additional: 45% tax on income over 125,140.

    Parameters:
    gross_income (float): The gross income on which the tax is to be calculated.

    Returns:
    float: The calculated tax.
    """
    personal_allowance = 12_570
    personal_allowance_reduction = 0.5 * max(0, gross_income - 100_000)
    personal_allowance = max(0, personal_allowance - personal_allowance_reduction)

    basic = tax(gross_income, 0.2, personal_allowance, 50_270)
    higher = tax(gross_income, 0.4, 50_270, 125_140)
    additional = tax(gross_income, 0.45, 125_140)
    return basic + higher + additional


def national_insurance(gross_income: float) -> float:
    """
    Calculates the national insurance based on the gross income.

    The national insurance is calculated in two brackets:
    - Basic: 12% tax on income between 12,576.12 and 50,268.
    - Reduced: 2% tax on income over 50,268.

    Parameters:
    gross_income (float): The gross income on which the national insurance is to be calculated.

    Returns:
    float: The calculated national insurance.
    """
    basic = tax(gross_income, 0.12, 12_576.12, 50_268)
    reduced = tax(gross_income, 0.02, 50_268)
    return basic + reduced


def monthly(func: callable, gross_income_monthly: pd.Series, *args: list) -> pd.Series:
    """
    Calculates the monthly tax based on the gross income and the given function.

    The function is applied on the gross income multiplied by 12 (to convert it to annual income),
    and the result is divided by 12 to get the monthly value.

    Parameters:
    func (callable): The function to be applied on the gross income.
    gross_income_monthly (pd.Series): The gross income on a monthly basis.
    *args (list): Additional arguments to be passed to the function.

    Returns:
    pd.Series: The calculated monthly tax.
    """
    return func(gross_income_monthly * 12, *args) / 12


def net_present_value(cash_flow: pd.Series, discount_rate: float = 0.05) -> pd.Series:
    """
    Calculates the net present value of a cash flow series.

    This function takes a series of cash flows and a discount rate, and returns a series of the same cash flows discounted
    to their present value. The discounting is done using the formula:

        present_value = future_value / (1 + discount_rate) ** number_of_periods

    where number_of_periods is the index of the cash flow in the series (i.e., the year).

    Parameters:
    cash_flow (pd.Series): The series of cash flows. The index of the series is assumed to represent the year.
    discount_rate (float, optional): The discount rate to be used for discounting the cash flows. Defaults to 0.05.

    Returns:
    pd.Series: The series of discounted cash flows.
    """
    discounted = cash_flow.copy()
    for i, year in enumerate(discounted.index):
        discounted[year] /= (1 + discount_rate) ** i
    return discounted
