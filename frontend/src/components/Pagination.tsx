import React from "react";
import { Pagination as HeroUIPagination } from "@heroui/pagination";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
  props?: PaginationProps;
}

const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  props,
}: PaginationProps) => {
  // 如果只有一页，不显示分页
  if (totalPages <= 1) return null;

  return (
    <>
      <div>
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
      </div>
    </>
  );
};

export default Pagination;
