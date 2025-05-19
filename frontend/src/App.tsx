import { Route, Routes } from "react-router-dom";

import LoginPage from "@/pages/login";
import InitPage from "@/pages/init";
import DashboardPage from "@/pages/dashboard";
import ProfilePage from "@/pages/profile";
import SettingsPage from "@/pages/settings";
import EndpointsPage from "@/pages/endpoints";
import ModelsPage from "@/pages/models";
import ApiKeysPage from "@/pages/apikeys";
import UsersPage from "@/pages/users";
import PlansPage from "@/pages/plans";
import UnauthorizedPage from "@/pages/unauthorized";
import NotFoundPage from "@/pages/notfound";
import ProtectedRoute from "@/components/ProtectedRoute";

function App() {
  return (
    <Routes>
      {/* 公共路由 */}
      <Route element={<LoginPage />} path="/login" />
      <Route element={<InitPage />} path="/init" />
      <Route element={<UnauthorizedPage />} path="/unauthorized" />

      {/* 受保护路由 */}
      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardPage />} path="/" />
        {/* 端点相关路由 */}
        <Route element={<EndpointsPage />} path="/endpoints/*" />
        {/* 模型相关路由 */}
        <Route element={<ModelsPage />} path="/models/*" />
        {/* API 密钥相关路由 */}
        <Route element={<ApiKeysPage />} path="/apikeys/*" />
        {/* 用户个人资料和设置路由 */}
        <Route element={<ProfilePage />} path="/profile" />
        <Route element={<SettingsPage />} path="/settings" />
      </Route>

      {/* 管理员路由 */}
      <Route element={<ProtectedRoute requireAdmin={true} />}>
        <Route element={<UsersPage />} path="/users/*" />
        <Route element={<PlansPage />} path="/plans/*" />
      </Route>

      {/* 404 页面 */}
      <Route element={<NotFoundPage />} path="*" />
    </Routes>
  );
}

export default App;
