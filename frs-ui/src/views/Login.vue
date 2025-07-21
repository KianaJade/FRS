<template>
  <div class="login">
    <div class="loginBox">
      <el-form label-width="80px"
               :hide-required-asterisk="true"
               style="height: 95%;width: 80%" :model="loginForm"
               :rules="loginRules" ref="loginForm">
        <h3 style="height: 5%;margin-left: 40px" class="title">电影推荐器</h3>
        <h4 style="height: 5%;color: #5F8AD3;margin-left: 40px" class="title">欢迎登录本系统</h4>
        <el-form-item label="用户名" tyle="height: 5%"  prop="userName">
          <el-input prefix-icon="el-icon-user"
                    style="width: 100%"
                    v-model="loginForm.userName"
                    type="text" auto-complete="off" placeholder="请输入用户名">
          </el-input>
        </el-form-item>
        <el-form-item label="密码"  prop="password">
          <el-input
              prefix-icon="el-icon-lock"
              style="width: 100%"
              show-password
              v-model="loginForm.password"
              type="password"
              auto-complete="off"
              placeholder="请输入密码"
          >
          </el-input>
        </el-form-item>
        <el-form-item   prop="code">
          <div style="display: flex;flex-direction:row;height: 20%">
            <div style="width: 50%">
              <el-input prefix-icon="el-icon-s-opportunity"
                        style="width: 150px;height: 10%; align-items:center;"
                        v-model="loginForm.code"
                        type="text"
                        auto-complete="off"
                        placeholder="请输入验证码">
              </el-input>
            </div>
            <div style="width: 50%;height: 5%">
              <valid-code style="height: 25px" @update:value="getCode"></valid-code>
            </div>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary"
                     style="width: 100%;height: 5%"
                     @click="login">
            登录
          </el-button>
        </el-form-item>
        <el-form-item>
          <hr style="width: 100%;color: #EFEFF5">
          <div @click="$router.push('/register')" style="margin-left: 40%;color: #5F8AD3;width: fit-content ;cursor: pointer">注册账号</div>
         </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import ValidCode from "@/components/ValidCode.vue";
export default {
  name: 'loginView',
  components: {
    ValidCode
  },
  data() {
    return {
      cookiePassword: "",
      loginForm: {
        userName: "",
        password: "",
        rememberMe: false,
        code: "",
        time: "",
        realKey: ""
      },
      loginRules: {
        userName: [{ required: true, trigger: "blur", message: "用户名不能为空" }],
        password: [{ required: true, trigger: "blur", message: "密码不能为空" }],
        code: [{ required: true, trigger: "blur", message: "验证码不能为空", min: 4,max:4 }]
      },
      loading: false,
      redirect: undefined
    }
  },
  methods: {
    getCode(code){
      this.loginForm.realKey=code.toLowerCase();
    },
    login(){
      if(this.loginForm.userName.indexOf(" ")!==-1){
        this.$message.error('用户名中不能包含空格')
        return
      }
      if(this.loginForm.password.indexOf(" ")!==-1){
        this.$message.error('密码中不能包含空格')
        return
      }
      this.$refs["loginForm"].validate((valid) => {
        if (valid) {
          if (this.loginForm.realKey !== this.loginForm.code.toLowerCase()){
            this.$message.error("验证码错误");
          }else{
            let form  = new FormData();
            form.append("username",this.loginForm.userName)
            form.append("password",this.loginForm.password)
            this.$request({
              method: 'post',
              url: 'http://localhost:5000/login',
              headers: {
                'Content-Type': 'multipart/form-data;',
              },
              data: form,
            }).then((res)=>{
              if(res.status === 'success'){
                sessionStorage.setItem('login','true')
                sessionStorage.setItem('username',this.loginForm.userName)
                this.$message.success("登录成功");
                this.$router.push('/');
              }else{
                this.$message.error(res.message);
              }
            });
          }
        } else {
          console.log('error submit!!');
          return false;
        }
      });
    }
  },
  mounted() {
  },
}
</script>

<style scoped>
.login{
  height: 97vh;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 加载背景图 */
  background-image: url(../assets/luoTianYi.webp);
  /* 背景图垂直、水平均居中 */
  background-position: center center;
  /* 背景图不平铺 */
  background-repeat: no-repeat;
  /* 当内容高度大于图片高度时，背景图像的位置相对于viewport固定 */
  background-attachment: fixed;
  /* 让背景图基于容器大小伸缩 */
  background-size: cover;
  /* 设置背景颜色，背景图加载过程中会显示背景色 */
  background-color: #464646;
}
.loginBox{
  border: 1px solid #F1F5F9;
  width: 420px;
  height: 510px;
  border-radius: 10px;
  overflow: hidden;
  background-color:#F1F5F9;
}
</style>