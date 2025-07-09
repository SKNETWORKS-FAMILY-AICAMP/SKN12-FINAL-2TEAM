import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 특성값 매핑
RISK_MAP = {'low': 0, 'medium': 0.5, 'high': 1}
HORIZON_MAP = {'intraday': 0, 'swing': 0.5, 'long-term': 1}
STYLE_MAP = {'momentum': 0, 'mean reversion': 0.33, 'scalping': 0.66, 'swing': 1}

FEATURES = ['risk_tolerance', 'trading_style', 'investment_horizon']

class UserAlgoEmbeddingRecommender:
    def __init__(self, user_df: pd.DataFrame, algo_df: pd.DataFrame):
        self.user_df = user_df.copy()
        self.algo_df = algo_df.copy()
        self.user_vecs = None
        self.algo_vecs = None

    def to_numeric(self, row):
        return [
            RISK_MAP.get(row['risk_tolerance'], 0),
            STYLE_MAP.get(row['trading_style'], 0),
            HORIZON_MAP.get(row['investment_horizon'], 0)
        ]

    def vectorize(self):
        self.user_vecs = self.user_df.apply(self.to_numeric, axis=1, result_type='expand').values
        self.algo_vecs = self.algo_df.apply(self.to_numeric, axis=1, result_type='expand').values
        return self.user_vecs, self.algo_vecs

    def recommend(self):
        if self.user_vecs is None or self.algo_vecs is None:
            self.vectorize()
        sim = cosine_similarity(self.user_vecs, self.algo_vecs)
        best_algo_idx = sim.argmax(axis=1)
        recommended_algos = self.algo_df['name'].iloc[best_algo_idx].values
        return recommended_algos, sim

# 사용 예시 (노트북/스크립트에서)
# user_data = [
#     {"user_id": 1, "risk_tolerance": "high", "trading_style": "momentum", "investment_horizon": "intraday"},
#     {"user_id": 2, "risk_tolerance": "low", "trading_style": "mean reversion", "investment_horizon": "long-term"},
# ]
# algo_data = [
#     {"name": "PPO", "risk_tolerance": "low", "trading_style": "swing", "investment_horizon": "long-term"},
#     {"name": "SAC", "risk_tolerance": "high", "trading_style": "momentum", "investment_horizon": "intraday"},
# ]
# user_df = pd.DataFrame(user_data)
# algo_df = pd.DataFrame(algo_data)
# recommender = UserAlgoEmbeddingRecommender(user_df, algo_df)
# recommended_algos, sim = recommender.recommend()
# print(recommended_algos) 