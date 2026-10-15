"""Composable European options under Black-Scholes-Merton."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr


@dataclass(kw_only=True)
class Tradeable(ABC):
    """Implement evaluate() to add another composable instrument.

    Valuation arguments broadcast like NumPy arrays. Time is in years,
    volatility and rates are decimals. Theta is per year; vega and rho
    are per unit (divide by 100 for a percentage-point sensitivity).
    """

    sign: int = 1  # +1 bought, -1 sold

    @abstractmethod
    def evaluate(self, spot, *, elapsed=0, volatility=None, rate=0, dividend=0):
        """Return a mapping of theo, delta, gamma, theta, vega and rho."""

    def theo(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["theo"]

    def greeks(self, spot, **scenario):
        return {k: v for k, v in self.evaluate(spot, **scenario).items() if k != "theo"}

    def delta(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["delta"]

    def gamma(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["gamma"]

    def theta(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["theta"]

    def vega(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["vega"]

    def rho(self, spot, **scenario):
        return self.evaluate(spot, **scenario)["rho"]

    def __add__(self, other):
        return Portfolio((self, other))

    def __radd__(self, other):
        return self if other == 0 else self + other

    def __neg__(self):
        return self * -1

    def __sub__(self, other):
        return self + -other

    def __mul__(self, quantity):
        return Portfolio(((quantity, self),))

    __rmul__ = __mul__


class Underlying(Tradeable):
    """An underlying position valued at the supplied spot."""

    def evaluate(self, spot, *, elapsed=0, volatility=None, rate=0, dividend=0):
        spot = np.broadcast_arrays(
            spot, elapsed, rate, dividend, 0 if volatility is None else volatility
        )[0]
        theo = self.sign * spot
        zeros = np.zeros_like(theo)
        return {
            "theo": theo,
            "delta": np.full_like(theo, self.sign),
            "gamma": zeros,
            "theta": zeros,
            "vega": zeros,
            "rho": zeros,
        }


@dataclass
class Option(Tradeable):
    """Strike, initial time to expiry (years), annual volatility (decimal)."""

    strike: float
    time_to_expiry: float
    volatility: float

    @property
    @abstractmethod
    def option_type(self):
        """+1 for calls, -1 for puts, independent of buy/sell direction."""

    def evaluate(self, spot, *, elapsed=0, volatility=None, rate=0, dividend=0):
        s, elapsed, vol, r, q = np.broadcast_arrays(
            spot,
            elapsed,
            self.volatility if volatility is None else volatility,
            rate,
            dividend,
        )
        t = np.maximum(self.time_to_expiry - elapsed, 0)
        k, sign = self.strike, self.option_type
        ds, dk = np.exp(-q * t), np.exp(-r * t)
        forward_diff = s * ds - k * dk
        regular = (t > 0) & (vol > 0) & (s > 0)
        # Safe placeholders avoid divisions by zero in deterministic scenarios.
        safe_t = np.where(regular, t, 1)
        safe_vol = np.where(regular, vol, 1)
        safe_s = np.where(regular, s, k)
        root = np.sqrt(safe_t)
        d1 = (np.log(safe_s / k) + (r - q + safe_vol**2 / 2) * safe_t) / (
            safe_vol * root
        )
        d2 = d1 - safe_vol * root
        n1, n2 = ndtr(sign * d1), ndtr(sign * d2)
        density = np.exp(-(d1**2) / 2) / np.sqrt(2 * np.pi)
        active = np.where(
            sign * forward_diff > 0, 1.0, np.where(forward_diff == 0, 0.5, 0.0)
        )
        values = {
            "theo": np.where(
                regular,
                sign * (s * ds * n1 - k * dk * n2),
                np.maximum(sign * forward_diff, 0),
            ),
            "delta": np.where(regular, sign * ds * n1, sign * ds * active),
            "gamma": np.where(regular, ds * density / (safe_s * safe_vol * root), 0.0),
            "vega": np.where(regular, s * ds * density * root, 0.0),
            "theta": np.where(
                regular,
                -s * ds * density * safe_vol / (2 * root)
                + sign * q * s * ds * n1
                - sign * r * k * dk * n2,
                sign * (q * s * ds - r * k * dk) * active,
            ),
            "rho": np.where(
                regular, sign * k * t * dk * n2, sign * k * t * dk * active
            ),
        }
        # At a deterministic payoff kink these derivatives do not exist.
        kink = (~regular) & (forward_diff == 0)
        values["gamma"] = np.where(kink, np.nan, values["gamma"])
        values["vega"] = np.where(
            (t > 0) & (vol == 0) & (forward_diff == 0),
            s * ds * np.sqrt(t) / np.sqrt(2 * np.pi),
            values["vega"],
        )
        values["theta"] = np.where(t == 0, 0.0, values["theta"])
        return {name: self.sign * value for name, value in values.items()}


class Call(Option):
    option_type = 1


class Put(Option):
    option_type = -1


@dataclass(init=False)
class Portfolio(Tradeable):
    """Weighted legs; accepts instruments or (quantity, instrument).

    Nested portfolios flatten automatically. All legs share the scenario's
    underlying spot, rates and optional volatility override.
    """

    positions: tuple[tuple[float, Tradeable], ...]

    def __init__(self, positions=(), *, sign=1):
        self.sign = sign
        flattened = []
        for position in positions:
            quantity, instrument = (
                (1.0, position) if isinstance(position, Tradeable) else position
            )
            legs = (
                instrument.positions
                if isinstance(instrument, Portfolio)
                else ((1.0, instrument),)
            )
            for weight, leg in legs:
                combined = quantity * weight
                if isinstance(instrument, Portfolio):
                    combined *= instrument.sign
                if combined != 0:
                    flattened.append((combined, leg))
        self.positions = tuple(flattened)

    def evaluate(self, spot, *, elapsed=0, volatility=None, rate=0, dividend=0):
        values = dict.fromkeys(("theo", "delta", "gamma", "theta", "vega", "rho"), 0)
        for quantity, leg in self.positions:
            result = leg.evaluate(
                spot,
                elapsed=elapsed,
                volatility=volatility,
                rate=rate,
                dividend=dividend,
            )
            for name in values:
                values[name] += quantity * result[name]
        return {name: self.sign * value for name, value in values.items()}
