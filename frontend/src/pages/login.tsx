import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { addToast } from "@heroui/toast";
import { Card, CardBody, CardFooter, CardHeader } from "@heroui/card";
import { Form } from "@heroui/form";

import { EnhancedAxiosError } from "@/api";
import { useAuth } from "@/contexts/AuthContext";
import { LogoIcon } from "@/components/icons";
import DashboardLayout from "@/layouts/Main";

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // 获取重定向来源
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname || "/";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      addToast({
        title: "登录失败",
        description: "请输入用户名和密码",
        color: "danger",
      });

      return;
    }

    try {
      setIsLoading(true);
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      addToast({
        title: "登录失败",
        description:
          (err as EnhancedAxiosError).detail || "发生未知错误，请稍后重试",
        color: "danger",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex items-center justify-center min-h-full pt-10">
        <Card className="w-full max-w-md p-8">
          <CardHeader>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <LogoIcon className="w-8 h-8" /> Ollama Hack
            </h1>
          </CardHeader>
          <Form onSubmit={handleSubmit}>
            <CardBody className="space-y-4">
              <Input
                required
                label="用户名"
                placeholder="请输入用户名"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <Input
                required
                label="密码"
                placeholder="请输入密码"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </CardBody>
            <CardFooter>
              <Button
                fullWidth
                color="primary"
                isLoading={isLoading}
                type="submit"
              >
                登录
              </Button>
            </CardFooter>
          </Form>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default LoginPage;
