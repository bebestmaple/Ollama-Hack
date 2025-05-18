import React from "react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from "@heroui/modal";
import { Button } from "@heroui/button";

export type DialogType = "error" | "confirm";

interface DialogModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  type: DialogType;
  onConfirm?: () => void;
}

/**
 * 对话框组件，支持错误提示和确认对话框
 */
const DialogModal: React.FC<DialogModalProps> = ({
  isOpen,
  onClose,
  title,
  message,
  type,
  onConfirm,
}) => {
  const defaultTitle = type === "error" ? "操作失败" : "确认操作";

  return (
    <Modal
      hideCloseButton={false}
      isDismissable={type === "error"}
      isOpen={isOpen}
      placement="center"
      size="sm"
      onClose={onClose}
    >
      <ModalContent>
        <ModalHeader
          className={`flex flex-col gap-1 ${type === "error" ? "text-red-600" : type === "confirm" ? "text-blue-600" : ""}`}
        >
          {title || defaultTitle}
        </ModalHeader>
        <ModalBody>
          <p>{message}</p>
        </ModalBody>
        <ModalFooter>
          {type === "error" ? (
            <Button
              className="w-full"
              color="danger"
              variant="light"
              onPress={onClose}
            >
              关闭
            </Button>
          ) : (
            <div className="flex w-full justify-end gap-2">
              <Button variant="flat" onPress={onClose}>
                取消
              </Button>
              <Button
                color="primary"
                onPress={() => {
                  if (onConfirm) onConfirm();
                  onClose();
                }}
              >
                确认
              </Button>
            </div>
          )}
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default DialogModal;
