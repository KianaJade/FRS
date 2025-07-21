<template>
  <div>
    <div style="height: 64px"></div>
    <div class="hot-movies">
      <div style="margin-left: 30%">
        <el-table
            :data="movies"
            height="600"
            border
            style="width: 100%">
          <el-table-column
              prop="title"
              label="名称"
              width="180">
          </el-table-column>
          <el-table-column
              prop="genres"
              label="类型"
              width="180">
          </el-table-column>
          <el-table-column
              prop="rating_count"
              label="点评数"
              width="80">
          </el-table-column>
          <el-table-column
              label="我的评分"
              width="280">
            <template slot-scope="scope">
              <div style="display: flex">
                <el-rate v-model="movies[scope.$index].user_rating"></el-rate>
                <el-button plain size="mini" type="primary" @click="rating(scope.$index)">提交</el-button>
              </div>
              </template>
          </el-table-column>
        </el-table>
      </div>
      <div>
        <div style="margin-top: 50px;margin-left: 20px">
          <h3>当前页数:</h3>
          <el-input-number v-model="page"
                           @change="getMovies"
                           :min="1" :max="2168" :step="1"
                           label="描述文字"></el-input-number>
          <div style="display: flex;margin-top: 5px">
            <el-button type="primary" @click="prePage">上一页</el-button>
            <el-button type="primary" @click="nextPage">下一页</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'HotMovies',
  components: {
  },
  data() {
    return {
      activeMenu:1,
      movies:[],
      page:1,
    }
  },
  methods: {
    getMovies(){
      this.$request({
        method: 'get',
        url: 'http://localhost:5000/moviesList',
        headers: {
          'Content-Type': 'application/json;charset=utf-8'
        },
        params: {
          page: this.page,
        }
      }).then(res=>{
        if(res.status === 'success'){
          this.movies = res.data;
        }else{
          this.$message.error(res.message);
        }
      }).catch(()=>{
        this.$message.error('错误！获取电影列表失败');
      })
    },
    rating(index){
      let form  = new FormData();
      form.append("movie_id",this.movies[index].original_movieId)
      form.append('rating',this.movies[index].user_rating)
      this.$request({
        method: 'post',
        url: 'http://localhost:5000/moviesList',
        headers: {
          'Content-Type': 'multipart/form-data;',
        },
        data: form,
      }).then(res=>{
        if(res.status === 'success'){
          this.$message.success("评分成功")
        }else{
          this.$message.error(res.message);
        }
      }).catch(()=>{
        this.$message.error('错误！评分失败');
      })
    },
    prePage(){
      if(this.page <= 1){
        return;
      }
      this.page --;
      this.getMovies()
    },
    nextPage(){
      if(this.page >= 2168){
        return;
      }
      this.page ++;
      this.getMovies()
    },
  },
  mounted() {
    this.getMovies()
  }
}
</script>

<style scoped>
.hot-movies {
  display: flex;
}
</style>