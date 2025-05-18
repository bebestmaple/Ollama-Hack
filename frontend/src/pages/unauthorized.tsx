import { Button } from "@heroui/button";
import { Card, CardBody } from "@heroui/card";
import { Link } from "@heroui/link";

import { useAuth } from "@/contexts/AuthContext";
import DashboardLayout from "@/layouts/Main";
import { LogoIcon } from "@/components/icons";

const UnauthorizedPage = () => {
  const { isAuthenticated } = useAuth();

  return (
    <DashboardLayout>
      <div className="flex items-center justify-center min-h-full">
        <Card className="w-full max-w-md p-8 space-y-8">
          <CardBody>
            <h1 className="text-8xl font-bold flex items-center gap-2">
              <LogoIcon />
              403
            </h1>
            <p className="mt-2">
              您没有权限访问此页面，此页面需要管理员权限才能访问。
            </p>
            <div className="mt-6 flex gap-2 w-full justify-center items-center">
              {isAuthenticated ? (
                <Link className="inline-block" href="/">
                  <Button color="primary">返回首页</Button>
                </Link>
              ) : (
                <Link className="inline-block" href="/login">
                  <Button color="primary">登录</Button>
                </Link>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default UnauthorizedPage;
