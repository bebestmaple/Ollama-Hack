import { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";

import {
  useCustomQuery,
  usePaginationUrlState,
  PaginationValidationConfig,
} from "@/hooks";
import { aiModelApi } from "@/api";
import { AIModelInfoWithEndpointCount, PageResponse } from "@/types";
import DashboardLayout from "@/layouts/Main";
import ModelTable from "@/components/models/Table";
import ModelDetailDrawer from "@/components/models/DetailDrawer";

// 模型列表页面
export const ModelListPage = () => {
  // 验证配置
  const [validationConfig, setValidationConfig] =
    useState<PaginationValidationConfig>({
      page: { min: 1 },
      pageSize: { min: 5, max: 100 },
      totalPages: 1,
      orderBy: {
        allowedFields: ["id", "name", "created_at", "last_used_at"],
        defaultField: "id",
      },
    });

  // 使用URL参数管理状态，替代多个单独的useState
  const {
    page,
    pageSize,
    search: searchTerm,
    orderBy,
    order,
    setPage,
    setPageSize,
    setSearch: setSearchTerm,
    setOrderBy,
    setOrder,
  } = usePaginationUrlState(
    {
      page: 1,
      pageSize: 10,
      search: "",
      orderBy: undefined,
      order: undefined,
    },
    validationConfig,
  );

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

  // 当总页数变化时，更新验证配置
  useEffect(() => {
    if (models?.pages) {
      setValidationConfig((prev) => ({
        ...prev,
        totalPages: models.pages,
      }));
    }
  }, [models?.pages]);

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

// 模型路由入口
const ModelsPage = () => {
  return (
    <Routes>
      <Route index element={<ModelListPage />} />
    </Routes>
  );
};

export default ModelsPage;
