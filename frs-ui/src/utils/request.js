import axios from 'axios'
//import Vue from "vue";

// 关键配置：允许跨域请求携带Cookie
axios.defaults.withCredentials = true

const request = axios.create({
    baseURL:'http://localhost:5000',//Vue.prototype.$baseUrl,
    timeout:30000
})

request.interceptors.request.use(function (config) {
    //config.headers['Content-Type']='application/json;charset=utf-8';
    //config.headers['token'] =localStorage.getItem('msToken') ;
    // 在发送请求之前做些什么
    return config;
}, function (error) {
    // 对请求错误做些什么

    console.error('request error:'+error);
    return Promise.reject(error);
});

// 添加响应拦截器
request.interceptors.response.use(function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么

    let res = response.data;
    if(typeof res === 'string'){
        res = res ? JSON.parse(res):res;
    }
    return res;
}, function (error) {
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    return Promise.reject(error);
});

export default request;