# Quantopian-0.916
My Quantitative trading algorithms written on Quantopian for contest. The algorithm is designed to evaluate cross-sectional, long-short US equity strategies following a particular set of strict criteria.

![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/1.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/2.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/3.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/4.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/5.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/6.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/7.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/8.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/9.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/10.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/11.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/12.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/13.png)
![image](https://github.com/BenjiKCF/Quantopian-0.916/blob/master/image/14.png)

Critieria and risk model:

Trade liquid stocks: Trade liquid stocks: Contest entries must have 95% or more of their invested capital in stocks in the QTradableStocksUS universe (QTU, for short). This is checked at the end of each trading day by comparing an entry’s end-of-day holdings to the constituent members of the QTradableStocksUS on that day. Contest entries are allowed to have as little as 90% of their invested capital invested in members of the QTU on up to 2% of trading days in the backtest used to check criteria. This is in place to help mitigate the effect of turnover in the QTU definition.

Low position concentration: Contest entries cannot have more than 5% of their capital invested in any one asset. This is checked at the end of each trading day. Algorithms may exceed this limit and have up to 10% of their capital invested in a particular asset on up to 2% of trading days in the backtest used to check criteria.

Long/short: Contest entries must not have more than 10% net dollar exposure. This means that the long and short arms of a Contest entry can not be more than 10% different (measured as 10% of the total capital base). For example, if the entry has 100% of its capital invested, neither the sum value of the long investments nor the sum value of the short investments may exceed 55% of the total capital. This is measured at the end of each trading day. Entries may exceed this limit and have up to a 20% net dollar exposure on up to 2% of trading days in the backtest used to check criteria.

Turnover: Contest entries must have a mean daily turnover between 5%-65% measured over a 63-trading-day rolling window. Turnover is defined as amount of capital traded divided by the total portfolio value. For algorithms that trade once per day, Turnover ranges from 0-200% (200% means the algorithm completely moved its capital from one set of assets to another). Entries are allowed to have as little as 3% rolling mean daily turnover on up to 2% of trading days in the backtest used to check criteria. In addition, entries are allowed to have as much as 80% rolling mean daily turnover on 2% of trading days in the same backtest.

Leverage: Contest entries must maintain a gross leverage between 0.8x-1.1x. In other words entries must have between 80% and 110% of their capital invested in US equities. The leverage of an algorithm is checked at the end of each trading day. Entries are allowed to have as little as 70% of their capital invested (0.7x leverage) on up to 2% of trading days in the backtest used to check criteria. In addition, entries are allowed to have as much as 120% of their capital invested (1.2x leverage) on up to 2% of trading days in the same backtest. These buffers are meant to provide leniency in cases where trades are canceled, fill prices drift, or other events that can cause leverage to change unexpectedly.

Low beta-to-SPY: Contest entries must have an absolute beta-to-SPY below 0.3 (low correlation to the market). Beta-to-SPY is measured over a rolling 6-month regression length and is checked at the end of each trading day. The beta at the end of each day must be between -0.3 and 0.3. Contest entries can exceed this limit and have a beta-to-SPY of up to 0.4 on 2% of trading days in the backtest used to check criteria.

Low exposure to Quantopian risk model: Contest entries must be less than 20% exposed to each of the 11 sectors defined in the Quantopian risk model. Contest entries must also be less than 40% exposed to each of the 5 style factors in the risk model. Exposure to risk factors in the Quantopian risk model is measured as the mean net exposure over a 63-trading-day rolling window at the end of each trading day. Contest entries can exceed these limits on up to 2% of trading days 2 from years before the entry was submitted to today. Entries are allow to have each of sector exposure as high as 25% on 2% of trading days. Additionally, each style exposure can go as high as 50% on 2% of trading days.

Positive returns: Contest entries must have positive total returns. The return used for the Positive Returns constraint is defined as the portfolio value at the end of the backtest used to check criteria divided by the starting capital ($10M). As with all the criteria, the positive returns criterion is re-checked after each day that an entry remains active in the contest.

The risk model consists of a series of cascading linear regressions on each asset. In each step in the cascade, we calculate a regression, and pass the residual returns for each asset to the next step.

Sector returns - Our model has 11 sectors. A sector ETF is specified to represent each sector factor. Each stock is assigned to a sector. We perform a regression to calculate each stock's beta to its respective sector. A portion of each stock's return is attributable to its sector. The residual return is calculated and passed to the next step.

Style risk - We start with the residual from the sector return, above. We then regress the stock against the 5 style factors together. The five styles in the Quantopian risk model:

Momentum - The momentum factor captures return differences between stocks on an upswing (winner stocks) and the stocks on a downswing (loser stocks) over 11 months.
Company Size - The size factor captures return differences between big-cap stocks and small-cap stocks.
Value - The value factor captures return differences between expensive stocks and in-expensive stocks (measured by the ratio of book value of company to the price of the stock).
Short-term Reversal - The short-term reversal factor captures return differences between stocks with strong losses to reverse (recent loser stocks) and the stocks with strong gains (recent winner stocks) to reverse in a short time period.
Volatility - The volatility factor captures return differences between high volatility stocks and low volatility stocks in the market. The volatility can be measured in historical long term or near-term.
