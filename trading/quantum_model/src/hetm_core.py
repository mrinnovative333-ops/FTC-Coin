"""
Holographic Entanglement Trading Model (HETM)
Core module for quantum-inspired market analysis.
"""

import numpy as np
import pandas as pd
from scipy.stats import entropy
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import LedoitWolf
import networkx as nx


class MarketQubit:
    """
    Represents a single asset as a quantum-like state.
    The density matrix is built from a feature embedding of returns, volume, range, etc.
    """
    def __init__(self, returns, features=None, bandwidth=1.0):
        self.returns = np.asarray(returns).flatten()
        if features is not None:
            self.features = np.asarray(features)
        else:
            # Default features: returns, squared returns (vol proxy), rolling mean
            self.features = np.column_stack([
                self.returns,
                self.returns ** 2,
                pd.Series(self.returns).rolling(5, min_periods=1).mean().values,
            ])
        self.scaler = StandardScaler()
        self.features_scaled = self.scaler.fit_transform(self.features)
        self.bandwidth = bandwidth
        self.rho = self._compute_density_matrix()

    def _compute_density_matrix(self):
        """
        Build a density matrix from normalized feature covariance.
        Uses Ledoit-Wolf shrinkage for stability.
        """
        if self.features_scaled.shape[0] < 2:
            n = self.features_scaled.shape[1]
            return np.eye(n) / n
        cov = LedoitWolf().fit(self.features_scaled).covariance_
        # Normalize to trace 1
        rho = cov / np.trace(cov)
        # Ensure positive semidefinite
        eigvals, eigvecs = np.linalg.eigh(rho)
        eigvals = np.maximum(eigvals, 1e-10)
        rho = eigvecs @ np.diag(eigvals / eigvals.sum()) @ eigvecs.T
        return rho

    def von_neumann_entropy(self):
        eigvals = np.linalg.eigvalsh(self.rho)
        eigvals = eigvals[eigvals > 1e-12]
        return -np.sum(eigvals * np.log(eigvals))


class EntanglementBulk:
    """
    Builds a bulk geometry graph from multi-asset density matrices.
    Edges = ER-bridges (high mutual information / quantum mutual information proxy).
    """
    def __init__(self, assets_data, lookback=60, er_threshold=0.3):
        """
        assets_data: dict {asset_name: DataFrame with 'Close', 'Volume', optionally others}
        """
        self.asset_names = list(assets_data.keys())
        self.lookback = lookback
        self.er_threshold = er_threshold
        self.returns_df = self._compute_returns(assets_data)
        self.qubits = self._build_qubits()
        self.graph = self._build_bulk_geometry()

    def _compute_returns(self, assets_data):
        prices = pd.DataFrame({name: df["Close"] for name, df in assets_data.items()})
        prices = prices.dropna()
        return prices.pct_change().dropna()

    def _build_qubits(self):
        qubits = {}
        for name in self.asset_names:
            r = self.returns_df[name].values[-self.lookback:]
            if len(r) < 10:
                continue
            qubits[name] = MarketQubit(r)
        return qubits

    def _classical_mutual_information(self, x, y, bins=20):
        """
        Estimate mutual information I(X;Y) from histograms.
        """
        c_xy = np.histogram2d(x, y, bins=bins)[0]
        c_x = c_xy.sum(axis=1)
        c_y = c_xy.sum(axis=0)

        p_xy = c_xy / c_xy.sum()
        p_x = c_x / c_x.sum()
        p_y = c_y / c_y.sum()

        mi = 0.0
        for i in range(bins):
            for j in range(bins):
                if p_xy[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                    mi += p_xy[i, j] * np.log(p_xy[i, j] / (p_x[i] * p_y[j]))
        return max(0, mi)

    def _build_bulk_geometry(self):
        G = nx.Graph()
        for name in self.qubits:
            G.add_node(name)

        names = list(self.qubits.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                # Use classical mutual information of returns as ER-bridge weight
                r_i = self.returns_df[names[i]].values[-self.lookback:]
                r_j = self.returns_df[names[j]].values[-self.lookback:]
                if len(r_i) != len(r_j):
                    continue
                mi = self._classical_mutual_information(r_i, r_j)
                if mi > self.er_threshold:
                    G.add_edge(names[i], names[j], weight=mi, er_bridge=True)
        return G

    def get_er_bridges(self, top_n=10):
        edges = sorted(self.graph.edges(data=True), key=lambda x: x[2]["weight"], reverse=True)
        return edges[:top_n]

    def get_geodesic(self, source, target):
        try:
            path = nx.shortest_path(self.graph, source, target, weight="weight")
            length = nx.shortest_path_length(self.graph, source, target, weight="weight")
            return path, length
        except nx.NetworkXNoPath:
            return None, None

    def get_centrality(self):
        return nx.degree_centrality(self.graph)

    def get_entropy_time_series(self):
        """Von Neumann entropy for each asset — proxy for local market complexity."""
        return {name: q.von_neumann_entropy() for name, q in self.qubits.items()}


class HolographicTrader:
    """
    Generates trading signals from the bulk geometry.
    """
    def __init__(self, bulk, target_asset="EURUSD"):
        self.bulk = bulk
        self.target = target_asset
        self.returns = bulk.returns_df[target_asset]

    def signal(self, lookback=20, entropy_regime_threshold=1.2):
        """
        Returns a dict with:
        - direction: 1 (long), -1 (short), 0 (flat)
        - confidence: 0..1
        - rationale: string
        """
        if len(self.returns) < lookback + 1:
            return {"direction": 0, "confidence": 0, "rationale": "Insufficient data"}

        recent = self.returns.values[-lookback:]
        momentum = recent[-1] - recent.mean()

        # ER-bridge pressure: weighted average return of entangled neighbors
        neighbors = list(self.bulk.graph.neighbors(self.target))
        if not neighbors:
            return {"direction": 0, "confidence": 0, "rationale": "No ER-bridges found"}

        weights = []
        neighbor_returns = []
        for n in neighbors:
            w = self.bulk.graph[self.target][n]["weight"]
            weights.append(w)
            neighbor_returns.append(self.bulk.returns_df[n].values[-1])

        weights = np.array(weights)
        neighbor_returns = np.array(neighbor_returns)
        bulk_pressure = np.average(neighbor_returns, weights=weights)

        # Entropy regime check
        entropies = self.bulk.get_entropy_time_series()
        target_entropy = entropies.get(self.target, 0)
        entropy_regime = target_entropy / np.mean(list(entropies.values())) if entropies else 1.0

        # Combine signals
        score = np.sign(momentum) * 0.3 + np.sign(bulk_pressure) * 0.5
        if entropy_regime > entropy_regime_threshold:
            # High entropy = uncertainty, reduce directional confidence
            score *= 0.6

        direction = int(np.sign(score))
        confidence = min(abs(score), 1.0)

        rationale = (
            f"Momentum={momentum:.5f}, BulkPressure={bulk_pressure:.5f}, "
            f"EntropyRegime={entropy_regime:.2f}, Neighbors={len(neighbors)}"
        )

        return {
            "direction": direction,
            "confidence": confidence,
            "rationale": rationale,
            "momentum": momentum,
            "bulk_pressure": bulk_pressure,
            "entropy_regime": entropy_regime,
        }


def demo():
    """Run a minimal example once multi-asset data is loaded."""
    print("HETM loaded. Use load_data() and EntanglementBulk() to run analysis.")


if __name__ == "__main__":
    demo()
