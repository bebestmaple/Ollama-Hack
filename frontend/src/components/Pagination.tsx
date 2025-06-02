import React, { useState, KeyboardEvent } from "react";
import { Pagination as HeroUIPagination } from "@heroui/pagination";
import { NumberInput } from "@heroui/number-input";
import { Button } from "@heroui/button";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
  props?: PaginationProps;
  showJumper?: boolean; // 是否显示跳转输入框
}

const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  props,
  showJumper = true, // 默认显示跳转输入框
}: PaginationProps) => {
  // 页码输入状态
  const [jumpValue, setJumpValue] = useState<number | null>(null);

  // 如果只有一页，不显示分页
  if (totalPages <= 1) return null;

  // 处理跳转
  const handleJump = () => {
    if (jumpValue !== null) {
      // NumberInput已经确保了值在范围内
      if (
        jumpValue >= 1 &&
        jumpValue <= totalPages &&
        jumpValue !== currentPage
      ) {
        onPageChange(jumpValue);
      }
      // 跳转后清空输入框
      setJumpValue(null);
    }
  };

  // 处理回车键跳转
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleJump();
    }
  };

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <HeroUIPagination
          showControls
          color="primary"
          page={currentPage}
          radius="md"
          size="md"
          total={totalPages}
          onChange={onPageChange}
          {...props}
          classNames={
            {
              // wrapper: "gap-1",
              // prev: "text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900",
              // next: "text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900",
              // item: "text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-900",
              // cursor: "bg-primary-500 text-white",
            }
          }
        />

        {/* 页码跳转输入框 */}
        {showJumper && totalPages > 5 && (
          <div className="items-center ml-2 gap-1 hidden sm:flex">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              前往
            </span>
            <NumberInput
              hideStepper
              className="w-16"
              classNames={{
                mainWrapper: "h-8",
                input: "h-8",
                inputWrapper: "h-8 min-h-8",
              }}
              maxValue={totalPages}
              minValue={1}
              placeholder={currentPage.toString()}
              radius="sm"
              size="sm"
              value={jumpValue}
              onKeyDown={handleKeyDown}
              onValueChange={(value) => setJumpValue(value)}
            />
            <span className="text-sm text-gray-500 dark:text-gray-400">页</span>
            <Button
              color="primary"
              size="sm"
              variant="light"
              onClick={handleJump}
            >
              跳转
            </Button>
          </div>
        )}
      </div>
    </>
  );
};

export default Pagination;
