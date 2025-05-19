import { useState, useEffect } from "react";
import { Button } from "@heroui/button";
import { Input } from "@heroui/input";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from "@heroui/modal";
import { addToast, Form } from "@heroui/react";

import { endpointApi, EnhancedAxiosError } from "@/api";
import { EndpointUpdate } from "@/types";
import LoadingSpinner from "@/components/LoadingSpinner";

interface EndpointEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  endpointId: number | undefined;
  endpointName: string;
  endpointUrl: string;
  onDelete?: (id: number) => void;
}

const EndpointEditModal = ({
  isOpen,
  onClose,
  onSuccess,
  endpointId,
  endpointName,
  endpointUrl,
}: EndpointEditModalProps) => {
  // 表单状态
  const [formData, setFormData] = useState<EndpointUpdate>({
    name: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 当 props 变化时更新表单数据
  useEffect(() => {
    if (endpointName) {
      setFormData({
        name: endpointName,
      });
    }
  }, [endpointName, isOpen]);

  // 关闭时重置状态
  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  // 处理表单输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!endpointId) return;

    setIsSubmitting(true);

    try {
      // 表单验证
      if (!formData.name) {
        throw new Error("名称不能为空");
      }

      // 提交更新请求
      await endpointApi.updateEndpoint(endpointId, formData);

      // 更新成功，关闭模态框
      setIsSubmitting(false);
      onSuccess();
      handleClose();
    } catch (err) {
      addToast({
        title: "更新端点失败",
        description: (err as EnhancedAxiosError).detail || "更新端点失败",
        color: "danger",
      });
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} placement="center" onClose={handleClose}>
      <ModalContent>
        <Form className="w-full" onSubmit={handleSubmit}>
          <ModalHeader>编辑端点</ModalHeader>
          <ModalBody className="w-full">
            <div className="space-y-4">
              <div className="mb-4">
                <Input
                  disabled
                  className="w-full"
                  description="端点 URL 不可修改"
                  id="url"
                  label="端点 URL"
                  value={endpointUrl}
                />
              </div>

              <div className="mb-6">
                <Input
                  className="w-full"
                  description="端点名称"
                  id="name"
                  label="端点名称"
                  name="name"
                  placeholder="端点名称"
                  value={formData.name}
                  onChange={handleInputChange}
                />
              </div>
            </div>
          </ModalBody>
          <ModalFooter className="w-full">
            <Button
              color="primary"
              disabled={isSubmitting}
              isLoading={isSubmitting}
              type="submit"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="small" />
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
  );
};

export default EndpointEditModal;
