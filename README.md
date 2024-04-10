# Finspan
Finspan is a simple program for stock analysis. It allows you to quickly obtain the most common metrics used for stock analysis, such as ROA, ROE, asset turnover, profit margin, liquidity, solvency, P/E, and more in the form of tables and charts.

## Prerequisites
Finspan requires Python 3.12.

Finspan also requires the following packages:
* `matplotlib`
* `python-dateutil`

### External data

Finspan uses data from [Financial Modeling Prep API](https://site.financialmodelingprep.com). You will need a valid Financial Modeling Prep API key which you can get by signing up on their website. At the time of writing, a free API key is available which limits you to 250 API requests per day and stocks listed on the US stock exchanges, however, stocks of most large companies that are located outside the US can also be found on US stock exchanges.

### Setup

Before you run Finspan for the first time, create an empty `secret.py` file in the project directory with the following contents:

```
API_KEY = "{{ Your API key}}"
```

Make sure to replace `{{ Your API key }}` with your own Financial Modeling Prep API key.

## Usage

When all the requirements are satisfied, you can run Finspan by running:

```
python3 finspan.py --symbols [SYMBOLS]
```

Replace `[SYMBOLS]` in the command above with a list of stock symbols of the companies you would like to analyze, separated with spaces. For instance, if you would like to analyze Visa (V), MasterCard (MA), and American Express (AXP), use the following command to run Finspan:

```
python3 finspan.py --symbols V MA AXP
```

If you would like to analyze a company that is trading under multiple different symbols, all of them should produce the same result, so using any of them should be fine.

The charts and spreadsheets are exported to the `analysis` directory.

## Features

Finspan currently computes the following metrics:
* ROA (return on assets)
* ROE (return on equity)
* Asset turnover
* Profit margin
* Equity multiplier
* ROE (using market capitalization instead of equity)
* Share of current assets
* Share of non-current assets
* Share of equity
* Share of liabilities
* Liquidity
* Solvency
* P/E (price to earnings ratio)
* P/S (price to sales ratio)
* P/B (price to book value ratio)

For each metric, a chart that shows the change of the metric values through years and the corresponding spreadsheet with all metric values and their averages for each analyzed company is exported.

**DISCLAIMER:** Investments in securities are associated with financial risks. The author does not promote any specific product, does not guarantee the correct operation of the program, and does not assume any responsibility for possible financial losses.