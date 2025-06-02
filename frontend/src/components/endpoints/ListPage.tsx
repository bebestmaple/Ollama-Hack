import React, { useState, useRef, useEffect } from "react";
import { addToast } from "@heroui/toast";
import { Selection } from "@heroui/table";

import EndpointDetailDrawer from "@/components/endpoints/DetailDrawer";
import CreateEndpointModal from "@/components/endpoints/CreateModal";
import EndpointTable from "@/components/endpoints/Table";
import EndpointEditModal from "@/components/endpoints/EditModal";
import { useAuth } from "@/contexts/AuthContext";
import {
  useCustomQuery,
  usePaginationUrlState,
  PaginationValidationConfig,
} from "@/hooks";
import { endpointApi } from "@/api";
import {
  EndpointWithAIModelCount,
  PageResponse,
  SortOrder,
  TaskStatusEnum,
} from "@/types";
import DashboardLayout from "@/layouts/Main";
import ErrorDisplay from "@/components/ErrorDisplay";
import { useDialog } from "@/contexts/DialogContext";

// 端点列表页
const EndpointListPage = () => {
  const { isAdmin } = useAuth();
  const { confirm } = useDialog();

  // 验证配置
  const [validationConfig, setValidationConfig] =
    useState<PaginationValidationConfig>({
      page: { min: 1 },
      pageSize: { min: 5, max: 100 },
      totalPages: 1,
      orderBy: {
        allowedFields: ["id", "name", "status", "created_at"],
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
      orderBy: "status",
      order: SortOrder.ASC,
    },
    validationConfig,
  );

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

  // 测试状态管理
  const [testingEndpointIds, setTestingEndpointIds] = useState<number[]>([]);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

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

  // 当总页数变化时，更新验证配置
  useEffect(() => {
    if (endpoints?.pages) {
      setValidationConfig((prev) => ({
        ...prev,
        totalPages: endpoints.pages,
      }));
    }
  }, [endpoints?.pages]);

  useEffect(() => {
    const running_endpoint_ids = endpoints?.items
      .filter((endpoint) => endpoint.task_status === TaskStatusEnum.RUNNING)
      .map((endpoint) => endpoint.id);

    if (running_endpoint_ids && running_endpoint_ids.length > 0) {
      let new_testing_endpoint_ids = new Set([
        ...testingEndpointIds,
        ...running_endpoint_ids,
      ]);

      setTestingEndpointIds(Array.from(new_testing_endpoint_ids));
    }
  }, [endpoints, setTestingEndpointIds]);

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

  // 处理测试端点
  const handleTestEndpoint = (id: number) => {
    confirm(
      `确定要测试端点 ${id} 吗？`,
      async () => {
        try {
          // 直接调用函数式更新，避免 stale closure
          setTestingEndpointIds((prev) => {
            if (prev.includes(id)) {
              addToast({
                title: "测试已触发",
                description: `端点 ${id} 测试已开始，请等待结果`,
                color: "primary",
              });

              return prev;
            }
            endpointApi.triggerEndpointTest(id);
            addToast({
              title: "测试已触发",
              description: `端点 ${id} 测试已开始，请等待结果`,
              color: "primary",
            });

            return [...prev, id];
          });
        } catch (err) {
          addToast({
            title: "触发测试失败",
            description: (err as Error).message || "请重试",
            color: "danger",
          });
        }
      },
      "确认测试端点",
    );
  };

  // 添加轮询逻辑
  useEffect(() => {
    // 如果有正在测试的端点，开始轮询
    if (testingEndpointIds.length > 0 && !pollingIntervalRef.current) {
      // 创建一个当前ID列表的副本，用于闭包内部使用
      const currentTestingIds = [...testingEndpointIds];

      pollingIntervalRef.current = setInterval(async () => {
        // 获取当前最新的测试ID列表
        let stillTestingIds = [...currentTestingIds];

        // 检查每个正在测试的端点的状态
        for (const endpointId of currentTestingIds) {
          try {
            const task = await endpointApi.getEndpointTask(endpointId);

            const endpoint = endpoints?.items.find(
              (endpoint) => endpoint.id === endpointId,
            );

            if (endpoint) {
              endpoint.task_status = task.status;
            }

            if (
              task.status !== TaskStatusEnum.RUNNING &&
              task.status !== TaskStatusEnum.PENDING
            ) {
              if (task.status === TaskStatusEnum.FAILED) {
                addToast({
                  title: "测试失败",
                  description: `端点 ${endpointId} 测试失败，请重试`,
                  color: "danger",
                });
              } else if (task.status === TaskStatusEnum.DONE) {
                addToast({
                  title: "测试成功",
                  description: `端点 ${endpointId} 测试成功`,
                  color: "success",
                });
              }
              // 如果没有运行中的任务，从测试列表中移除
              stillTestingIds = stillTestingIds.filter(
                (id) => Number(id) !== Number(endpointId),
              );
              // 刷新端点列表以获取最新状态
              refetch();
            }
          } catch {
            // 出错时也从列表中移除，避免无限尝试
            stillTestingIds = stillTestingIds.filter(
              (id) => Number(id) !== Number(endpointId),
            );
          }
        }

        // 更新正在测试的端点列表 - 使用函数式更新确保使用最新状态
        setTestingEndpointIds((prev) => {
          if (JSON.stringify(stillTestingIds) !== JSON.stringify(prev)) {
            return stillTestingIds;
          }

          return prev;
        });

        // 如果没有正在测试的端点，清除轮询
        if (stillTestingIds.length === 0 && pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }, 5000); // 每5秒轮询一次
    }

    return () => {
      // 组件卸载时清除轮询
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [testingEndpointIds, refetch]);

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
          testingEndpointIds={testingEndpointIds}
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
          onTestEndpoint={handleTestEndpoint}
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

export default EndpointListPage;
