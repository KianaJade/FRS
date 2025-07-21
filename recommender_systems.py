import numpy as np
import pandas as pd
import scipy.sparse
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from surprise import Dataset, Reader, KNNBasic, SVD
from surprise.model_selection import cross_validate, train_test_split
import warnings

warnings.filterwarnings('ignore')

# 加载处理后的数据
full_data = pd.read_csv('data/processed/full_data.csv')
tfidf_matrix = scipy.sparse.load_npz('data/processed/tfidf_matrix.npz')
le_user = joblib.load('data/processed/le_user.pkl')
le_movie = joblib.load('data/processed/le_movie.pkl')
tfidf = joblib.load('data/processed/tfidf_vectorizer.pkl')

# 在recommender_systems.py已有导入下方添加
le_movie = joblib.load('data/processed/le_movie.pkl')  # 加载电影ID编码器

class RecommenderSystem:
    def __init__(self, ratings_data, movie_features, le_movie):
        self.ratings = ratings_data
        self.movie_features = movie_features
        self.le_movie = le_movie
        self.user_item_matrix = self._create_user_item_matrix()  # 初始化用户-物品矩阵

    def _create_user_item_matrix(self):
        """创建用户-物品评分矩阵"""
        return self.ratings.pivot(index='userId', columns='movieId', values='rating').fillna(0)

    def user_based_cf(self, user_id, n_recommendations=10):
        """基于用户的协同过滤推荐"""
        # 计算用户相似度
        user_similarity = cosine_similarity(self.user_item_matrix)
        user_similarity_df = pd.DataFrame(
            user_similarity,
            index=self.user_item_matrix.index,
            columns=self.user_item_matrix.index
        )

        # 找到相似用户
        similar_users = user_similarity_df[user_id].sort_values(ascending=False)[1:11]

        # 生成推荐
        user_ratings = self.user_item_matrix.loc[user_id]
        unrated_movies = user_ratings[user_ratings == 0].index

        recommendations = {}
        for movie in unrated_movies:
            movie_ratings = self.user_item_matrix[movie]
            weighted_sum = 0
            sim_sum = 0

            for similar_user, similarity in similar_users.items():
                rating = movie_ratings.loc[similar_user]
                if rating > 0:
                    weighted_sum += similarity * rating
                    sim_sum += similarity

            if sim_sum > 0:
                recommendations[movie] = weighted_sum / sim_sum

        # 按预测评分排序并返回前n个推荐
        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]

    def item_based_cf(self, user_id, n_recommendations=10):
        """基于物品的协同过滤推荐"""
        # 计算物品相似度
        item_similarity = cosine_similarity(self.user_item_matrix.T)
        item_similarity_df = pd.DataFrame(
            item_similarity,
            index=self.user_item_matrix.columns,
            columns=self.user_item_matrix.columns
        )

        # 获取用户已评分的电影及评分
        user_ratings = self.user_item_matrix.loc[user_id]
        rated_movies = user_ratings[user_ratings > 0].index

        # 生成推荐
        recommendations = {}
        for movie, rating in user_ratings[rated_movies].items():
            similar_items = item_similarity_df[movie].sort_values(ascending=False)[1:11]

            for similar_movie, similarity in similar_items.items():
                if similar_movie not in rated_movies:
                    if similar_movie not in recommendations:
                        recommendations[similar_movie] = 0
                    recommendations[similar_movie] += similarity * rating

        # 按加权评分排序排序并返回前n个推荐
        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]

    def matrix_factorization(self, user_id, n_recommendations=10, n_components=20):
        """基于矩阵分解(SVD)的推荐"""
        # 应用SVD
        svd = TruncatedSVD(n_components=n_components)
        user_factors = svd.fit_transform(self.user_item_matrix)
        item_factors = svd.components_.T

        # 预测评分
        predicted_ratings = np.dot(user_factors, item_factors.T)
        predicted_df = pd.DataFrame(
            predicted_ratings,
            index=self.user_item_matrix.index,
            columns=self.user_item_matrix.columns
        )

        # 获取用户已评分的电影
        user_ratings = self.user_item_matrix.loc[user_id]
        rated_movies = user_ratings[user_ratings > 0].index

        # 生成推荐
        user_predictions = predicted_df.loc[user_id]
        recommendations = user_predictions.drop(rated_movies).sort_values(ascending=False)

        return list(recommendations.head(n_recommendations).index)

    def content_based(self, user_id, n_recommendations=10):
        if self.movie_features is None:
            raise ValueError("未提供电影特征数据")

        # 获取用户喜欢的电影（使用编码后的movieId）
        user_ratings = self.ratings[self.ratings['userId'] == user_id]
        liked_movies = user_ratings[user_ratings['rating'] >= 4]['movieId'].values
        if len(liked_movies) == 0:
            return []

        # 关键修复：通过tfidf_matrix的行数确定电影数量，生成与特征矩阵匹配的索引
        # 注意：tfidf_matrix的行数 = 全量电影数（与le_movie编码的总电影数一致）
        total_movies = self.movie_features.shape[0]  # 获取特征矩阵的行数（全量电影数）
        all_movie_ids = le_movie.classes_  # le_movie包含所有电影的编码映射，classes_是原始电影ID列表

        # 验证长度是否匹配（调试用，可删除）
        if len(all_movie_ids) != total_movies:
            raise ValueError(f"电影特征矩阵行数（{total_movies}）与le_movie中的电影数（{len(all_movie_ids)}）不匹配")

        # 仅提取用户喜欢的电影的特征向量索引
        liked_indices = []
        for movie_id in liked_movies:
            # 找到该电影在le_movie中的索引（即特征矩阵中的行索引）
            idx = np.where(le_movie.classes_ == movie_id)[0]
            if len(idx) > 0:
                liked_indices.append(idx[0])
        if not liked_indices:
            return []

        # 提取特征向量并计算相似度
        liked_movie_features = self.movie_features[liked_indices]
        movie_similarity = cosine_similarity(liked_movie_features, self.movie_features)

        # 生成推荐
        recommendations = {}
        for i in range(len(liked_indices)):
            similar_scores = movie_similarity[i]  # 长度=total_movies
            # 用全量电影ID作为索引（长度=total_movies，与similar_scores一致）
            similar_movies = pd.Series(
                similar_scores,
                index=all_movie_ids
            ).sort_values(ascending=False)[1:11]  # 排除自身

            for similar_movie, similarity in similar_movies.items():
                if similar_movie not in liked_movies:
                    recommendations[similar_movie] = recommendations.get(similar_movie, 0) + similarity

        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]

    def hybrid_recommender(self, user_id, n_recommendations=10, weights=[0.3, 0.3, 0.2, 0.2]):
        """混合推荐系统"""
        # 获取各种方法的推荐
        ub_recs = dict(self.user_based_cf(user_id, n_recommendations * 2))
        ib_recs = dict(self.item_based_cf(user_id, n_recommendations * 2))
        mf_recs = {movie: i + 1 for i, movie in enumerate(self.matrix_factorization(user_id, n_recommendations * 2))}
        cb_recs = dict(self.content_based(user_id, n_recommendations * 2))

        # 归一化分数
        def normalize(scores):
            if not scores:
                return {}
            max_score = max(scores.values())
            return {k: v / max_score for k, v in scores.items()}

        ub_norm = normalize(ub_recs)
        ib_norm = normalize(ib_recs)
        mf_norm = normalize(mf_recs)
        cb_norm = normalize(cb_recs)

        # 组合推荐
        recommendations = {}
        for movie in set(ub_norm.keys() | ib_norm.keys() | mf_norm.keys() | cb_norm.keys()):
            score = (
                    weights[0] * ub_norm.get(movie, 0) +
                    weights[1] * ib_norm.get(movie, 0) +
                    weights[2] * mf_norm.get(movie, 0) +
                    weights[3] * cb_norm.get(movie, 0)
            )
            recommendations[movie] = score

        # 返回前n个推荐
        return sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]


# 使用Surprise库实现的推荐算法评估
def evaluate_algorithms(ratings_data):
    """评估不同推荐算法的性能"""
    # 准备数据
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(ratings_data[['userId', 'movieId', 'rating']], reader)

    # 定义算法
    algorithms = {
        '基于用户的协同过滤': KNNBasic(sim_options={'user_based': True}),
        '基于物品的协同过滤': KNNBasic(sim_options={'user_based': False}),
        'SVD矩阵分解': SVD()
    }

    # 评估算法
    results = {}
    for name, algo in algorithms.items():
        print(f"评估 {name}...")
        cv_results = cross_validate(algo, data, measures=['RMSE', 'MAE'], cv=5, verbose=False)
        results[name] = {
            'RMSE': np.mean(cv_results['test_rmse']),
            'MAE': np.mean(cv_results['test_mae']),
            'Fit Time': np.mean(cv_results['fit_time']),
            'Test Time': np.mean(cv_results['test_time'])
        }

    # 输出结果
    results_df = pd.DataFrame(results).T
    print("\n评估结果:")
    print(results_df)

    return results_df
