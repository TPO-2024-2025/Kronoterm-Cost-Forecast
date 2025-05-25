"""Prediction model for predictor."""

from datetime import datetime, timedelta
from typing import Any, Self
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor  # type: ignore
import pickle


class Predictor:
    """Interface for energy providers."""

    INTERVALS: int = 15  # min

    def __init__(self) -> None:
        """Initialize an untrained Gradient Boosting Regressor model."""
        self.model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, random_state=42
        )
        self.history: list[tuple[datetime, float]] = []

    @staticmethod
    def _datetime_to_features(dt: datetime) -> list[float]:
        """Convert datetime to numerical features for the model."""
        return [
            dt.hour + dt.minute / 60,
            dt.weekday(),
            int(dt.weekday() >= 5),
            np.sin(2 * np.pi * dt.hour / 24),
            np.cos(2 * np.pi * dt.hour / 24),
            np.sin(2 * np.pi * dt.minute / 60),
            np.cos(2 * np.pi * dt.minute / 60),
            np.sin(2 * np.pi * (dt.hour * 60 + dt.minute) / (24 * 60)),
            np.cos(2 * np.pi * (dt.hour * 60 + dt.minute) / (24 * 60)),
            dt.month,
            dt.isocalendar().week,
            np.sin(2 * np.pi * dt.month / 12),
            np.cos(2 * np.pi * dt.month / 12),
            np.sin(2 * np.pi * dt.isocalendar().week / 52),
            np.cos(2 * np.pi * dt.isocalendar().week / 52),
        ]

    def dump(self) -> Any:
        """Return model in serializable format."""
        return pickle.dumps((self.model, self.history))

    @classmethod
    def load(cls: type[Self], m: Any) -> Self:
        """Load model from serializable format."""
        instance = cls()
        instance.model, instance.history = pickle.loads(m)
        return instance

    @classmethod
    def new(cls: type[Self], data: list[tuple[datetime, float]]) -> Self:
        """Create and return a trained model from initial data."""
        instance = cls()
        instance.fit(data)
        return instance

    def fit(self, data: list[tuple[datetime, float]] | None = None) -> None:
        """Fit linear regression model to the provided data."""
        if data is not None:
            self.history.extend(data)

        if not self.history:
            return

        filtered_history = [
            (dt, val) for dt, val in self.history if isinstance(val, int | float)
        ]

        if not filtered_history:
            return

        X = np.array([self._datetime_to_features(dt) for dt, _ in filtered_history])
        y = np.array([val for _, val in filtered_history])
        self.model.fit(X, y)

    def add_and_refit(self, dt: datetime, value: float) -> None:
        """Add new data point and refit the model."""
        self.history.append((dt, value))
        self.fit()

    def _predict(self, dt: datetime) -> float | None:
        """Predict consumption using the trained regression model."""
        X = np.array(self._datetime_to_features(dt)).reshape(1, -1)
        return abs(float(self.model.predict(X)[0]))

    def forecast(self, start: datetime) -> list[tuple[datetime, float | None]]:
        """Return series of predicted consumption (per interval defined in this class)."""

        def dt_fixed(dt: datetime, i: int = 0) -> datetime:
            d = datetime(
                dt.year,
                dt.month,
                dt.day,
                dt.hour,
                (dt.minute // self.INTERVALS) * self.INTERVALS,
                0,
                0,
                dt.tzinfo,
                fold=dt.fold,
            )
            return d + timedelta(minutes=self.INTERVALS * i)

        return [
            (dt_fixed(start, i), self._predict(dt_fixed(start, i)))
            for i in range(4 * 8)
        ]
