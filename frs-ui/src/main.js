import Vue from 'vue'
import App from './App.vue'
import router from './router'
import request from "@/utils/request";
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';

Vue.config.productionTip = false
Vue.use(ElementUI);

Vue.prototype.$request=request
Vue.prototype.$baseUrl=process.env.VUE_APP_BASEURL

router.beforeEach((to,from,next) =>{
  if(to.meta.title){
    document.title = to.meta.title
  }
  next();
})

new Vue({
  router,
  render: h => h(App)
}).$mount('#app')
