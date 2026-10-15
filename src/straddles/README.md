# Straddles

European calls and puts priced using Black-Scholes-Merton. From the
project root, import from `src.straddles` (or `straddles` with `src` on PYTHONPATH).

```python
import numpy as np
import matplotlib.pyplot as plt
from src.straddles import Call, Put, Portfolio

# Positional arguments: strike, time to expiry in years, annual volatility.
straddle = Call(100, 30 / 365, 0.20) + Put(100, 30 / 365, 0.20)
print(straddle.theo(100))
print(straddle.greeks(100, elapsed=7 / 365))

# Short positions, quantities, nested portfolios and sum() are supported.
spread = 2 * Call(100, 1, 0.2) - Call(110, 1, 0.2)
portfolio = Portfolio([straddle, (3, spread)])

spots = np.linspace(70, 130, 301)
plt.plot(spots, straddle.theo(spots), label="Today")
plt.plot(spots, straddle.theo(spots, elapsed=15 / 365), label="In 15 days")
plt.legend()
plt.show()

# Broadcast spot and elapsed time to produce a surface for any metric.
delta_surface = portfolio.delta(spots[:, None], elapsed=np.array([0, 7, 15]) / 365)
```

All tradeables implement `theo`, `delta`, `gamma`, `theta`, `vega`, `rho`,
`greeks` (a dictionary), and `evaluate` (theo and all Greeks together).
Implement `Tradeable.evaluate` to introduce another instrument type.

Spot and scenario arguments accept scalars or broadcastable arrays. Each leg
retains its initial maturity and volatility. `elapsed` reduces each maturity;
`volatility`, when supplied, overrides every leg's volatility. Optional `rate`
and continuous dividend yield `dividend` default to zero and use annual decimals.
Prices are per underlying unit, without a contract multiplier or initial premium.
All legs refer to the same underlying and valuation date.

Theta measures change as calendar time advances and is per year; divide by 365
for daily theta. Vega and rho are per unit change; divide by 100 for a one
percentage-point change. Volatility `.20` means 20%, not `20`.

At and after a leg's expiry its value is intrinsic at the supplied scenario spot;
this is a payoff surface, not a simulation of historical settlement or cash
reinvestment. Expired theta, vega and rho are zero. At deterministic payoff kinks,
delta uses the midpoint convention and gamma is NaN because the derivative is
undefined. At zero volatility before expiry, vega at the forward strike uses its
right-hand limit. Zero volatility otherwise uses discounted deterministic payoffs.

Inputs are assumed to be valid. Results are NumPy values or arrays; an empty
portfolio returns zero for each metric.

## Direction and underlying

Every tradeable has `sign=1` for bought or `sign=-1` for sold, supplied as a
keyword. Call/put type is separate from position direction. The sign applies
to theo and every Greek, including when a signed portfolio is nested.

```python
from src.straddles import Underlying, Call

stock = Underlying()
short_call = Call(100, 30 / 365, 0.20, sign=-1)
covered_call = stock + short_call
stock.theo(100)  # 100
stock.delta(100)  # 1
```

`Underlying` is valued at `sign * spot`. Delta is `sign`; gamma, theta,
vega and rho are zero. Scenario arguments broadcast the output for plotting
but do not change its value at a given spot. Financing costs and future carry
are not included.
