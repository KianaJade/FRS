import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.sparse
import joblib
from sklearn.model_selection import train_test_split

from recommender_systems import RecommenderSystem, evaluate_algorithms

# 加载处理后的数据
full_data = pd.read_csv('data/processed/full_data.csv')
tfidf_matrix = scipy.sparse.load_npz('data/processed/tfidf_matrix.npz')
le_user = joblib.load('data/processed/le_user.pkl')
le_movie = joblib.load('data/processed/le_movie.pkl')
tfidf = joblib.load('data/processed/tfidf_vectorizer.pkl')

# 准备评估数据
def prepare_evaluation_data(ratings, test_size=0.2):
    """将数据分为训练集和测试集用于评估"""
    # 确保每个用户在测试集中至少有一个评分
    unique_users = ratings['userId'].unique()
    train_data = []
    test_data = []

    for user in unique_users:
        user_ratings = ratings[ratings['userId'] == user]
        if len(user_ratings) > 1:
            # 为每个用户保留一些评分作为测试
            user_train, user_test = train_test_split(user_ratings, test_size=test_size, random_state=42)
            train_data.append(user_train)
            test_data.append(user_test)
        else:
            # 如果用户只有一个评分，全部放入训练集
            train_data.append(user_ratings)

    return pd.concat(train_data), pd.concat(test_data)


# 评估推荐质量
def evaluate_recommendations(recommender, test_data, n_recommendations=10):
    """评估推荐系统的准确率、召回率等指标"""
    precision_scores = []
    recall_scores = []
    f1_scores = []

    unique_users = test_data['userId'].unique()

    for user_id in unique_users:
        # 获取用户在测试集中喜欢的电影(评分>=4)
        user_test = test_data[test_data['userId'] == user_id]
        liked_movies = set(user_test[user_test['rating'] >= 4]['movieId'])

        if len(liked_movies) == 0:
            continue

        # 获取推荐
        recommendations = recommender.hybrid_recommender(user_id, n_recommendations)
        recommended_movies = set([movie for movie, _ in recommendations])

        # 计算准确率和召回率
        intersection = liked_movies & recommended_movies
        precision = len(intersection) / len(recommended_movies) if recommended_movies else 0
        recall = len(intersection) / len(liked_movies) if liked_movies else 0

        # 计算F1分数
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
        else:
            f1 = 0

        precision_scores.append(precision)
        recall_scores.append(recall)
        f1_scores.append(f1)

    # 计算覆盖率
    all_movies = set(recommender.ratings['movieId'].unique())
    all_recommendations = set()

    # 为多个用户生成推荐以计算覆盖率
    sample_users = np.random.choice(unique_users, min(100, len(unique_users)), replace=False)
    for user_id in sample_users:
        recommendations = recommender.hybrid_recommender(user_id, n_recommendations)
        all_recommendations.update([movie for movie, _ in recommendations])

    coverage = len(all_recommendations) / len(all_movies) if all_movies else 0

    return {
        'Precision': np.mean(precision_scores),
        'Recall': np.mean(recall_scores),
        'F1': np.mean(f1_scores),
        'Coverage': coverage
    }


# 模型参数调优
def optimize_hybrid_weights(recommender, test_data):
    """优化混合推荐系统的权重参数"""
    # 尝试不同的权重组合
    weight_combinations = [
        [0.4, 0.4, 0.1, 0.1],  # 更侧重协同过滤
        [0.1, 0.1, 0.4, 0.4],  # 更侧重内容和矩阵分解
        [0.25, 0.25, 0.25, 0.25],  # 平均权重
        [0.3, 0.2, 0.3, 0.2],  # 平衡协同过滤和矩阵分解
        [0.2, 0.3, 0.2, 0.3]  # 平衡协同过滤和内容推荐
    ]

    best_score = -1
    best_weights = None

    for weights in weight_combinations:
        # 临时修改权重
        def temp_hybrid(user_id, n_recs=10):
            return recommender.hybrid_recommender(user_id, n_recs, weights)

        # 创建临时推荐器
        class TempRecommender:
            def __init__(self, rec_func):
                self.rec_func = rec_func
                self.ratings = recommender.ratings

            def hybrid_recommender(self, user_id, n_recs=10):
                return self.rec_func(user_id, n_recs)

        temp_rec = TempRecommender(temp_hybrid)

        # 评估
        metrics = evaluate_recommendations(temp_rec, test_data)
        current_score = metrics['F1']

        # 记录最佳权重
        if current_score > best_score:
            best_score = current_score
            best_weights = weights

    return best_weights, best_score


# 结果可视化
def visualize_results(algorithm_results, metric_results):
    """可视化不同算法的性能指标"""
    # 绘制RMSE和MAE对比
    plt.figure(figsize=(12, 6))
    results_df = pd.DataFrame(algorithm_results).T

    ax = results_df[['RMSE', 'MAE']].plot(kind='bar')
    plt.title('不同算法的预测误差对比')
    plt.ylabel('误差值')
    plt.xlabel('推荐算法')
    plt.xticks(rotation=45)

    # 在柱状图上添加数值标签
    for p in ax.patches:
        ax.annotate(f'{p.get_height():.4f}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 10), textcoords='offset points')

    plt.tight_layout()
    plt.show()

    # 绘制准确率、召回率和F1分数
    plt.figure(figsize=(10, 6))
    metrics_df = pd.DataFrame([metric_results])
    metrics_df = metrics_df[['Precision', 'Recall', 'F1']].T

    ax = metrics_df.plot(kind='bar', color=['blue', 'green', 'red'])
    plt.title('混合推荐系统的质量指标')
    plt.ylabel('分数')
    plt.xlabel('评估指标')
    plt.xticks(rotation=0)

    # 添加数值标签
    for p in ax.patches:
        ax.annotate(f'{p.get_height():.4f}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 10), textcoords='offset points')

    plt.tight_layout()
    plt.show()

    # 绘制覆盖率
    plt.figure(figsize=(8, 6))
    plt.bar(['覆盖率'], [metric_results['Coverage']], color='purple')
    plt.title('推荐系统的覆盖率')
    plt.ylabel('比例')
    plt.ylim(0, 1)

    # 添加数值标签
    plt.text(0, metric_results['Coverage'] + 0.05,
             f'{metric_results["Coverage"]:.2%}',
             ha='center')

    plt.tight_layout()
    plt.show()


# 主函数：运行完整的分析流程
def run_analysis(ratings_data, movie_features):
    """运行完整的推荐系统分析流程"""
    # 分割训练集和测试集
    train_data, test_data = prepare_evaluation_data(ratings_data)

    # 创建推荐器实例
    recommender = RecommenderSystem(train_data, movie_features, le_movie)  # 补充le_movie

    # 评估不同算法
    print("评估各个推荐算法的性能...")
    algo_results = evaluate_algorithms(train_data)

    # 优化混合推荐系统的权重
    print("\n优化混合推荐系统的权重...")
    best_weights, best_score = optimize_hybrid_weights(recommender, test_data)
    print(f"最佳权重: {best_weights}, 对应的F1分数: {best_score:.4f}")

    # 评估最终混合模型
    print("\n评估最终混合推荐系统...")
    metrics = evaluate_recommendations(recommender, test_data)
    print("混合推荐系统评估指标:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

    # 可视化结果
    visualize_results(algo_results, metrics)

    # 返回最佳模型和结果
    return recommender, best_weights, algo_results, metrics