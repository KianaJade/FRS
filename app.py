from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import joblib
import os
import scipy.sparse
from flask_cors import CORS

from make_recommend import recommend_for_new_user,load_or_init_recommender
from models.user import db, User, Rating
from recommender_systems import RecommenderSystem  # 复用推荐系统

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345678'
base_dir = os.path.abspath(os.path.dirname(__file__))# 获取当前文件所在目录的绝对路径
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "data", "user_ratings.db")}'# 拼接数据库文件的绝对路径
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(
    app,
    resources={r"/*": {  # 对所有路由生效
        "origins": "http://localhost:7000",  # 你的Vue前端地址
        "supports_credentials": True  # 允许携带Cookie
    }}
)

# 初始化数据库和登录管理
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 加载原有数据和推荐器
movies_df = pd.read_csv('data/movies.csv')  # 电影元数据
le_movie = joblib.load('data/processed/le_movie.pkl')  # 电影ID编码器
tfidf_matrix = scipy.sparse.load_npz('data/processed/tfidf_matrix.npz')
full_data = pd.read_csv('data/processed/full_data.csv')  # 原有评分数据
recommender = load_or_init_recommender()  # 初始化推荐器

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# 注册页面
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    if User.query.filter_by(username=username).first():
        flash('用户名已存在')
        return jsonify({
            "status": "error",
            "message": "用户名已存在"
        })

    # 创建新用户
    new_user = User(
        username=username,
        email=email,
        password=password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "status": "success",
        "message":"注册成功"
    })


# 登录页面
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if not user or password != user.password:
        flash('用户名或密码错误')
        return jsonify({
            "status": "error",
            "message":"用户名或密码错误"
        })

    login_user(user)
    return jsonify({
        "status": "success",
        "message":"登录成功"
    })


# 电影列表与评分页面
@app.route('/moviesList', methods=['GET', 'POST'])
@login_required
def movie_list():
    if request.method == 'POST':
        # 处理用户评分提交（保持原逻辑不变）
        movie_id = int(request.form['movie_id'])
        rating = float(request.form['rating'])

        existing_rating = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        if existing_rating:
            existing_rating.rating = rating
        else:
            new_rating = Rating(user_id=current_user.id, movie_id=movie_id, rating=rating)
            db.session.add(new_rating)
        db.session.commit()
        return jsonify({"status": "success", "message": "评分成功！"})  # 提交评分后返回JSON

    # 处理GET请求：分页返回热门电影JSON数据
    # 获取分页参数，默认第一页
    page = request.args.get('page', 1, type=int)
    per_page = 8  # 每页8条数据

    # 1. 从全量评分数据中计算每部电影的评分次数
    movie_ratings_count = full_data['movieId'].value_counts().reset_index()
    movie_ratings_count.columns = ['movieId', 'rating_count']

    # 2. 转换为原始电影ID（因为full_data中是编码后的ID）
    movie_ratings_count['original_movieId'] = le_movie.inverse_transform(movie_ratings_count['movieId'])

    # 3. 合并电影元数据并按评分次数排序
    popular_movies = pd.merge(
        movies_df,
        movie_ratings_count,
        left_on='movieId',
        right_on='original_movieId',
        how='inner'
    ).sort_values(by='rating_count', ascending=False)

    # 4. 计算总页数和当前页数据
    total = len(popular_movies)
    total_pages = (total + per_page - 1) // per_page  # 向上取整计算总页数
    # 分页切片（注意：pandas索引从0开始，page从1开始）
    start = (page - 1) * per_page
    end = start + per_page
    #current_page_data = popular_movies.iloc[start:end].to_dict('records')

    # 在movie_list函数的GET请求处理部分，修改current_page_data的生成逻辑
    # 原代码：
    # current_page_data = popular_movies.iloc[start:end].to_dict('records')

    # 新代码：
    # 1. 获取当前用户对当前页电影的评分记录
    current_page_movie_ids = popular_movies.iloc[start:end]['original_movieId'].tolist()
    # 6. 查询用户对这些电影的评分（使用in_而非movie_id_in）
    user_ratings = Rating.query.filter(
        Rating.user_id == current_user.id,
        Rating.movie_id.in_(current_page_movie_ids)  # 正确使用in_方法
    ).all()

    # 2. 转换为字典便于查询 {movie_id: rating}
    rating_dict = {r.movie_id: r.rating for r in user_ratings}

    # 3. 为每条电影数据添加用户评分
    current_page_data = []
    for _, row in popular_movies.iloc[start:end].iterrows():
        movie_data = row.to_dict()
        # 添加用户评分（如果没有则为None或0）
        movie_data['user_rating'] = rating_dict.get(row['movieId'], None)
        current_page_data.append(movie_data)

    # 5. 转换为JSON格式返回（包含分页信息和当前页数据）
    return jsonify({
        "status": "success",
        "pagination": {
            "total": total,          # 总条数
            "total_pages": total_pages,  # 总页数
            "current_page": page,    # 当前页
            "per_page": per_page     # 每页条数
        },
        "data": current_page_data
    })


@app.route('/recommendations')
@login_required
def recommendations():
    # 获取当前用户的评分记录
    user_ratings = Rating.query.filter_by(user_id=current_user.id).all()
    if not user_ratings:
        # 新用户（无评分）：返回热门电影
        recs = recommend_for_new_user(recommender)
    else:
        # 老用户：转换评分格式为推荐器所需的编码ID
        user_rating_dict = {
            r.movie_id: r.rating for r in user_ratings
        }
        # 调用推荐器（需将原始movieId转换为编码ID）
        encoded_ratings = {
            le_movie.transform([mid])[0]: rating
            for mid, rating in user_rating_dict.items()
            if mid in le_movie.classes_
        }
        # 生成混合推荐
        recs = recommender.hybrid_recommender(
            user_id=current_user.id,
            n_recommendations=10
        )

    # 转换推荐结果为电影信息
    rec_movie_ids = [mid for mid, _ in recs]
    original_ids = le_movie.inverse_transform(rec_movie_ids)
    recommended_movies = movies_df[movies_df['movieId'].isin(original_ids)]

    # 返回JSON格式数据
    return jsonify({
        "status": "success",
        "data": recommended_movies[['movieId', 'title', 'genres']].to_dict('records')
    })


# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({
        "status": "success",
    })


if __name__ == '__main__':
    # 确保data文件夹存在
    if not os.path.exists('data'):
        os.makedirs('data')
    with app.app_context():
        db.create_all()  # 初始化数据库表
    app.run(debug=True)