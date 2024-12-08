import argparse
import csv
import json
import urllib.request
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

from datetime import datetime

import pandas as pd
from dateutil.relativedelta import relativedelta
from jinja2 import Environment, FileSystemLoader
from minify_html import minify_html

from secret import API_KEY

API_URL = "https://financialmodelingprep.com/api"
METRICS = {
    "roa": {
        "name": "ROA",
        "type": "percent",
    },
    "roe": {
        "name": "ROE",
        "type": "percent",
    },
    "asset_turnover": {
        "name": "Asset turnover",
        "type": "percent",
    },
    "profit_margin": {
        "name": "Profit margin",
        "type": "decimal",
    },
    "equity_multiplier": {
        "name": "Equity multiplier",
        "type": "decimal",
    },
    "roe_market_cap": {
        "name": "ROE (market cap)",
        "type": "percent",
    },
    "current_assets_share": {
        "name": "Share of current assets",
        "type": "percent",
    },
    "non_current_assets_share": {
        "name": "Share of non-current assets",
        "type": "percent",
    },
    "equity_share": {
        "name": "Share of equity",
        "type": "percent",
    },
    "liabilities_share": {
        "name": "Share of liabilities",
        "type": "percent",
    },
    "liquidity": {
        "name": "Liquidity",
        "type": "decimal",
    },
    "solvency": {
        "name": "Solvency",
        "type": "decimal",
    },
    "p_e": {
        "name": "P/E",
        "type": "decimal",
    },
    "p_s": {
        "name": "P/S",
        "type": "decimal",
    },
    "p_b": {
        "name": "P/B",
        "type": "decimal",
    },
}


# API
def get_income_statements(symbol):
    with urllib.request.urlopen(
            f"{API_URL}/v3/income-statement/{symbol}?period=annual&apikey={API_KEY}") as income_statements_url:
        income_statements_response = json.load(income_statements_url)
        income_statements_response = sorted(income_statements_response, key=lambda d: d["date"])
        return income_statements_response


def get_balance_sheet_statements(symbol):
    with urllib.request.urlopen(
            f"{API_URL}/v3/balance-sheet-statement/{symbol}?period=annual&apikey={API_KEY}") as balance_sheet_statements_url:
        balance_sheet_statements_response = json.load(balance_sheet_statements_url)
        balance_sheet_statements_response = sorted(balance_sheet_statements_response, key=lambda d: d["date"])
        return balance_sheet_statements_response


def get_market_caps(symbol, end):
    with urllib.request.urlopen(
            f"{API_URL}/v3/historical-market-capitalization/{symbol}?to={end}&apikey={API_KEY}") as market_caps_url:
        market_caps_response = json.load(market_caps_url)
        market_caps_response = sorted(market_caps_response, key=lambda d: d["date"])
        return market_caps_response


def compute_metric(metric, income_statement, balance_sheet_statement, market_cap):
    book_value = balance_sheet_statement["totalAssets"] - balance_sheet_statement["goodwillAndIntangibleAssets"] - \
                 balance_sheet_statement["totalLiabilities"]

    match metric:
        case "roa":
            return income_statement["netIncome"] / balance_sheet_statement["totalAssets"]
        case "roe":
            return income_statement["netIncome"] / balance_sheet_statement["totalStockholdersEquity"]
        case "asset_turnover":
            return income_statement["revenue"] / balance_sheet_statement["totalAssets"]
        case "profit_margin":
            return income_statement["netIncome"] / income_statement["revenue"]
        case "equity_multiplier":
            return balance_sheet_statement["totalAssets"] / balance_sheet_statement["totalStockholdersEquity"]
        case "roe_market_cap":
            return income_statement["netIncome"] / market_cap["marketCap"]

        case "current_assets_share":
            return balance_sheet_statement["totalCurrentAssets"] / balance_sheet_statement["totalAssets"]
        case "non_current_assets_share":
            return balance_sheet_statement["totalNonCurrentAssets"] / balance_sheet_statement["totalAssets"]
        case "equity_share":
            return balance_sheet_statement["totalEquity"] / balance_sheet_statement["totalAssets"]
        case "liabilities_share":
            return balance_sheet_statement["totalLiabilities"] / balance_sheet_statement["totalAssets"]

        case "liquidity":
            return balance_sheet_statement["cashAndShortTermInvestments"] / balance_sheet_statement[
                "totalCurrentLiabilities"]
        case "solvency":
            return balance_sheet_statement["totalLiabilities"] / balance_sheet_statement["totalStockholdersEquity"]

        case "p_e":
            return market_cap["marketCap"] / income_statement["netIncome"]
        case "p_s":
            return market_cap["marketCap"] / income_statement["revenue"]
        case "p_b":
            return market_cap["marketCap"] / book_value

        case _:
            return None


