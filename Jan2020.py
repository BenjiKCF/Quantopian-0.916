"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.pipeline.factors import SimpleBeta
import quantopian.algorithm as algo
from quantopian.pipeline.filters import QTradableStocksUS
from quantopian.pipeline.data import Fundamentals, morningstar
from quantopian.pipeline.data import builtin, morningstar as mstar
from quantopian.pipeline.classifiers.morningstar import Sector
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline import Pipeline, CustomFactor
from quantopian.pipeline.factors import Returns, AverageDollarVolume
from quantopian.pipeline.experimental import risk_loading_pipeline  
from quantopian.pipeline.factors.morningstar import MarketCap
import time
from datetime import date  
from datetime import timedelta  
import quantopian.optimize as opt
# Algorithm Parameters
# --------------------
# Universe Selection Parameters
LIQUIDITY_LOOKBACK_LENGTH = 300
# Constraint Parameters
MAX_GROSS_EXPOSURE = 1.0
MAX_SHORT_POSITION_SIZE = 0.015# 1.5% #0.005
MAX_LONG_POSITION_SIZE = 0.015# 1.5%
UNIVERSE_SIZE = 3000

# Scheduling Parameters
MINUTES_AFTER_OPEN_TO_TRADE = 120
BASE_UNIVERSE_RECALCULATE_FREQUENCY = 'month_start'  # {week,quarter,year}_start are also valid

# 0.03, 0.015
# 

class Momentum(CustomFactor):
    # Default inputs
    inputs = [USEquityPricing.close]
    # Compute momentum
    def compute(self, today, assets, out, close):
        out[:] = close[-1] / close[0]

class AverageMonthlyTradingVolume(CustomFactor):   
    # Monthly trading volume is the total number of shares traded each month 
    # as a percentage of the total number of shares outstanding at the end of the month.
    # Pre-declare inputs and window_length
    inputs = [USEquityPricing.volume,morningstar.valuation.shares_outstanding] 
    window_length = 252
    # Compute factor1 value
    def compute(self, today, assets, out, volume, shares):       
        monthly = sum(volume[-21:])/sum(shares[-21:])
        yearly = sum(volume[:])/sum(shares[:])
        out[:] = monthly/yearly
        
def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    #This is for the trend following filter
    context.spy = sid(8554)
    context.TF_filter = False
    context.TF_lookback = 126
    # Attach the risk loading pipeline to our algorithm.
    algo.attach_pipeline(risk_loading_pipeline(), 'risk_loading_pipeline')
    algo.attach_pipeline(make_pipeline(), 'pipe')
    # Schedule a function, 'do_portfolio_construction', to run once a week
    # ten minutes after market open.
    algo.schedule_function(
        do_portfolio_construction,
        date_rule=algo.date_rules.week_start(),
        time_rule=algo.time_rules.market_open(minutes=MINUTES_AFTER_OPEN_TO_TRADE),
        half_days=False,
    )

def make_pipeline():
    base_universe = QTradableStocksUS()
    beta = SimpleBeta(
                target=sid(8554),
                regression_length=260,
                )
    universe = (Sector().notnull() & base_universe & beta.notnull())
    AMTvol = AverageMonthlyTradingVolume()
    #market_cap = Fundamentals.market_cap.latest
    #book_to_price = 1/Fundamentals.pb_ratio.latest
    momentum = Momentum(window_length=252)
    growth = Fundamentals.growth_score.latest
    
    # Alpha Generation
    # ----------------
    # Compute Z-scores  
    AMTvol_z = AMTvol.zscore(mask=universe)
    growth_z = growth.zscore(mask=universe)
    large = AMTvol_z.percentile_between(80,100)
    fast = growth_z.percentile_between(80,100)
    momentum_z = momentum.zscore(mask=(universe & (fast | large)))
    # Alpha Combination
    # -----------------
    # Assign every asset a combined rank and center the values at 0.
    # For UNIVERSE_SIZE=500, the range of values should be roughly -250 to 250.
    alpha1 = (momentum_z).rank().demean()    
    
    # S2
    monthly_top_volume = (
        AverageDollarVolume(window_length=LIQUIDITY_LOOKBACK_LENGTH)
        .top(UNIVERSE_SIZE, mask=universe)
        .downsample(BASE_UNIVERSE_RECALCULATE_FREQUENCY))
    universe2 = (monthly_top_volume & universe)
    vr = mstar.valuation_ratios
    #fcf_zscore = vr.fcf_yield.latest.zscore(mask=universe2)
    yield_zscore = vr.earning_yield.latest.zscore(mask=universe2)
    roe_zscore = Fundamentals.roic.latest.zscore(mask=universe2)
    ltd_to_eq = Fundamentals.long_term_debt_equity_ratio.latest.zscore(mask=universe2)
    value = (Fundamentals.cash_return.latest.zscore(mask=universe2) + Fundamentals.fcf_yield.latest.zscore(mask=universe2)).zscore()
    quality = (roe_zscore + ltd_to_eq +value + 0)
    
    #alpha2 = (fcf_zscore + yield_zscore+quality).rank().demean()
    alpha2 = (yield_zscore+quality).rank().demean()
    
    combined_alpha = alpha1 + alpha2
    
    return Pipeline(
        columns={
            'Momentum': momentum,
            'Volume': AMTvol,
            'Growth_score':growth,
            'sector':Sector(),
            'alpha':combined_alpha,
            'beta': beta,
        },
        screen= combined_alpha.notnull() 
    )


