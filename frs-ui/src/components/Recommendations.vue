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
              width="280">
          </el-table-column>
        </el-table>
      </div>
      <div style="margin-left: 20px;margin-top: 50px">
        <el-button type="primary"
                   plain
                   @click="getMovies"
                   icon="el-icon-refresh-left">刷新推荐</el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RecmdMovies',
  components: {
  },
  data() {
    return {
      activeMenu:1,
      movies:[],
    }
  },
  methods: {
    getMovies(){
      this.$request({
        method: 'get',
        url: 'http://localhost:5000/recommendations',
        headers: {
          'Content-Type': 'application/json;charset=utf-8'
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