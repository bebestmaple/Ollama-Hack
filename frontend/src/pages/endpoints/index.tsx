import React from "react";
import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { addToast } from "@heroui/toast";
import { Selection } from "@heroui/table";

import EndpointDetailDrawer from "@/components/endpoints/DetailDrawer.tsx";
import CreateEndpointModal from "@/components/endpoints/CreateModal.tsx";
import EndpointTable from "@/components/endpoints/Table.tsx";
import EndpointEditModal from "@/components/endpoints/EditModal.tsx";
import { useAuth } from "@/contexts/AuthContext";
import { useCustomQuery } from "@/hooks";
import { endpointApi } from "@/api";
import { EndpointWithAIModelCount, PageResponse, SortOrder } from "@/types";
import DashboardLayout from "@/layouts/Main";
import ErrorDisplay from "@/components/ErrorDisplay";
import { useDialog } from "@/contexts/DialogContext";

// 端点列表页
export const EndpointListPage = () => {
  const { isAdmin } = useAuth();
  const { confirm } = useDialog();
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [orderBy, setOrderBy] = useState<string | undefined>("status");
  const [order, setOrder] = useState<SortOrder | undefined>(SortOrder.ASC);

  // 详情抽屉状态
  const [isDetailDrawerOpen, setIsDetailDrawerOpen] = useState(false);
  const [selectedEndpointId, setSelectedEndpointId] = useState<number | null>(
    null,
  );

  // 新增状态变量
  const INITIAL_VISIBLE_COLUMNS = [
    "id",
    "name",
    // "url",
    "status",
    "models",
    // "created_at",
    "actions",
  ];
  const [visibleColumns, setVisibleColumns] = useState<Selection>(
    new Set(INITIAL_VISIBLE_COLUMNS),
  );

  // 模态框状态
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingEndpoint, setEditingEndpoint] =
    useState<EndpointWithAIModelCount | null>(null);

  // 处理每页行数变化
  const [pageSize, setPageSize] = useState(10);

  // 获取端点列表
  const {
    data: endpoints,
    isLoading,
    error: endpointsError,
    refetch,
  } = useCustomQuery<PageResponse<EndpointWithAIModelCount>>(
    ["endpoints", page, searchTerm, orderBy, order, pageSize],
    () =>
      endpointApi.getEndpoints({
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

  // 处理删除端点
  const handleDeleteEndpoint = async (id: number) => {
    confirm("确定要删除这个端点吗？此操作不可撤销。", async () => {
      try {
        await endpointApi.deleteEndpoint(id);
        refetch();
        setIsEditModalOpen(false);
      } catch (err) {
        addToast({
          title: "删除端点失败",
          description: (err as Error).message || "请重试",
          color: "danger",
        });
      }
    });
  };

  // 打开端点详情抽屉
  const openEndpointDetail = (endpointId: number) => {
    setSelectedEndpointId(endpointId);
    setIsDetailDrawerOpen(true);
  };

  // 关闭端点详情抽屉
  const closeEndpointDetail = () => {
    setIsDetailDrawerOpen(false);
  };

  return (
    <DashboardLayout current_root_href="/endpoints">
      {endpointsError ? (
        <ErrorDisplay
          error={
            new Error((endpointsError as Error)?.message || "加载端点列表失败")
          }
        />
      ) : (
        <EndpointTable
          endpoints={endpoints?.items}
          error={endpointsError}
          isAdmin={isAdmin}
          isLoading={isLoading}
          order={order}
          orderBy={orderBy}
          page={page}
          pageSize={pageSize}
          searchTerm={searchTerm}
          setOrder={setOrder}
          setOrderBy={setOrderBy}
          setPageSize={setPageSize}
          setSearchTerm={setSearchTerm}
          setVisibleColumns={setVisibleColumns}
          totalItems={endpoints?.total}
          totalPages={endpoints?.pages}
          visibleColumns={visibleColumns}
          onCreateEndpoint={() => setIsCreateModalOpen(true)}
          onDeleteEndpoint={handleDeleteEndpoint}
          onEditEndpoint={(endpoint) => {
            setEditingEndpoint(endpoint);
            setIsEditModalOpen(true);
          }}
          onOpenEndpointDetail={openEndpointDetail}
          onPageChange={handlePageChange}
          onSearch={handleSearch}
        />
      )}

      {/* 创建端点对话框 */}
      <CreateEndpointModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={refetch}
      />

      {/* 编辑端点对话框 */}
      {editingEndpoint && (
        <EndpointEditModal
          endpointId={editingEndpoint.id}
          endpointName={editingEndpoint.name}
          endpointUrl={editingEndpoint.url}
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          onDelete={handleDeleteEndpoint}
          onSuccess={refetch}
        />
      )}

      {/* 端点详情抽屉 */}
      {selectedEndpointId && (
        <EndpointDetailDrawer
          id={selectedEndpointId}
          isAdmin={isAdmin}
          isOpen={isDetailDrawerOpen}
          onClose={closeEndpointDetail}
          onDelete={handleDeleteEndpoint}
          onEdit={(endpoint) => {
            setEditingEndpoint(endpoint);
            setIsEditModalOpen(true);
          }}
        />
      )}
    </DashboardLayout>
  );
};

// 路由组件
const EndpointsPage = () => {
  return (
    <Routes>
      <Route element={<EndpointListPage />} path="/" />
    </Routes>
  );
};

export default EndpointsPage;
