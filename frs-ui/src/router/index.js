import Vue from 'vue'
import VueRouter from 'vue-router'

Vue.use(VueRouter)

const routes = [
  {
    path: '/login',
    name: 'login',
    component:()=> import('../views/Login.vue'),
    meta:{
      title:'登录',
      hideAppPage: true,
    }
  },
  {
    path: '/register',
    name: 'register',
    component:()=> import('../views/Register.vue'),
    meta:{
      title:'注册',
      hideAppPage: true,
    }
  },
]

const router = new VueRouter({
  mode:'history',
  routes
})

router.beforeEach((to, from, next) => {
  if (to.fullPath === from.fullPath) {
    // 如果目标路径和当前路径相同，阻止导航
    return next(false)
  }else{
    return next();
  }
});

export default router