def draw_chart(companies, analysis, labels, key, title, formatting):
    plt.rcParams["font.family"] = ["Helvetica", "Arial"]

    min_value = 0
    for company in companies:
        plt.plot(analysis[company]["labels"], analysis[company][key])

        company_min_value = min(analysis[company][key])
        if company_min_value < min_value:
            min_value = company_min_value

    plt.title(title)
    plt.xticks(labels)

    if min_value == 0:
        plt.ylim(bottom=0)

    ax = plt.gca()

    # Legend
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
    ax.legend(companies, loc="upper center", bbox_to_anchor=(0.5, -0.1), fancybox=True, ncol=len(companies))

    # Grid
    ax.set_axisbelow(True)
    ax.yaxis.grid(color="lightgray")
    ax.spines[["right", "top"]].set_visible(False)

    # y-axis formatting
    if formatting == "percent":
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    plt.savefig(f"./analysis/{key}.png", dpi=300)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+", help="stock symbols for analysis, separated with spaces")

    arguments = parser.parse_args()
    companies = arguments.symbols

    if not os.path.exists("analysis"):
        os.makedirs("analysis")

    analysis = {}
    fiscal_years = set()
    for company in companies:
        analysis[company] = {
            "labels": [],
        }

        income_statements = get_income_statements(company)
        balance_sheet_statements = get_balance_sheet_statements(company)

        # End date for getting the sufficient range for market capitalization
        end_date = datetime.strptime(income_statements[-1]["date"], "%Y-%m-%d")
        end_date += relativedelta(months=1)
        end_date = end_date.strftime("%Y-%m-%d")

        market_caps = get_market_caps(company, end_date)

        for income_statement, balance_sheet_statement in zip(income_statements, balance_sheet_statements):
            analysis[company]["labels"].append(int(income_statement["calendarYear"]))
            fiscal_years.add(int(income_statement["calendarYear"]))

            # Find the company's market capitalization on the date of the statement
            for market_cap in market_caps:
                statement_date = datetime.strptime(income_statement["date"], "%Y-%m-%d")
                market_cap_date = datetime.strptime(market_cap["date"], "%Y-%m-%d")

                if market_cap_date >= statement_date:
                    for metric in METRICS.keys():
                        if metric not in analysis[company]:
                            analysis[company][metric] = []
                        analysis[company][metric].append(
                            compute_metric(metric, income_statement, balance_sheet_statement, market_cap))
                    break

    report = {}
    for metric in METRICS.keys():
        labels = sorted(list(fiscal_years))

        draw_chart(companies, analysis, labels, metric, METRICS[metric]["name"], METRICS[metric]["type"])

        with open(f"./analysis/{metric}.csv", "w", newline="") as file:
            writer = csv.writer(file, delimiter=",")

            header_row = [" "] + labels + ["Average"]
            header_row = list(map(lambda x: f"'{x}'", header_row))
            writer.writerow(header_row)

            for company in companies:
                metric_data = analysis[company][metric]
                metric_data_row = metric_data.copy()

                # Format metric values
                if METRICS[metric]["type"] == "percent":
                    metric_data_row = list(map(lambda x: f"{(x * 100):.2f}\xa0%", metric_data_row))
                else:
                    metric_data_row = list(map(lambda x: f"{x:.2f}", metric_data_row))

                # Add empty cells for missing fiscal years to the start or the end of the table
                offset_start = min(analysis[company]["labels"]) - min(fiscal_years)
                for _ in range(offset_start):
                    metric_data_row.insert(0, " ")

                offset_end = max(fiscal_years) - max(analysis[company]["labels"])
                for _ in range(offset_end):
                    metric_data_row.append(" ")

                # Compute the average value
                average = sum(metric_data) / len(metric_data)
                if METRICS[metric]["type"] == "percent":
                    average = f"{(average * 100):.2f}\xa0%"
                else:
                    average = f"{average:.2f}"

                metric_data_row = [f"{company}"] + metric_data_row + [f"{average}"]
                metric_data_row = list(map(lambda x: f"'{x}'", metric_data_row))

                writer.writerow(metric_data_row)

        table = pd.read_csv(f"./analysis/{metric}.csv", index_col=False, quotechar="'", dtype=str)
        report[metric] = {
            "name": METRICS[metric]["name"],
            "chart": f"./{metric}.png",
            "table": table.to_html(index=False, border=0),
        }

    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("template.j2")
    html_report = minify_html.minify(template.render(report=report, companies=companies), minify_css=True,
                                     do_not_minify_doctype=True)
    with open("./analysis/analysis.html", "w") as file:
        file.write(html_report)
