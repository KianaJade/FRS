import os
import pandas as pd
import scipy.sparse
import joblib
from recommender_systems import RecommenderSystem

# 加载处理后的数据
full_data = pd.read_csv('data/processed/full_data.csv')
tfidf_matrix = scipy.sparse.load_npz('data/processed/tfidf_matrix.npz')
le_movie = joblib.load('data/processed/le_movie.pkl')  # 加载电影标签编码器

# 关键：添加数据一致性校验
print(f"TF-IDF矩阵行数（特征矩阵电影数）: {tfidf_matrix.shape[0]}")
print(f"标签编码器中的电影数: {len(le_movie.classes_)}")

# 校验不通过时抛出明确信息并终止
if tfidf_matrix.shape[0] != len(le_movie.classes_):
    raise ValueError(
        f"数据不一致：特征矩阵电影数（{tfidf_matrix.shape[0]}）与标签编码器电影数（{len(le_movie.classes_)}）不匹配！"
        "\n请重新生成tfidf_matrix和le_movie，确保它们基于同一批电影数据"
    )

# 新增：定义推荐器保存路径
RECOMMENDER_SAVE_PATH = 'data/processed/recommender_model.pkl'

# 新增：加载已保存的推荐器，若不存在则初始化并保存
def load_or_init_recommender():
    if os.path.exists(RECOMMENDER_SAVE_PATH):
        print("加载已保存的推荐器...")
        return joblib.load(RECOMMENDER_SAVE_PATH)
    else:
        print("初始化新的推荐器...")
        recommender = RecommenderSystem(
            ratings_data=full_data,
            movie_features=tfidf_matrix,
            le_movie=le_movie
        )
        # 保存初始化后的推荐器
        joblib.dump(recommender, RECOMMENDER_SAVE_PATH)
        print(f"推荐器已保存至 {RECOMMENDER_SAVE_PATH}")
        return recommender

def recommend_for_new_user(
        recommender=None,
        new_user_ratings=None,  # 新用户的初始评分字典，格式：{原始movieId: 评分}
        n_recommendations=10,
        popular_threshold=50  # 热门电影的最低评分次数
):
    """为新用户推荐电影（处理冷启动问题）"""
    # 1. 若新用户无任何评分，返回热门电影
    if not new_user_ratings:
        # 计算电影评分次数和平均评分（筛选热门且质量高的电影）
        movie_popularity = full_data.groupby('movieId').agg(
            rating_count=('rating', 'count'),
            avg_rating=('rating', 'mean')
        )
        # 筛选热门电影（评分次数≥threshold，平均评分≥3.5）
        popular_movies = movie_popularity[
            (movie_popularity['rating_count'] >= popular_threshold) &
            (movie_popularity['avg_rating'] >= 3.5)
            ].sort_values(by=['rating_count', 'avg_rating'], ascending=False)

        # 取前n个热门电影
        top_popular = popular_movies.head(n_recommendations).index.tolist()
        # 转换为 (电影ID, 推荐分数) 格式（分数用评分次数归一化）
        max_count = popular_movies['rating_count'].max()
        return [(mid, cnt / max_count) for mid, cnt in
                zip(top_popular, popular_movies.loc[top_popular, 'rating_count'])]

    # 2. 若新用户有初始评分，基于内容推荐相似电影
    else:
        # 将新用户的原始movieId转换为编码后的ID
        try:
            encoded_movies = le_movie.transform(list(new_user_ratings.keys()))
        except ValueError as e:
            raise ValueError(f"部分电影ID不在训练集中：{e}")

        # 为新用户创建临时评分数据（用户ID用一个未出现的值，如max_id+1）
        new_user_id = full_data['userId'].max() + 1 if not full_data.empty else 0
        temp_ratings = pd.DataFrame({
            'userId': [new_user_id] * len(encoded_movies),
            'movieId': encoded_movies,
            'rating': list(new_user_ratings.values())
        })

        # 将临时数据加入推荐器的评分数据中
        temp_full_data = pd.concat([full_data, temp_ratings], ignore_index=True)
        temp_recommender = RecommenderSystem(
            ratings_data=temp_full_data,
            movie_features=tfidf_matrix,
            le_movie=le_movie
        )

        # 使用基于内容的推荐（依赖初始评分的电影特征）
        return temp_recommender.content_based(
            user_id=new_user_id,
            n_recommendations=n_recommendations
        )

def recommend_for_old_user(
        recommender = None,
        user_id = 10,
        n_recommendations = 10
):
    # 获取混合推荐结果
     return recommender.hybrid_recommender(
        user_id=user_id,
        n_recommendations=n_recommendations,
        weights=[0.25, 0.25, 0.25, 0.25]
    )

# 加载原始电影数据
movies = pd.read_csv('data/movies.csv')
# 修正电影名称映射函数：使用le_movie转换编码ID为原始ID
def get_movie_names(recommendations, movies_df, le_movie):
    rec_movie_ids = [movie_id for movie_id, _ in recommendations]
    # 将编码后的movieId转换为原始movieId
    original_ids = le_movie.inverse_transform(rec_movie_ids)
    # 根据原始ID匹配电影名称
    rec_movies = movies_df[movies_df['movieId'].isin(original_ids)]
    # 按推荐顺序排序
    rec_movies = rec_movies.set_index('movieId').reindex(original_ids).reset_index()
    return rec_movies[['movieId', 'title']]




if __name__ == "__main__":
    # 初始化/加载推荐器（替换原来的直接初始化）
    recommender = load_or_init_recommender()
    #hybrid_recs = recommend_for_new_user(recommender)
    hybrid_recs = recommend_for_old_user(recommender,25,5)
    print("混合推荐结果（电影ID, 推荐分数）：")
    for movie_id, score in hybrid_recs:
        print(f"{movie_id}: {score:.4f}")

    # 转换混合推荐结果为电影名称（传入le_movie）
    rec_movie_names = get_movie_names(hybrid_recs, movies, le_movie)
    print("\n推荐电影名称：")
    print(rec_movie_names['title'].tolist())