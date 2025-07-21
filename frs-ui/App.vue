<template>
  <div id="app">
    <router-view/>
    <div v-if="!$route.meta.hideAppPage">
      <div>
        <div class="page-head">
          <div class="page-head-logo">
            <div style="display: flex;margin-top: 5px;margin-left: 20px">
              <el-tag>电</el-tag>
              <el-tag type="success">影</el-tag>
              <el-tag type="info">推</el-tag>
              <el-tag type="warning">荐</el-tag>
              <el-tag type="danger">器</el-tag>
            </div>
          </div>
          <div class="page-head-menu">
            <div style="margin-left: 150px">
              <el-menu :default-active="activeMenu"
                       class="el-menu-demo" mode="horizontal" @select="handleSelect">
                <el-menu-item index="1">热门电影</el-menu-item>
                <el-menu-item index="2">电影推荐</el-menu-item>
              </el-menu>
            </div>
          </div>

          <div class="page-head-user">
            <template v-if="loginStatus === 'true'">
              <h5>{{ username }}</h5>
              <el-button style="margin-left: 10px"
                  type="text" @click="logOut">退出登录</el-button>
            </template>
            <el-button type="text" v-else @click="goToLogin">未登录</el-button>
          </div>
        </div>
        <HotMovies v-if="activeMenu === '1'"/>
        <Recommendations v-else-if="activeMenu === '2'"/>
      </div>
    </div>
  </div>
</template>

<script>
import HotMovies from "@/components/HotMovies.vue";
import Recommendations from "@/components/Recommendations.vue";

export default {
  name: 'appView',
  components: {
    HotMovies,Recommendations
  },
  data() {
    return {
      activeMenu:'1',
      username:'',
      loginStatus: 'false',
    }
  },
  methods: {
    goToLogin(){
      this.$router.push('/login');
    },
    handleSelect(key) {
      this.activeMenu = key;
    },
    logOut(){
      this.$request({
        method: 'get',
        url: 'http://localhost:5000/logout',
        headers: {
          'Content-Type': 'multipart/form-data;',
        },
      }).then((res)=>{
        if(res.status === 'success'){
          this.$message.success("退出登录");
          sessionStorage.setItem('login','false')
          sessionStorage.setItem('username','')
          this.$router.push('/login');
        }else{
          this.$message.error(res.message);
        }
      });
    }
  },
  mounted() {
    this.loginStatus = sessionStorage.getItem('login') || '';
    this.username = sessionStorage.getItem('username') || '' ;
    if(this.loginStatus !== 'true'){
      this.goToLogin();
    }
  },
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.page-head {
  position: fixed;
  z-index: 1002;
  height: 64px;
  width: 100%;
  display: flex;
  box-shadow: 0 2px 4px #00000014;
}
.page-head-menu {
  width: 50%;
  height: 100%;
  justify-content: space-between;
  align-items: center;
}
.page-head-logo {
  width: 25%;
}
.page-head-user {
  width: 25%;
  display: flex;
}
</style>