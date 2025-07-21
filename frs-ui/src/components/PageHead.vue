<template>
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
        <el-button type="text" @click="handleSelect">退出登录</el-button>
      </template>
      <el-button type="text" v-else @click="goToLogin">未登录</el-button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageHead',
  components: {

  },
  props: {
    activeMenu:{
      type: String,
      default: '1',
    },
  },
  data() {
    return {
      loginStatus: 'true',
      username:''
    }
  },
  methods: {
    goToLogin(){
      this.$router.push('/login');
    },
    handleSelect(){

    }
  },
  mounted() {
    this.loginStatus = sessionStorage.getItem('login') || '';
    this.username = sessionStorage.getItem('username') || '' ;
  }
}
</script>

<style scoped>
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