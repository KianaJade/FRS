import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy.sparse
import joblib

# 加载所有原始数据（不立即抽样，先保留完整电影集）
ratings = pd.read_csv('data/ratings.csv')
movies = pd.read_csv('data/movies.csv')
tags = pd.read_csv('data/tags.csv')
links = pd.read_csv('data/links.csv')

# --------------------------
# 1. 处理电影数据（保留全部电影）
# --------------------------
# 清洗电影数据（确保所有电影都被纳入）
movies = movies.dropna(subset=['movieId', 'title', 'genres']).drop_duplicates(subset='movieId')
all_movie_ids = movies['movieId'].unique()  # 全部电影的ID列表

# 处理标签数据（合并到电影表，确保所有电影都有标签字段）
# 关键修复：将tag列转换为字符串并填充空值，避免拼接时出现float类型
tags['tag'] = tags['tag'].astype(str).fillna('')
movie_tags = tags.groupby('movieId')['tag'].apply(lambda x: ', '.join(x)).reset_index()
# 用所有电影ID左连接标签（确保无标签的电影也保留，填充空字符串）
movie_data = pd.merge(movies, movie_tags, on='movieId', how='left')
movie_data['tag'] = movie_data['tag'].fillna('')  # 无标签的电影用空字符串填充

# --------------------------
# 2. 用户抽样（仅对交互数据抽样，不影响电影集）
# --------------------------
sample_fraction = 0.01  # 抽样比例
np.random.seed(42)

# 对用户抽样（仅影响评分和标签的用户范围，不影响电影集）
unique_users = ratings['userId'].unique()
sampled_users = np.random.choice(unique_users, size=int(len(unique_users) * sample_fraction), replace=False)

# 过滤评分和标签数据（仅保留抽样用户的交互）
ratings = ratings[ratings['userId'].isin(sampled_users)]
tags = tags[tags['userId'].isin(sampled_users)]

# --------------------------
# 3. 合并数据并编码（确保编码基于全部电影）
# --------------------------
# 合并评分与电影数据（仅保留抽样用户的交互，但保留所有电影的元数据）
full_data = pd.merge(ratings, movie_data, on='movieId', how='inner')

# 对用户ID编码（仅针对抽样用户）
le_user = LabelEncoder()
full_data['userId'] = le_user.fit_transform(full_data['userId'])

# 对电影ID编码（关键：基于全部电影ID，而非仅抽样用户交互过的电影）
le_movie = LabelEncoder()
le_movie.fit(all_movie_ids)  # 用所有电影ID训练编码器
full_data['movieId'] = le_movie.transform(full_data['movieId'])  # 转换交互数据中的电影ID

# --------------------------
# 4. 生成TF-IDF矩阵（基于全部电影的特征）
# --------------------------
# 基于全部电影的标签生成TF-IDF（行数 = 全部电影数）
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movie_data['tag'])  # 使用包含所有电影的movie_data

# --------------------------
# 5. 时间特征处理
# --------------------------
full_data['timestamp'] = pd.to_datetime(full_data['timestamp'], unit='s')
full_data['rating_year'] = full_data['timestamp'].dt.year

# --------------------------
# 6. 验证数据一致性（关键检查）
# --------------------------
print(f"全部电影数量: {len(all_movie_ids)}")
print(f"TF-IDF矩阵行数（电影特征数）: {tfidf_matrix.shape[0]}")
print(f"标签编码器电影数: {len(le_movie.classes_)}")

if tfidf_matrix.shape[0] != len(le_movie.classes_):
    raise ValueError("数据不一致：TF-IDF矩阵与标签编码器的电影数量不匹配！")

# --------------------------
# 7. 保存数据
# --------------------------
full_data.to_csv('data/processed/full_data.csv', index=False)
scipy.sparse.save_npz('data/processed/tfidf_matrix.npz', tfidf_matrix)
joblib.dump(le_user, 'data/processed/le_user.pkl')
joblib.dump(le_movie, 'data/processed/le_movie.pkl')
joblib.dump(tfidf, 'data/processed/tfidf_vectorizer.pkl')

# 输出抽样后交互数据的统计信息
print(f"抽样后用户-电影交互数据形状: {full_data.shape}")
print(f"抽样后用户数量: {full_data['userId'].nunique()}")
print(f"抽样后交互涉及的电影数量: {full_data['movieId'].nunique()}")