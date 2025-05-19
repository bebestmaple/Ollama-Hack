import { useState } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import { Form } from "@heroui/form";
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
  addToast,
  Chip,
  Select,
  SelectItem,
} from "@heroui/react";

import { useCustomQuery, useCustomMutation } from "@/hooks";
import { useAuth } from "@/contexts/AuthContext";
import { authApi, planApi, EnhancedAxiosError } from "@/api";
import {
  UserAuth,
  UserInfo,
  UserUpdate,
  PageResponse,
  SortOrder,
  PlanResponse,
} from "@/types";
import DashboardLayout from "@/layouts/Main";
import { DeleteIcon, EditIcon, PlusIcon } from "@/components/icons";
import { DataTable } from "@/components/DataTable";
import { useDialog } from "@/contexts/DialogContext";

const UsersPage = () => {
  const { user: currentUser, isAdmin } = useAuth();
  const { confirm } = useDialog();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [orderBy, setOrderBy] = useState<string | undefined>();
  const [order, setOrder] = useState<SortOrder | undefined>();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newUser, setNewUser] = useState({
    username: "",
    password: "",
    is_admin: false,
  });
  const [isCreating, setIsCreating] = useState(false);

  // 编辑Modal相关状态
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserUpdate>({
    username: "",
    is_admin: false,
    plan_id: undefined,
  });
  const [editingUserId, setEditingUserId] = useState<number | undefined>();
  const [isUpdating, setIsUpdating] = useState(false);

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

  // 获取用户列表
  const {
    data: users,
    isLoading,
    error: usersError,
    refetch,
  } = useCustomQuery<PageResponse<UserInfo>>(
    ["users", page, pageSize, searchTerm, orderBy, order],
    () =>
      authApi.getUsers({
        page,
        size: pageSize,
        search: searchTerm,
        order_by: orderBy,
        order,
      }),
    {
      staleTime: 30000,
      enabled: isAdmin,
    },
  );

  // 获取所有计划列表（用于编辑用户时选择计划）
  const { data: plans, isLoading: isLoadingPlans } = useCustomQuery<
    PageResponse<PlanResponse>
  >(
    ["plans-for-users", 1, 50],
    () =>
      planApi.getPlans({
        page: 1,
        size: 50,
      }),
    {
      staleTime: 60000,
      enabled: isAdmin,
    },
  );

  // 创建用户
  const createUserMutation = useCustomMutation<UserInfo, UserAuth>(
    (data) => {
      return authApi.createUser(data);
    },
    {
      onSuccess: () => {
        refetch();
        setIsCreateModalOpen(false);
        setNewUser({ username: "", password: "", is_admin: false });
        setIsCreating(false);
      },
      onError: (err) => {
        addToast({
          title: "创建用户失败",
          description: (err as EnhancedAxiosError).detail || "创建用户失败",
          color: "danger",
        });
        setIsCreating(false);
      },
    },
  );

  // 更新用户
  const updateUserMutation = useCustomMutation<
    UserInfo,
    { id: number; data: UserUpdate }
  >(({ id, data }) => authApi.updateUser(id, data), {
    onSuccess: () => {
      refetch();
      setIsEditModalOpen(false);
      setEditingUser({
        username: "",
        is_admin: false,
        plan_id: undefined,
      });
      setEditingUserId(undefined);
      setIsUpdating(false);
      addToast({
        title: "更新用户成功",
        description: "用户信息已成功更新",
        color: "success",
      });
    },
    onError: (err) => {
      addToast({
        title: "更新用户失败",
        description: (err as EnhancedAxiosError).detail || "更新用户失败",
        color: "danger",
      });
      setIsUpdating(false);
    },
  });

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

  // 处理创建用户
  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();

    if (!newUser.username || !newUser.password) {
      addToast({
        title: "创建用户失败",
        description: "用户名和密码不能为空",
        color: "danger",
      });

      return;
    }

    setIsCreating(true);
    createUserMutation.mutate({
      username: newUser.username,
      password: newUser.password,
    });
  };

  const handleDeleteUser = async (userId: number) => {
    confirm(
      "确定要删除此用户吗？此操作不可逆，且可能影响使用此用户的服务。",
      async () => {
        await authApi.deleteUser(userId);
        refetch();
        addToast({
          title: "删除用户成功",
          description: "用户已成功删除",
          color: "success",
        });
      },
    );
  };

  // 打开编辑模态框
  const openEditModal = (user: UserInfo) => {
    setEditingUser({
      username: user.username,
      is_admin: user.is_admin,
      plan_id: user.plan_id,
    });
    setEditingUserId(user.id);
    setIsEditModalOpen(true);
  };

  // 处理表单输入变化
  const handleEditInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setEditingUser((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // 处理复选框变化
  const handleCheckboxChange = (isSelected: boolean) => {
    setEditingUser((prev) => ({
      ...prev,
      is_admin: isSelected,
    }));
  };

  // 处理计划选择变化
  const handlePlanChange = (planId: string) => {
    const numericPlanId = planId === "" ? undefined : Number(planId);

    setEditingUser((prev) => ({
      ...prev,
      plan_id: numericPlanId,
    }));
  };

  // 处理编辑表单提交
  const handleUpdateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUserId) return;

    // 验证表单
    if (!editingUser.username) {
      addToast({
        title: "更新用户失败",
        description: "用户名不能为空",
        color: "danger",
      });

      return;
    }

    setIsUpdating(true);
    const updateData: UserUpdate = {
      username: editingUser.username,
      is_admin: editingUser.is_admin,
      plan_id: editingUser.plan_id,
    };

    // 只有当密码字段有值时才包含密码
    if (editingUser.password) {
      updateData.password = editingUser.password;
    }

    updateUserMutation.mutate({
      id: editingUserId,
      data: updateData,
    });
  };

  // 关闭编辑模态框
  const handleCloseEditModal = () => {
    if (!isUpdating) {
      setIsEditModalOpen(false);
      setEditingUser({
        username: "",
        is_admin: false,
        plan_id: undefined,
      });
      setEditingUserId(undefined);
    }
  };

  // 定义表格列
  const columns = [
    { key: "id", label: "ID", allowsSorting: true },
    { key: "username", label: "用户名", allowsSorting: true },
    { key: "is_admin", label: "角色", allowsSorting: true },
    { key: "plan_id", label: "计划", allowsSorting: true },
    { key: "actions", label: "操作" },
  ];

  // 渲染单元格内容
  const renderCell = (user: UserInfo, columnKey: string) => {
    switch (columnKey) {
      case "id":
        return user.id;
      case "username":
        return <span>{user.username}</span>;
      case "is_admin":
        return user.is_admin ? (
          <Chip color="primary" variant="flat">
            管理员
          </Chip>
        ) : (
          <Chip color="default" variant="flat">
            普通用户
          </Chip>
        );
      case "plan_id":
        return user.plan_name || "-";
      case "actions":
        return (
          <div className="relative flex items-center gap-2">
            <Tooltip content="编辑用户">
              <Button
                isIconOnly
                className="text-default-400 active:opacity-50 text-lg"
                variant="light"
                onPress={() => openEditModal(user)}
              >
                <EditIcon />
              </Button>
            </Tooltip>
            {user?.id !== currentUser?.id && isAdmin && (
              <Tooltip content="删除用户">
                <Button
                  isIconOnly
                  className="text-default-400 active:opacity-50 text-lg"
                  variant="light"
                  onPress={() => handleDeleteUser(user.id)}
                >
                  <DeleteIcon />
                </Button>
              </Tooltip>
            )}
          </div>
        );
      default:
        return null;
    }
  };

  if (!isAdmin) {
    return (
      <DashboardLayout current_root_href="/users">
        <div className="p-8 text-center">
          <h2 className="text-xl font-semibold mb-4">权限不足</h2>
          <p className="text-gray-600 dark:text-gray-400">
            您没有权限访问此页面
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout current_root_href="/users">
      <DataTable<UserInfo>
        addButtonProps={{
          tooltip: "创建用户",
          onClick: () => setIsCreateModalOpen(true),
          isIconOnly: true,
        }}
        autoSearchDelay={1000}
        columns={columns}
        data={users?.items || []}
        emptyContent={
          <>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              暂无用户数据
            </p>
            <Tooltip
              color="primary"
              content="创建第一个用户"
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
        error={usersError}
        isLoading={isLoading}
        page={page}
        pageSize={pageSize}
        pages={Math.ceil((users?.total || 0) / pageSize)}
        renderCell={renderCell}
        searchPlaceholder="搜索用户..."
        searchTerm={searchTerm}
        selectedSize={pageSize}
        setSearchTerm={setSearchTerm}
        setSize={setPageSize}
        sortDescriptor={sortDescriptor}
        title="用户列表"
        total={users?.total}
        onPageChange={handlePageChange}
        onSearch={handleSearch}
        onSortChange={handleSort}
      />

      {/* 创建用户对话框 */}
      <Modal
        isOpen={isCreateModalOpen}
        placement="center"
        onClose={() => !isCreating && setIsCreateModalOpen(false)}
      >
        <ModalContent>
          {(onClose) => (
            <Form className="w-full" onSubmit={handleCreateUser}>
              <ModalHeader>创建新用户</ModalHeader>
              <ModalBody className="w-full">
                <Input
                  fullWidth
                  isRequired
                  label="用户名"
                  maxLength={128}
                  minLength={3}
                  placeholder="输入用户名"
                  value={newUser.username}
                  onChange={(e) =>
                    setNewUser({
                      ...newUser,
                      username: e.target.value,
                    })
                  }
                />
                <Input
                  fullWidth
                  isRequired
                  errorMessage={({ validationErrors }) => validationErrors}
                  label="密码"
                  maxLength={128}
                  minLength={8}
                  placeholder="输入密码"
                  type="password"
                  value={newUser.password}
                  onChange={(e) =>
                    setNewUser({
                      ...newUser,
                      password: e.target.value,
                    })
                  }
                />
                <Checkbox
                  isSelected={newUser.is_admin}
                  onValueChange={(e) =>
                    setNewUser({
                      ...newUser,
                      is_admin: e,
                    })
                  }
                >
                  设为管理员
                </Checkbox>
              </ModalBody>
              <ModalFooter className="w-full">
                <Button disabled={isCreating} variant="light" onPress={onClose}>
                  取消
                </Button>
                <Button color="primary" isLoading={isCreating} type="submit">
                  创建
                </Button>
              </ModalFooter>
            </Form>
          )}
        </ModalContent>
      </Modal>

      {/* 编辑用户对话框 */}
      <Modal
        isOpen={isEditModalOpen}
        placement="center"
        onClose={handleCloseEditModal}
      >
        <ModalContent>
          <Form className="w-full" onSubmit={handleUpdateUser}>
            <ModalHeader>编辑用户</ModalHeader>
            <ModalBody className="w-full">
              <div className="space-y-4">
                <Input
                  fullWidth
                  isRequired
                  label="用户名"
                  maxLength={128}
                  minLength={3}
                  name="username"
                  placeholder="输入用户名"
                  value={editingUser.username}
                  onChange={handleEditInputChange}
                />
                <Input
                  fullWidth
                  description="留空则不修改密码"
                  label="密码"
                  maxLength={128}
                  minLength={8}
                  name="password"
                  placeholder="输入新密码"
                  type="password"
                  value={editingUser.password || ""}
                  onChange={handleEditInputChange}
                />
                <Select
                  label="关联计划"
                  placeholder="选择计划"
                  selectedKeys={
                    editingUser.plan_id ? [editingUser.plan_id.toString()] : []
                  }
                  onChange={(e) => handlePlanChange(e.target.value)}
                >
                  {isLoadingPlans ? (
                    <SelectItem key="loading" value="loading">
                      加载中...
                    </SelectItem>
                  ) : (
                    plans?.items?.map((plan) => (
                      <SelectItem
                        key={plan.id.toString()}
                        value={plan.id.toString()}
                      >
                        {plan.name}
                      </SelectItem>
                    ))
                  )}
                </Select>
                <Checkbox
                  isSelected={editingUser.is_admin}
                  onValueChange={handleCheckboxChange}
                >
                  设为管理员
                </Checkbox>
              </div>
            </ModalBody>
            <ModalFooter className="w-full">
              <Button
                disabled={isUpdating}
                variant="light"
                onPress={handleCloseEditModal}
              >
                取消
              </Button>
              <Button
                color="primary"
                disabled={isUpdating}
                isLoading={isUpdating}
                type="submit"
              >
                {isUpdating ? (
                  <>
                    <span className="ml-2">保存中...</span>
                  </>
                ) : (
                  "保存更改"
                )}
              </Button>
            </ModalFooter>
          </Form>
        </ModalContent>
      </Modal>
    </DashboardLayout>
  );
};

export default UsersPage;
