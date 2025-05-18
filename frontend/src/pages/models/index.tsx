import { useState } from "react";
import { Routes, Route } from "react-router-dom";

import { useCustomQuery } from "@/hooks";
import { aiModelApi } from "@/api";
import { AIModelInfoWithEndpointCount, PageResponse, SortOrder } from "@/types";
import DashboardLayout from "@/layouts/Main";
import ModelTable from "@/components/models/Table";
import ModelDetailDrawer from "@/components/models/DetailDrawer";

// 模型列表页面
export const ModelListPage = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [orderBy, setOrderBy] = useState<string | undefined>();
  const [order, setOrder] = useState<SortOrder | undefined>();

  // 详情抽屉状态
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null);

  // 获取模型列表
  const {
    data: models,
    isLoading,
    error: modelsError,
    refetch,
  } = useCustomQuery<PageResponse<AIModelInfoWithEndpointCount>>(
    ["models", page, pageSize, searchTerm, orderBy, order],
    () =>
      aiModelApi.getAIModels({
        page,
        size: pageSize,
        search: searchTerm,
        order_by: orderBy,
        order,
      }),
    { staleTime: 30000 },
  );

  // 处理搜索
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    refetch();
  };

  // 处理页码变化
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  // 打开模型详情抽屉
  const openModelDetail = (modelId: number) => {
    setSelectedModelId(modelId);
    setIsDetailDrawerOpen(true);
  };

  // 关闭模型详情抽屉
  const closeModelDetail = () => {
    setIsDetailDrawerOpen(false);
  };

  return (
    <DashboardLayout current_root_href="/models">
      <ModelTable
        error={modelsError}
        isLoading={isLoading}
        models={models?.items}
        order={order}
        orderBy={orderBy}
        page={page}
        pageSize={pageSize}
        searchTerm={searchTerm}
        setOrder={setOrder}
        setOrderBy={setOrderBy}
        setPageSize={setPageSize}
        setSearchTerm={setSearchTerm}
        totalItems={models?.total}
        totalPages={models?.pages}
        onOpenModelDetail={openModelDetail}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
      />

      {/* 模型详情抽屉 */}
      {selectedModelId && (
        <ModelDetailDrawer
          id={selectedModelId}
          isOpen={isDetailDrawerOpen}
          onClose={closeModelDetail}
        />
      )}
    </DashboardLayout>
  );
};

// 路由组件
const ModelsPage = () => {
  return (
    <Routes>
      <Route element={<ModelListPage />} path="/" />
      {/* <Route path="/:id" element={<ModelDetailPage />} /> */}
    </Routes>
  );
};

export default ModelsPage;