def before_trading_start(context, data):
    # Call pipeline_output in before_trading_start so that pipeline
    # computations happen in the 5 minute timeout of BTS instead of the 1
    # minute timeout of handle_data/scheduled functions.
    # Get the risk loading data every day.
    context.risk_loading_pipeline = algo.pipeline_output('risk_loading_pipeline')
    context.pipeline_data = algo.pipeline_output('pipe')


# Portfolio Construction
# ----------------------
def do_portfolio_construction(context, data):
    pipeline_data = context.pipeline_data
    # Objective
    # ---------
    # For our objective, we simply use our naive ranks as an alpha coefficient
    # and try to maximize that alpha.
    # 
    # This is a **very** naive model. Since our alphas are so widely spread out,
    # we should expect to always allocate the maximum amount of long/short
    # capital to assets with high/low ranks.
    #
    # A more sophisticated model would apply some re-scaling here to try to generate
    # more meaningful predictions of future returns.
    objective = opt.MaximizeAlpha(pipeline_data.alpha)

    # Constraints
    # -----------
    # Constrain our gross leverage to 1.0 or less. This means that the absolute
    # value of our long and short positions should not exceed the value of our
    # portfolio.
    constrain_gross_leverage = opt.MaxGrossExposure(MAX_GROSS_EXPOSURE)
    
    # Constrain individual position size to no more than a fixed percentage 
    # of our portfolio. Because our alphas are so widely distributed, we 
    # should expect to end up hitting this max for every stock in our universe.
    constrain_pos_size = opt.PositionConcentration.with_equal_bounds(
        -MAX_SHORT_POSITION_SIZE,
        MAX_LONG_POSITION_SIZE,
    )

    # Constrain ourselves to allocate the same amount of capital to 
    # long and short positions.
    market_neutral = opt.DollarNeutral()
    
    # Constrain ourselve to have a net leverage of 0.0 in each sector.
    sector_neutral = opt.NetGroupExposure.with_equal_bounds(
        labels=pipeline_data.sector,
        min=-0.0025,
        max=0.0025,
    )

    beta_neutral = opt.FactorExposure(
            pipeline_data[['beta']],
            min_exposures={'beta': -0.05},
            max_exposures={'beta': 0.05},
        )
    # Constrain our risk exposures. We're using version 0 of the default bounds
    # which constrain our portfolio to 18% exposure to each sector and 36% to
    # each style factor.
    constrain_sector_style_risk = opt.experimental.RiskModelExposure(  
        risk_model_loadings=context.risk_loading_pipeline.dropna(),  
        version=0,
        max_momentum=0.3,
        min_short_term_reversal = -0.3
    )
    
    # Run the optimization. This will calculate new portfolio weights and
    # manage moving our portfolio toward the target.
    algo.order_optimal_portfolio(
        objective=objective,
        constraints=[
            constrain_gross_leverage,
            constrain_pos_size,
            market_neutral,
            sector_neutral,
            beta_neutral,
            constrain_sector_style_risk
        ],
    )