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
import {
  SortDescriptor,
  Checkbox,
  Tooltip,
  Form,
  addToast,
} from "@heroui/react";

import { useCustomQuery, useCustomMutation } from "@/hooks";
import { EnhancedAxiosError, planApi } from "@/api";
import {
  PlanCreate,
  PlanResponse,
  PlanUpdate,
  PageResponse,
  SortOrder,
} from "@/types";
import DashboardLayout from "@/layouts/Main";
import { useDialog } from "@/contexts/DialogContext";
import { DeleteIcon, EditIcon, PlusIcon } from "@/components/icons";
import { DataTable } from "@/components/DataTable";

const PlansPage = () => {
  const { confirm } = useDialog();
  // 分页和搜索状态
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [orderBy, setOrderBy] = useState("id");
  const [order, setOrder] = useState<SortOrder>(SortOrder.ASC);

  // 模态框状态
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PlanResponse | null>(null);

  // 表单状态
  const [newPlan, setNewPlan] = useState<PlanCreate>({
    name: "",
    description: "",
    rpm: 60,
    rpd: 1000,
    is_default: false,
  });
  const [isLoading, setIsLoading] = useState(false);

  // 排序状态
  const [sortDescriptor, setSortDescriptor] = useState<SortDescriptor>({
    column: orderBy,
    direction: order === SortOrder.ASC ? "ascending" : "descending",
  });

  // 处理排序
  const handleSort = (descriptor: SortDescriptor) => {
    setSortDescriptor(descriptor);
    setOrderBy(descriptor.column?.toString() || "id");
    setOrder(
      descriptor.direction === "ascending" ? SortOrder.ASC : SortOrder.DESC,
    );
  };

  // 获取计划列表
  const {
    data: plans,
    isLoading: isLoadingPlans,
    error: plansError,
    refetch,
  } = useCustomQuery<PageResponse<PlanResponse>>(
    ["plans", page, pageSize, searchTerm, orderBy, order],
    () =>
      planApi.getPlans({
        page,
        size: pageSize,
        search: searchTerm,
        order_by: orderBy,
        order,
      }),
    { staleTime: 30000 },
  );

  // 创建计划
  const createPlanMutation = useCustomMutation<PlanResponse, PlanCreate>(
    (data) => planApi.createPlan(data),
    {
      onSuccess: () => {
        refetch();
        setIsCreateModalOpen(false);
        setNewPlan({
          name: "",
          description: "",
          rpm: 60,
          rpd: 1000,
          is_default: false,
        });
        setIsLoading(false);
      },
      onError: (err) => {
        addToast({
          title: "创建计划失败",
          description: (err as EnhancedAxiosError).detail || "创建计划失败",
          color: "danger",
        });
        setIsLoading(false);
      },
    },
  );

  // 更新计划
  const updatePlanMutation = useCustomMutation<
    PlanResponse,
    { id: number; data: PlanUpdate }
  >(({ id, data }) => planApi.updatePlan(id, data), {
    onSuccess: () => {
      refetch();
      setIsEditModalOpen(false);
      setEditingPlan(null);
      setIsLoading(false);
    },
    onError: (err) => {
      addToast({
        title: "更新计划失败",
        description: (err as EnhancedAxiosError).detail || "更新计划失败",
        color: "danger",
      });
      setIsLoading(false);
    },
  });

  // 删除计划
  const deletePlanMutation = useCustomMutation<void, number>(
    (id) => planApi.deletePlan(id),
    {
      onSuccess: () => {
        refetch();
      },
    },
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

  // 处理创建计划
  const handleCreatePlan = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    createPlanMutation.mutate(newPlan);
  };

  // 处理更新计划
  const handleUpdatePlan = (e: React.FormEvent) => {
    e.preventDefault();

    if (!editingPlan) return;

    setIsLoading(true);
    updatePlanMutation.mutate({
      id: editingPlan.id,
      data: {
        name: editingPlan.name,
        description: editingPlan.description,
        rpm: editingPlan.rpm,
        rpd: editingPlan.rpd,
        is_default: editingPlan.is_default,
      },
    });
  };

  // 处理删除计划
  const handleDeletePlan = (id: number) => {
    confirm(
      "确定要删除此计划吗？此操作不可逆，且可能影响使用此计划的用户。",
      () => {
        deletePlanMutation.mutate(id);
      },
    );
  };

  // 打开编辑模态框
  const openEditModal = (plan: PlanResponse) => {
    setEditingPlan(plan);
    setIsEditModalOpen(true);
  };

  // 定义表格列
  const columns = [
    { key: "id", label: "ID", allowsSorting: true },
    { key: "name", label: "名称", allowsSorting: true },
    { key: "rpm", label: "每分钟请求数", allowsSorting: true },
    { key: "rpd", label: "每天请求数", allowsSorting: true },
    { key: "is_default", label: "默认计划", allowsSorting: true },
    { key: "actions", label: "操作" },
  ];

  // 渲染单元格内容
  const renderCell = (plan: PlanResponse, columnKey: string) => {
    switch (columnKey) {
      case "id":
        return plan.id;
      case "name":
        return (
          <span className="whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
            {plan.name}
          </span>
        );
      case "rpm":
        return plan.rpm;
      case "rpd":
        return plan.rpd;
      case "is_default":
        return plan.is_default ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100">
            是
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100">
            否
          </span>
        );
      case "actions":
        return (
          <div className="relative flex items-center gap-2">
            <Tooltip content="编辑">
              <Button
                isIconOnly
                className="text-default-400 active:opacity-50 text-lg"
                variant="light"
                onPress={() => openEditModal(plan)}
              >
                <EditIcon />
              </Button>
            </Tooltip>
            <Tooltip color="danger" content="删除">
              <Button
                isIconOnly
                className="text-default-400 active:opacity-50 text-lg"
                variant="light"
                onPress={() => handleDeletePlan(plan.id)}
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
    <DashboardLayout current_root_href="/plans">
      <DataTable<PlanResponse>
        addButtonProps={{
          tooltip: "创建计划",
          onClick: () => setIsCreateModalOpen(true),
          isIconOnly: true,
        }}
        autoSearchDelay={1000}
        columns={columns}
        data={plans?.items || []}
        emptyContent={
          <>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              暂无计划数据
            </p>
            <Tooltip
              color="primary"
              content="创建第一个计划"
              placement="bottom"
            >
              <Button
                isIconOnly
                className="mt-4"
                color="primary"
                onPress={() => setIsCreateModalOpen(true)}
              >
                <PlusIcon />
              </Button>
            </Tooltip>
          </>
        }
        error={plansError}
        isLoading={isLoadingPlans}
        page={page}
        pageSize={pageSize}
        pages={Math.ceil((plans?.total || 0) / pageSize)}
        renderCell={renderCell}
        searchPlaceholder="搜索计划..."
        searchTerm={searchTerm}
        selectedSize={pageSize}
        setSearchTerm={setSearchTerm}
        setSize={setPageSize}
        sortDescriptor={sortDescriptor}
        title="计划列表"
        total={plans?.total}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
        onSortChange={handleSort}
      />

      {/* 创建计划对话框 */}
      <Modal
        isOpen={isCreateModalOpen}
        placement="center"
        onClose={() => !isLoading && setIsCreateModalOpen(false)}
      >
        <ModalContent>
          {(onClose) => (
            <Form className="w-full" onSubmit={handleCreatePlan}>
              <ModalHeader>创建新计划</ModalHeader>
              <ModalBody className="w-full">
                <Input
                  fullWidth
                  isRequired
                  label="计划名称"
                  placeholder="输入计划名称"
                  value={newPlan.name}
                  onChange={(e) =>
                    setNewPlan({
                      ...newPlan,
                      name: e.target.value,
                    })
                  }
                />
                <Input
                  fullWidth
                  isRequired
                  label="描述"
                  placeholder="输入计划描述"
                  value={newPlan.description}
                  onChange={(e) =>
                    setNewPlan({
                      ...newPlan,
                      description: e.target.value,
                    })
                  }
                />
                <Input
                  fullWidth
                  isRequired
                  errorMessage={({ validationErrors }) => {
                    return validationErrors;
                  }}
                  label="每分钟请求数 (RPM)"
                  max={1000000}
                  min={0}
                  placeholder="输入每分钟请求数限制"
                  type="number"
                  value={newPlan.rpm.toString()}
                  onChange={(e) =>
                    setNewPlan({
                      ...newPlan,
                      rpm: parseInt(e.target.value),
                    })
                  }
                />
                <Input
                  fullWidth
                  isRequired
                  errorMessage={({ validationErrors }) => {
                    return validationErrors;
                  }}
                  label="每天请求数 (RPD)"
                  max={1000000}
                  min={0}
                  placeholder="输入每天请求数限制"
                  type="number"
                  value={newPlan.rpd.toString()}
                  onChange={(e) =>
                    setNewPlan({
                      ...newPlan,
                      rpd: parseInt(e.target.value),
                    })
                  }
                />
                <Checkbox
                  isSelected={newPlan.is_default}
                  onValueChange={(isSelected) =>
                    setNewPlan({
                      ...newPlan,
                      is_default: isSelected,
                    })
                  }
                >
                  设为默认计划
                </Checkbox>
              </ModalBody>
              <ModalFooter className="w-full">
                <Button disabled={isLoading} variant="light" onPress={onClose}>
                  取消
                </Button>
                <Button color="primary" isLoading={isLoading} type="submit">
                  创建
                </Button>
              </ModalFooter>
            </Form>
          )}
        </ModalContent>
      </Modal>

      {/* 编辑计划对话框 */}
      <Modal
        isOpen={isEditModalOpen}
        placement="center"
        onClose={() => !isLoading && setIsEditModalOpen(false)}
      >
        <ModalContent>
          {(onClose) => (
            <Form className="w-full" onSubmit={handleUpdatePlan}>
              <ModalHeader>编辑计划</ModalHeader>
              <ModalBody className="w-full">
                {editingPlan && (
                  <div className="space-y-4">
                    <Input
                      fullWidth
                      isRequired
                      label="计划名称"
                      placeholder="输入计划名称"
                      value={editingPlan.name}
                      onChange={(e) =>
                        setEditingPlan({
                          ...editingPlan,
                          name: e.target.value,
                        })
                      }
                    />
                    <Input
                      fullWidth
                      isRequired
                      label="描述"
                      placeholder="输入计划描述"
                      value={editingPlan.description || ""}
                      onChange={(e) =>
                        setEditingPlan({
                          ...editingPlan,
                          description: e.target.value,
                        })
                      }
                    />
                    <Input
                      fullWidth
                      isRequired
                      errorMessage={({ validationErrors }) => {
                        return validationErrors;
                      }}
                      label="每分钟请求数 (RPM)"
                      max={1000000}
                      min={0}
                      placeholder="输入每分钟请求数限制"
                      type="number"
                      value={editingPlan.rpm.toString()}
                      onChange={(e) =>
                        setEditingPlan({
                          ...editingPlan,
                          rpm: parseInt(e.target.value),
                        })
                      }
                    />
                    <Input
                      fullWidth
                      isRequired
                      errorMessage={({ validationErrors }) => {
                        return validationErrors;
                      }}
                      label="每天请求数 (RPD)"
                      max={1000000}
                      min={0}
                      placeholder="输入每天请求数限制"
                      type="number"
                      value={editingPlan.rpd.toString()}
                      onChange={(e) =>
                        setEditingPlan({
                          ...editingPlan,
                          rpd: parseInt(e.target.value),
                        })
                      }
                    />
                    <Checkbox
                      isSelected={editingPlan.is_default}
                      onValueChange={(isSelected) =>
                        setEditingPlan({
                          ...editingPlan,
                          is_default: isSelected,
                        })
                      }
                    >
                      设为默认计划
                    </Checkbox>
                  </div>
                )}
              </ModalBody>
              <ModalFooter className="w-full">
                <Button disabled={isLoading} variant="light" onPress={onClose}>
                  取消
                </Button>
                <Button color="primary" isLoading={isLoading} type="submit">
                  保存
                </Button>
              </ModalFooter>
            </Form>
          )}
        </ModalContent>
      </Modal>
    </DashboardLayout>
  );
};

export default PlansPage;
