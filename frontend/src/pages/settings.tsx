import { useState } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Card } from "@heroui/card";

import { authApi } from "@/api";
import { useAuth } from "@/contexts/AuthContext";
import DashboardLayout from "@/layouts/Main";
import ErrorDisplay from "@/components/ErrorDisplay";

const Settings = () => {
  const { user } = useAuth();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);

    if (!oldPassword || !newPassword || !confirmPassword) {
      setError(new Error("请填写所有密码字段"));

      return;
    }

    if (newPassword !== confirmPassword) {
      setError(new Error("新密码与确认密码不匹配"));

      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      // 清空表单
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err
          : new Error("密码修改失败，请检查旧密码是否正确"),
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout current_root_href="/settings">
      <div className="max-w-3xl mx-auto">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-6">修改密码</h2>

          {error && <ErrorDisplay className="mb-4" error={error} />}

          {success && (
            <div className="p-4 mb-4 text-white bg-success-500 rounded-md">
              <p>密码修改成功！</p>
            </div>
          )}

          <form onSubmit={handleChangePassword}>
            <div className="space-y-4">
              <div>
                <label
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                  htmlFor="oldPassword"
                >
                  当前密码
                </label>
                <Input
                  fullWidth
                  id="oldPassword"
                  placeholder="请输入当前密码"
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                />
              </div>

              <div>
                <label
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                  htmlFor="newPassword"
                >
                  新密码
                </label>
                <Input
                  fullWidth
                  id="newPassword"
                  placeholder="请输入新密码"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>

              <div>
                <label
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                  htmlFor="confirmPassword"
                >
                  确认新密码
                </label>
                <Input
                  fullWidth
                  id="confirmPassword"
                  placeholder="请再次输入新密码"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <div className="mt-6">
              <Button color="primary" isLoading={isLoading} type="submit">
                修改密码
              </Button>
            </div>
          </form>
        </Card>

        <Card className="p-6 mt-6">
          <h2 className="text-xl font-semibold mb-4">账户信息</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">用户名：</span>
              <span className="font-medium">{user?.username}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">
                用户 ID：
              </span>
              <span className="font-medium">{user?.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">
                用户类型：
              </span>
              <span className="font-medium">
                {user?.is_admin ? "管理员" : "普通用户"}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Settings;
