import { useState } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from "@heroui/modal";
import { SortDescriptor, Tooltip, Form, Snippet } from "@heroui/react";

import { useAuth } from "@/contexts/AuthContext";
import { useCustomQuery, useCustomMutation } from "@/hooks";
import { apiKeyApi } from "@/api";
import {
  ApiKeyCreate,
  ApiKeyInfo,
  ApiKeyResponse,
  PageResponse,
  SortOrder,
} from "@/types";
import DashboardLayout from "@/layouts/Main";
import { DeleteIcon, PlusIcon, StatisticsIcon } from "@/components/icons";
import { DataTable } from "@/components/DataTable";
import { useDialog } from "@/contexts/DialogContext";
import { StatsDrawer } from "@/components/apikeys";

const ApiKeysPage = () => {
  const { isAdmin } = useAuth();
  const { confirm } = useDialog();
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [orderBy, setOrderBy] = useState<string | undefined>();
  const [order, setOrder] = useState<SortOrder | undefined>();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newApiKeyName, setNewApiKeyName] = useState("");
  const [createdApiKey, setCreatedApiKey] = useState<ApiKeyResponse | null>(
    null,
  );
  const [isCreating, setIsCreating] = useState(false);

  // 统计抽屉状态
  const [isStatsDrawerOpen, setIsStatsDrawerOpen] = useState(false);
  const [selectedApiKeyId, setSelectedApiKeyId] = useState<number | null>(null);
  const [selectedApiKeyName, setSelectedApiKeyName] = useState<string>("");

  // 排序状态
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: orderBy || "id",
    direction:
      order === SortOrder.ASC
        ? "ascending"
        : order === SortOrder.DESC
          ? "descending"
          : "ascending",
  });

  // 处理排序
  const handleSort = (descriptor: SortDescriptor) => {
    setSortDescriptor(descriptor);
    setOrderBy(descriptor.column?.toString());
    setOrder(
      descriptor.direction === "ascending" ? SortOrder.ASC : SortOrder.DESC,
    );
  };

  // 获取 API 密钥列表
  const {
    data: apiKeys,
    isLoading,
    error,
    refetch,
  } = useCustomQuery<PageResponse<ApiKeyInfo>>(
    ["apikeys", page, size, searchTerm, orderBy, order],
    () =>
      apiKeyApi.getApiKeys({
        page,
        size,
        search: searchTerm,
        order_by: orderBy,
        order,
      }),
    { staleTime: 30000 },
  );

  // 创建 API 密钥
  const createApiKeyMutation = useCustomMutation<ApiKeyResponse, ApiKeyCreate>(
    (data) => apiKeyApi.createApiKey(data),
    {
      onSuccess: (data) => {
        setCreatedApiKey(data);
        refetch();
        setIsCreating(false);
      },
      onError: () => {
        setIsCreating(false);
      },
    },
  );

  // 处理搜索
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // 搜索时重置页码
    setPage(1);
    refetch();
  };

  // 处理页码变化
  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  // 处理创建 API 密钥
  const handleCreateApiKey = () => {
    setIsCreating(true);
    createApiKeyMutation.mutate({ name: newApiKeyName });
  };

  // 处理关闭创建成功对话框
  const handleCloseSuccessModal = () => {
    setCreatedApiKey(null);
    setNewApiKeyName("");
    setIsCreateModalOpen(false);
  };

  // 处理删除 API 密钥
  const handleDeleteApiKey = (id: number) => {
    confirm("确定要删除此 API 密钥吗？此操作不可逆。", async () => {
      try {
        await apiKeyApi.deleteApiKey(id);
        refetch();
      } catch (err) {
        addToast({
          title: "删除 API 密钥失败",
          description: (err as Error).message || "请重试",
          color: "danger",
        });
      }
    });
  };

  // 打开API密钥统计抽屉
  const openApiKeyStats = (apiKey: ApiKeyInfo) => {
    setSelectedApiKeyId(apiKey.id);
    setSelectedApiKeyName(apiKey.name);
    setIsStatsDrawerOpen(true);
  };

  // 关闭API密钥统计抽屉
  const closeApiKeyStats = () => {
    setIsStatsDrawerOpen(false);
  };

  // 定义表格列
  const columns = [
    { key: "id", label: "ID", allowsSorting: true },
    { key: "name", label: "名称", allowsSorting: true },
    { key: "created_at", label: "创建时间", allowsSorting: true },
    { key: "last_used_at", label: "最后使用时间", allowsSorting: true },
    ...(isAdmin
      ? [{ key: "user_id", label: "用户", allowsSorting: true }]
      : []),
    { key: "actions", label: "操作" },
  ];

  // 渲染单元格内容
  const renderCell = (apiKey: ApiKeyInfo, columnKey: string) => {
    switch (columnKey) {
      case "id":
        return apiKey.id;
      case "name":
        return (
          <span className="whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
            {apiKey.name}
          </span>
        );
      case "created_at":
        return new Date(apiKey.created_at).toLocaleString();
      case "last_used_at":
        return apiKey.last_used_at
          ? new Date(apiKey.last_used_at).toLocaleString()
          : "从未使用";
      case "user_id":
        return apiKey.user_name || "-";
      case "actions":
        return (
          <div className="relative flex items-center gap-2">
            <Tooltip content="查看密钥用量">
              <Button
                isIconOnly
                className="text-default-400 active:opacity-50 text-lg"
                variant="light"
                onPress={() => openApiKeyStats(apiKey)}
              >
                <StatisticsIcon />
              </Button>
            </Tooltip>
            <Tooltip color="danger" content="删除密钥">
              <Button
                isIconOnly
                className="text-default-400 active:opacity-50 text-lg"
                variant="light"
                onPress={() => {
                  if (apiKey.id) {
                    handleDeleteApiKey(apiKey.id);
                  }
                }}
              >
                <DeleteIcon />
              </Button>
            </Tooltip>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <DashboardLayout current_root_href="/apikeys">
      <DataTable<ApiKeyInfo>
        addButtonProps={{
          tooltip: "创建 API 密钥",
          onClick: () => setIsCreateModalOpen(true),
          isIconOnly: true,
        }}
        autoSearchDelay={1000}
        columns={columns}
        data={apiKeys?.items || []}
        emptyContent={
          <>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              暂无 API 密钥数据
            </p>
            <Tooltip
              color="primary"
              content="创建第一个 API 密钥"
              placement="bottom"
            >
              <Button
                className="mt-4"
                color="primary"
                onPress={() => setIsCreateModalOpen(true)}
              >
                <PlusIcon />
              </Button>
            </Tooltip>
          </>
        }
        error={error}
        isLoading={isLoading}
        page={page}
        pageSize={size}
        pages={apiKeys?.pages}
        renderCell={renderCell}
        searchPlaceholder="搜索 API 密钥..."
        searchTerm={searchTerm}
        selectedSize={size}
        setSearchTerm={setSearchTerm}
        setSize={setSize}
        sortDescriptor={sortDescriptor}
        title="API 密钥列表"
        total={apiKeys?.total}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
        onSortChange={handleSort}
      />

      {/* 创建 API 密钥对话框 */}
      <Modal
        isOpen={isCreateModalOpen}
        placement="center"
        onClose={() => setIsCreateModalOpen(false)}
      >
        <ModalContent>
          {(onClose) => (
            <Form className="w-full" onSubmit={handleCreateApiKey}>
              <ModalHeader>
                {createdApiKey ? "密钥创建成功" : "创建 API 密钥"}
              </ModalHeader>
              <ModalBody className="w-full">
                {createdApiKey ? (
                  <div>
                    <p className="mb-2">
                      请保存好您的 API 密钥，这是唯一可以看到它的机会：
                    </p>
                    <Snippet color="primary" symbol="">
                      {createdApiKey.key}
                    </Snippet>
                  </div>
                ) : (
                  <Input
                    fullWidth
                    isRequired
                    errorMessage={({ validationErrors }) => {
                      return validationErrors;
                    }}
                    label="API 密钥名称"
                    maxLength={128}
                    minLength={3}
                    placeholder="输入 API 密钥名称"
                    value={newApiKeyName}
                    onChange={(e) => setNewApiKeyName(e.target.value)}
                  />
                )}
              </ModalBody>
              <ModalFooter className="w-full">
                {createdApiKey ? (
                  <Button color="primary" onPress={handleCloseSuccessModal}>
                    确定
                  </Button>
                ) : (
                  <>
                    <Button
                      disabled={isCreating}
                      variant="light"
                      onPress={onClose}
                    >
                      取消
                    </Button>
                    <Button
                      color="primary"
                      disabled={isCreating}
                      isLoading={isCreating}
                      onPress={handleCreateApiKey}
                    >
                      创建
                    </Button>
                  </>
                )}
              </ModalFooter>
            </Form>
          )}
        </ModalContent>
      </Modal>

      {/* API密钥统计抽屉 */}
      {selectedApiKeyId && (
        <StatsDrawer
          apiKeyName={selectedApiKeyName}
          id={selectedApiKeyId}
          isOpen={isStatsDrawerOpen}
          onClose={closeApiKeyStats}
        />
      )}
    </DashboardLayout>
  );
};

export default ApiKeysPage;
