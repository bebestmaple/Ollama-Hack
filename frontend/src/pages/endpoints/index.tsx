import React, { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";

import LoadingFallback from "@/components/LoadingFallback";

// 使用惰性加载导入 EndpointListPage 组件
const EndpointListPage = lazy(() => import("@/components/endpoints/ListPage"));

// 路由组件
const EndpointsPage = () => {
  return (
    <Routes>
      <Route
        element={
          <Suspense fallback={<LoadingFallback fullScreen={false} />}>
            <EndpointListPage />
          </Suspense>
        }
        path="/"
      />
    </Routes>
  );
};

export default EndpointsPage;
