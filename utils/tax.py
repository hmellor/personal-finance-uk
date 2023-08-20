import pandas as pd


def tax(
    income: float, rate: float, lower: float = 0, upper: float = float("inf")
) -> float:
    return max(0, min(upper - lower, income - lower)) * rate


def income_tax(gross_income: float):
    personal_allowance = 12_570
    personal_allowance_reduction = 0.5 * max(0, gross_income - 100_000)
    personal_allowance = max(0, personal_allowance - personal_allowance_reduction)

    basic = tax(gross_income, 0.2, personal_allowance, 50_270)
    higher = tax(gross_income, 0.4, 50_270, 125_140)
    additional = tax(gross_income, 0.45, 125_140)
    return basic + higher + additional


def national_insurance(gross_income: float):
    basic = tax(gross_income, 0.12, 12_576.12, 50_268)
    reduced = tax(gross_income, 0.02, 50_268)
    return basic + reduced


def monthly(func, gross_income_monthly, *args):
    return func(gross_income_monthly * 12, *args) / 12


def net_present_value(cash_flow: pd.Series, discount_rate: float = 0.05) -> pd.Series:
    discounted = cash_flow.copy()
    for i, year in enumerate(discounted.index):
        discounted[year] /= (1 + discount_rate) ** i
    return discounted
