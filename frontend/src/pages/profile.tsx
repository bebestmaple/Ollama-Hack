import { Card } from "@heroui/card";

import { useAuth } from "@/contexts/AuthContext";
import { useCustomQuery } from "@/hooks";
import { planApi } from "@/api";
import { PlanResponse } from "@/types";
import DashboardLayout from "@/layouts/Main";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorDisplay from "@/components/ErrorDisplay";

const ProfilePage = () => {
  const { user } = useAuth();

  // 获取用户当前计划
  const {
    data: userPlan,
    isLoading: isLoadingPlan,
    error: planError,
  } = useCustomQuery<PlanResponse>(
    ["plan", "current"],
    () => planApi.getCurrentUserPlan(),
    { enabled: !!user },
  );

  if (isLoadingPlan) {
    return (
      <DashboardLayout current_root_href="/profile">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="large" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout current_root_href="/profile">
      {planError && (
        <ErrorDisplay
          error={new Error((planError as any)?.message || "加载计划信息失败")}
        />
      )}

      <div className="max-w-3xl mx-auto">
        <Card className="p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold">{user?.username}</h2>
              <p className="text-gray-600 dark:text-gray-400">
                {user?.is_admin ? "管理员" : "普通用户"}
              </p>
            </div>
            {/* <Link href="/settings">
                            <Button variant="light" size="sm">
                                修改密码
                            </Button>
                        </Link> */}
          </div>

          <div className="mt-6 space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">
                用户 ID：
              </span>
              <span className="font-medium">{user?.id}</span>
            </div>
          </div>
        </Card>

        {userPlan && (
          <Card className="p-6">
            <div className="flex items-start justify-between">
              <h2 className="text-xl font-semibold">当前计划</h2>
            </div>

            <div className="mt-6 space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">
                  计划名称：
                </span>
                <span className="font-medium">{userPlan.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">
                  每分钟请求数限制：
                </span>
                <span className="font-medium">{userPlan.rpm}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">
                  每天请求数限制：
                </span>
                <span className="font-medium">{userPlan.rpd}</span>
              </div>
              {userPlan.description && (
                <div className="pt-2">
                  <span className="text-gray-600 dark:text-gray-400">
                    计划描述：
                  </span>
                  <p className="mt-1">{userPlan.description}</p>
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default ProfilePage;
