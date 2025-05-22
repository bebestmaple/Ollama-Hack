import { Card, CardHeader } from "@heroui/card";
import { Progress } from "@heroui/progress";

import { useAuth } from "@/contexts/AuthContext";
import { useCustomQuery } from "@/hooks";
import { endpointApi, aiModelApi, planApi } from "@/api";
import {
  PageResponse,
  EndpointWithAIModelCount,
  AIModelInfoWithEndpointCount,
  PlanResponse,
  ApiError,
} from "@/types";
import DashboardLayout from "@/layouts/Main";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorDisplay from "@/components/ErrorDisplay";

const DashboardPage = () => {
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

  // 管理员统计信息
  // const {
  //   data: users,
  //   isLoading: isLoadingUsers,
  //   error: usersError,
  // } = useCustomQuery<PageResponse<UserInfo>>(
  //   ["users", "stats"],
  //   () =>
  //     authApi.getUsers({
  //       page: 1,
  //       size: 1,
  //     }),
  //   { enabled: !!isAdmin },
  // );

  const {
    data: endpoints,
    isLoading: isLoadingEndpoints,
    error: endpointsError,
  } = useCustomQuery<PageResponse<EndpointWithAIModelCount>>(
    ["endpoints", "stats"],
    () =>
      endpointApi.getEndpoints({
        page: 1,
        size: 1,
      }),
    { enabled: true },
  );

  const {
    data: availableEndpoints,
    isLoading: isLoadingAvailableEndpoints,
    error: availableEndpointsError,
  } = useCustomQuery<PageResponse<EndpointWithAIModelCount>>(
    ["endpoints", "stats", "available"],
    () =>
      endpointApi.getEndpoints({
        page: 1,
        size: 1,
        status: "available",
      }),
    { enabled: true },
  );

  const {
    data: models,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useCustomQuery<PageResponse<AIModelInfoWithEndpointCount>>(
    ["models", "stats"],
    () =>
      aiModelApi.getAIModels({
        page: 1,
        size: 1,
      }),
    { enabled: true },
  );

  const {
    data: availableModels,
    isLoading: isLoadingAvailableModels,
    error: availableModelsError,
  } = useCustomQuery<PageResponse<AIModelInfoWithEndpointCount>>(
    ["models", "stats", "available"],
    () =>
      aiModelApi.getAIModels({
        page: 1,
        size: 1,
        is_available: true,
      }),
    { enabled: true },
  );

  const isLoading =
    isLoadingPlan ||
    // (isAdmin && isLoadingUsers) ||
    isLoadingEndpoints ||
    isLoadingModels ||
    isLoadingAvailableEndpoints ||
    isLoadingAvailableModels;
  const error =
    planError ||
    // (isAdmin && usersError) ||
    endpointsError ||
    modelsError ||
    availableEndpointsError ||
    availableModelsError;

  // 创建用于 ErrorDisplay 的 Error 对象
  const getErrorForDisplay = () => {
    if (!error) return null;

    // 将 ApiError 转换为 Error 对象
    return new Error((error as ApiError)?.message || "发生了一个错误");
  };

  if (isLoading) {
    return (
      <DashboardLayout current_root_href="/">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="large" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout current_root_href="/">
      {error && <ErrorDisplay error={getErrorForDisplay()} />}

      {/* 欢迎卡片 */}
      <Card className="mb-6 p-6">
        <h2 className="text-xl font-semibold mb-2">
          👋 你好, {user?.username}
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          欢迎使用 Ollama Hack 平台，这里可以管理你的 Ollama 端点和 AI 模型。
        </p>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card className="p-6">
          <CardHeader className="p-0">
            <h3 className="text-primary-400 text-lg font-bold">端点</h3>
          </CardHeader>
          <p className="text-3xl font-bold">{endpoints?.total || 0}</p>
          <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-2">
            已添加的端点总数
          </p>
          <div className="flex flex-col gap-2 justify-center">
            <Progress
              color="primary"
              formatOptions={{ style: "percent", maximumFractionDigits: 0 }}
              maxValue={endpoints?.total || 0}
              value={availableEndpoints?.total || 0}
            />
            <div className="flex flex-row gap-2 justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                可用端点
              </span>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {availableEndpoints?.total || 0} / {endpoints?.total || 0}
              </span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <CardHeader className="p-0">
            <h3 className="text-success-400 text-lg font-bold">AI 模型</h3>
          </CardHeader>
          <p className="text-3xl font-bold">{models?.total || 0}</p>
          <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-2">
            扫描出的 AI 模型总数
          </p>
          <div className="flex flex-col gap-2 justify-center">
            <Progress
              color="success"
              formatOptions={{ style: "percent", maximumFractionDigits: 0 }}
              maxValue={models?.total || 0}
              value={availableModels?.total || 0}
            />
            <div className="flex flex-row gap-2 justify-between">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                可用 AI 模型
              </span>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {availableModels?.total || 0} / {models?.total || 0}
              </span>
            </div>
          </div>
        </Card>
        {/* {isAdmin && (
          <Card className="p-6">
            <CardHeader className="p-0">
              <h3 className="text-primary-300 text-lg font-bold">用户</h3>
            </CardHeader>
            <p className="text-3xl font-bold">{users?.total || 0}</p>
            <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-2">
              已注册用户总数
            </p>
            <div className="flex flex-col gap-2 justify-center">
              <Progress
                color="primary"
                formatOptions={{ style: "percent", maximumFractionDigits: 0 }}
                maxValue={users?.total || 0}
                value={users?.total || 0}
              />
              <div className="flex flex-row gap-2 justify-between">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  已注册用户
                </span>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {users?.total || 0} / {users?.total || 0}
                </span>
              </div>
            </div>
          </Card>
        )} */}
      </div>

      {/* 当前计划 */}
      {userPlan && (
        <Card className="mb-6 p-6">
          <h3 className="font-semibold text-lg mb-4">当前计划</h3>
          <div className="space-y-2">
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
    </DashboardLayout>
  );
};

export default DashboardPage;
