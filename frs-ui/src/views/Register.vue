<template>
  <div class="loginBack" style="height: 100vh;display: flex;align-items: center;justify-content: center;">

    <div class="loginBox">
      <h3 style="height: 5%" class="title">电影推荐器</h3>
      <h4 style="height: 5%;color: #5F8AD3" class="title">欢迎注册本系统</h4>
      <el-form label-width="80px" :hide-required-asterisk="true" style="height: 95%;width: 80%" :model="registerForm" :rules="registerRules" ref="registerForm">
        <el-form-item label="用户名" tyle="height: 5%"  prop="userName">
          <!--                    <div style="height: 5%; display: flex;flex-direction:row;">-->
          <!--                      <div style="width: 80px;">账号</div>-->
          <el-input prefix-icon="el-icon-user" style="width: 100%" v-model="registerForm.userName" type="text" auto-complete="off" placeholder="请输入用户名">
            <!--                      <svg-icon slot="prefix" icon-class="user" class="el-input__icon input-icon" />-->
          </el-input>
          <!--                     </div>-->
        </el-form-item>
        <el-form-item label="密码"  prop="password">
          <el-input
              prefix-icon="el-icon-lock"
              style="width: 100%"
              show-password
              v-model="registerForm.password"
              type="password"
              auto-complete="off"
              placeholder="请输入密码"
          >
            <!--                  <svg-icon slot="prefix" icon-class="password" class="el-input__icon input-icon" />-->
          </el-input>
        </el-form-item>
        <el-form-item label="确认密码"  prop="passwordConfirm">
          <el-input
              prefix-icon="el-icon-lock"
              style="width: 100%"
              show-password
              v-model="registerForm.passwordConfirm"
              type="password"
              auto-complete="off"
              placeholder="请再次输入密码"
          >
            <!--                  <svg-icon slot="prefix" icon-class="password" class="el-input__icon input-icon" />-->
          </el-input>
        </el-form-item>
        <el-checkbox style="margin-left: 50px;margin-top: 10px;margin-bottom: 50px">我已仔细阅读并同意<span  style="color: #5F8AD3">《用户协议》</span>和<span style="color: #5F8AD3">《隐私权政策》</span></el-checkbox>
        <el-form-item>
          <el-button type="primary"
                     style="width: 100%;height: 5%"
                     @click="register">
            注册
          </el-button>
        </el-form-item>
        <el-form-item>
          <hr style="width: 100%;color: #EFEFF5">
          <div @click="$router.push('/register')" style="width: fit-content ;cursor: pointer">已经有账号了？ 请
            <span @click="$router.push('/login')" style="color: #5F8AD3">登录</span>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  name:'RegisterView',
  data(){
    return {
      //codeUrl: require('../assets/images/captcha.jpg'),
      cookiePassword: "",
      registerForm: {
        userName: "",
        password: "",
        rememberMe: false,
        time: "",
        passwordConfirm: ""
      },
      registerRules: {
        userName: [{ required: true, trigger: "blur", message: "用户名不能为空" }],
        password: [{ required: true, trigger: "blur", message: "密码不能为空" }],
        passwordConfirm: [{ required: true, trigger: "blur", message: "请再次输入密码" }]
      },
      loading: false,
      redirect: undefined
    };
  },
  methods:  {
    register(){
      if(this.registerForm.userName.indexOf(" ")!==-1){
        this.$message.error('用户名中不能包含空格')
        return
      }
      if(this.registerForm.password.indexOf(" ")!==-1 || this.registerForm.passwordConfirm.indexOf(" ")!==-1){
        this.$message.error('密码中不能包含空格')
        return
      }
      this.$refs["registerForm"].validate((valid) => {
        if (valid) {
          if (this.registerForm.passwordConfirm !== this.registerForm.password){
            this.$message.error("密码不一致");
          }else{
            let form = new FormData();
            form.append("username",this.registerForm.userName);
            form.append("password",this.registerForm.password);
            form.append("email",this.registerForm.userName+'@email.com');
            this.$request({
              method: 'post',
              url: 'http://localhost:5000/register',
              headers: {
                'Content-Type': 'multipart/form-data;',
              },
              data: form,
            }).then((res)=>{
              if(res.status === 'success'){
                this.$message.success("注册成功");
                this.$router.push('/login');
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

  }
}
</script>

<style scoped>
.loginBack{
  /* 加载背景图 */
  background-image: url(../assets/girl_glasses_autumn_267722_1280x720.jpg);
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