import React from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Card, CardBody } from "@heroui/card";

import LoadingSpinner from "./LoadingSpinner";

import { useAuth } from "@/contexts/AuthContext";
import DashboardLayout from "@/layouts/Main";

interface ProtectedRouteProps {
  requireAdmin?: boolean;
}

const ProtectedRoute = ({ requireAdmin = false }: ProtectedRouteProps) => {
  const { isAuthenticated, isLoading, isAdmin } = useAuth();
  const location = useLocation();

  if (isLoading) {
    // 加载中，可以返回一个加载组件
    return (
      <DashboardLayout>
        <Card>
          <CardBody>
            <LoadingSpinner />
          </CardBody>
        </Card>
      </DashboardLayout>
    );
  }

  // 如果用户未认证，重定向到登录页面
  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />;
  }

  // 如果需要管理员权限，但用户不是管理员，重定向到首页或显示无权限页面
  if (requireAdmin && !isAdmin) {
    return <Navigate replace to="/unauthorized" />;
  }

  // 用户已认证且满足权限要求，渲染子路由
  return <Outlet />;
};

export default ProtectedRoute;
