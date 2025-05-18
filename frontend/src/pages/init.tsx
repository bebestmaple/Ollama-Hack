import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Link } from "@heroui/link";
import { Form } from "@heroui/form";
import { addToast } from "@heroui/toast";
import { Card, CardBody, CardFooter, CardHeader } from "@heroui/card";

import { authApi, EnhancedAxiosError } from "@/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import DashboardLayout from "@/layouts/Main";
import { LogoIcon } from "@/components/icons";

const InitPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [initialized, setInitialized] = useState(false);

  const navigate = useNavigate();

  // 检查系统是否已经初始化
  useEffect(() => {
    const checkInitialization = async () => {
      try {
        setIsChecking(true);
        await authApi.getCurrentUser();
        // 如果成功获取用户信息，说明系统已初始化
        setInitialized(true);
        // 自动重定向到登录页
        setTimeout(() => navigate("/login"), 2000);
      } catch {
        // 错误意味着系统未初始化，可以继续
        setInitialized(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkInitialization();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      addToast({
        title: "初始化失败",
        description: "请输入用户名和密码",
        color: "danger",
      });

      return;
    }

    try {
      setIsLoading(true);
      await authApi.initUser({ username, password });
      setInitialized(true);
      // 初始化成功后跳转登录
      setTimeout(() => navigate("/login"), 2000);
    } catch (err) {
      addToast({
        title: "初始化失败",
        description:
          (err as EnhancedAxiosError).detail || "初始化失败，请稍后再试",
        color: "danger",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isChecking) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-full pt-10">
          <LoadingSpinner className="p-8" size="large" />
        </div>
      </DashboardLayout>
    );
  }

  if (initialized) {
    return (
      <DashboardLayout>
        {/* <div className="flex items-center justify-center min-h-full pt-10">
                    <div className="w-full max-w-md p-8 space-y-8 text-center">
                        <h1 className="text-2xl font-bold">
                            系统已初始化
                        </h1>
                        <p>
                            系统已经初始化过，正在跳转到登录页...
                        </p>
                        <Link href="/login" className="inline-block">
                            <Button color="primary">立即登录</Button>
                        </Link>
                        </div>
                    </div> */}
        <div className="flex items-center justify-center min-h-full pt-10">
          <Card className="w-full max-w-md p-8">
            <CardHeader>
              <h1 className="text-2xl font-bold">系统已初始化</h1>
            </CardHeader>
            <CardBody>
              <p>系统已经初始化过，正在跳转到登录页...</p>
            </CardBody>
            <CardFooter>
              <Link className="inline-block" href="/login">
                <Button color="primary">立即登录</Button>
              </Link>
            </CardFooter>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex items-center justify-center min-h-full pt-10">
        <Card className="w-full max-w-md p-8">
          <CardHeader>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <LogoIcon className="w-8 h-8" /> 管理员账号初始化
            </h1>
          </CardHeader>
          <Form className="space-y-4" onSubmit={handleSubmit}>
            <CardBody className="space-y-4">
              <Input
                isRequired
                label="用户名"
                placeholder="请输入用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <Input
                isRequired
                errorMessage={({ validationDetails, validationErrors }) => {
                  if (validationDetails.tooShort) {
                    return "密码长度不能小于8位";
                  }
                  if (validationDetails.tooLong) {
                    return "密码长度不能大于128位";
                  }

                  return validationErrors;
                }}
                label="密码"
                maxLength={128}
                minLength={8}
                placeholder="请输入密码"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Input
                isRequired
                label="确认密码"
                placeholder="请再次输入密码"
                type="password"
                validate={(value) => {
                  if (value !== password) {
                    return "两次输入的密码不一致";
                  }

                  return null;
                }}
              />
            </CardBody>
            <CardFooter>
              <Button
                fullWidth
                color="primary"
                isLoading={isLoading}
                type="submit"
              >
                初始化系统
              </Button>
            </CardFooter>
          </Form>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default InitPage;
