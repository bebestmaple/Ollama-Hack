import { Button } from "@heroui/button";
import { Link } from "@heroui/link";
import { Card, CardBody } from "@heroui/card";

import DashboardLayout from "@/layouts/Main";
import { LogoIcon } from "@/components/icons";

const NotFoundPage = () => {
  return (
    <DashboardLayout>
      <div className="flex items-center justify-center min-h-full">
        <Card className="w-full max-w-md p-8 space-y-8">
          <CardBody>
            <h1 className="text-8xl font-bold flex items-center gap-2">
              <LogoIcon />
              404
            </h1>
            <p className="mt-2">您访问的页面不存在或已被移除。</p>
            <div className="mt-6 flex gap-2 w-full justify-center items-center">
              <Link className="inline-block" href="/">
                <Button color="primary">返回首页</Button>
              </Link>
            </div>
          </CardBody>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default NotFoundPage;
