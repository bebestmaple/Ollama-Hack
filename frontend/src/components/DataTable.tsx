import React, { ReactNode, useState } from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableColumn,
  TableRow,
  TableCell,
  SortDescriptor,
  Selection,
} from "@heroui/table";
import { Button } from "@heroui/button";
import {
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from "@heroui/dropdown";
import { Pagination } from "@heroui/pagination";
import { Tooltip } from "@heroui/tooltip";

import LoadingSpinner from "./LoadingSpinner";
import ErrorDisplay from "./ErrorDisplay";
import SearchForm from "./SearchForm";
import { PlusIcon } from "./icons";

// ChevronDownIcon组件
const ChevronDownIcon = ({
  strokeWidth = 1.5,
  ...otherProps
}: { strokeWidth?: number } & React.SVGProps<SVGSVGElement>) => {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      focusable="false"
      height="1em"
      role="presentation"
      viewBox="0 0 24 24"
      width="1em"
      {...otherProps}
    >
      <path
        d="m19.92 8.95-6.52 6.52c-.77.77-2.03.77-2.8 0L4.08 8.95"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeMiterlimit={10}
        strokeWidth={strokeWidth}
      />
    </svg>
  );
};

// 列定义类型
export interface Column {
  key: string;
  label: string;
  allowsSorting?: boolean;
}

// 添加按钮属性类型
export interface AddButtonProps {
  tooltip?: string;
  onClick: () => void;
  label?: string;
  isIconOnly?: boolean;
}

// DataTable组件属性类型
export interface DataTableProps<T> {
  title: string;
  columns: Column[];
  data: T[];
  total?: number;
  page: number;
  pages?: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
  sortDescriptor: SortDescriptor;
  onSortChange: (descriptor: SortDescriptor) => void;
  isLoading?: boolean;
  error?: Error;
  searchTerm?: string;
  searchPlaceholder?: string;
  onSearch?: (e: React.FormEvent) => void;
  setSearchTerm?: (value: string) => void;
  renderCell: (item: T, columnKey: string) => ReactNode;
  emptyContent?: ReactNode;
  addButtonProps?: AddButtonProps;
  visibleColumns?: Selection;
  setVisibleColumns?: (selection: Selection) => void;
  selectedSize?: number;
  setSize?: (size: number) => void;
  autoSearchDelay?: number;
  removeWrapper?: boolean;
  topActionContent?: ReactNode;
}

// 通用DataTable组件
export const DataTable = <T extends { id?: number | string }>({
  title,
  columns,
  data,
  total,
  page,
  pages = 1,
  pageSize = 10,
  onPageChange,
  sortDescriptor,
  onSortChange,
  isLoading = false,
  error,
  searchTerm = "",
  searchPlaceholder = "搜索...",
  onSearch,
  setSearchTerm,
  renderCell,
  emptyContent,
  addButtonProps,
  visibleColumns = new Set(columns.map((col) => col.key)),
  setVisibleColumns,
  selectedSize = pageSize,
  setSize,
  autoSearchDelay = 0,
  removeWrapper = false,
  topActionContent,
}: DataTableProps<T>) => {
  // 获取表头列
  const headerColumns = React.useMemo(() => {
    if (visibleColumns === "all") return columns;

    return columns.filter((column) =>
      Array.from(visibleColumns).includes(column.key),
    );
  }, [visibleColumns, columns]);

  // 每页行数
  const pageSizeOptions = [5, 10, 15];
  const [selectedKeys, setSelectedKeys] = useState(
    new Set([selectedSize.toString()]),
  );

  // 底部内容区域
  const bottomContent = React.useMemo(() => {
    return (
      pages > 1 && (
        <div className="py-2 px-2 flex justify-between items-center flex-wrap gap-2">
          {setSize && (
            <Dropdown>
              <DropdownTrigger className="hidden sm:flex">
                <Button
                  className="text-default-400 text-small"
                  endContent={<ChevronDownIcon className="text-small" />}
                  variant="light"
                >
                  每页行数: {selectedSize}
                </Button>
              </DropdownTrigger>
              <DropdownMenu
                disallowEmptySelection
                aria-label="每页行数"
                closeOnSelect={true}
                selectedKeys={selectedKeys}
                selectionMode="single"
                onSelectionChange={(e) => {
                  setSize(Number(e.currentKey));
                  setSelectedKeys(new Set([e.currentKey]));
                  setPage(1);
                }}
              >
                {pageSizeOptions.map((size) => (
                  <DropdownItem key={size}>{size}</DropdownItem>
                ))}
              </DropdownMenu>
            </Dropdown>
          )}
          <Pagination
            isCompact
            showControls
            showShadow
            color="primary"
            page={page}
            total={pages}
            onChange={onPageChange}
          />
          <span className="text-default-400 text-small">
            共 {total || data.length} 条记录
          </span>
        </div>
      )
    );
  }, [
    pages,
    page,
    onPageChange,
    selectedSize,
    setSize,
    total,
    data.length,
    pageSize,
  ]);

  // 顶部内容区域
  const topContent = React.useMemo(() => {
    return (
      <div className="flex justify-between gap-3 items-end">
        {setSearchTerm && onSearch && (
          <SearchForm
            autoSearchDelay={autoSearchDelay}
            handleSearch={onSearch}
            placeholder={searchPlaceholder}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
          />
        )}
        <div className="flex gap-3">
          {setVisibleColumns && (
            <Dropdown>
              <DropdownTrigger className="hidden sm:flex">
                <Button
                  endContent={<ChevronDownIcon className="text-small" />}
                  variant="flat"
                >
                  选择列
                </Button>
              </DropdownTrigger>
              <DropdownMenu
                disallowEmptySelection
                aria-label="显示的列"
                closeOnSelect={false}
                selectedKeys={visibleColumns}
                selectionMode="multiple"
                onSelectionChange={setVisibleColumns}
              >
                {columns.map((column) => (
                  <DropdownItem key={column.key} className="capitalize">
                    {column.label}
                  </DropdownItem>
                ))}
              </DropdownMenu>
            </Dropdown>
          )}
          {topActionContent}
          {addButtonProps && (
            <Tooltip color="primary" content={addButtonProps.tooltip || "添加"}>
              <Button
                color="primary"
                isIconOnly={addButtonProps.isIconOnly || false}
                onPress={addButtonProps.onClick}
              >
                {addButtonProps.label || <PlusIcon />}
              </Button>
            </Tooltip>
          )}
        </div>
      </div>
    );
  }, [
    searchTerm,
    searchPlaceholder,
    setSearchTerm,
    onSearch,
    columns,
    visibleColumns,
    setVisibleColumns,
    addButtonProps,
    autoSearchDelay,
  ]);

  // 渲染表格
  const renderTable = () => (
    <Table
      isHeaderSticky
      aria-label={title}
      bottomContent={bottomContent}
      bottomContentPlacement="outside"
      // classNames={{
      //   wrapper: "max-h-[600px]",
      // }}
      removeWrapper={removeWrapper}
      sortDescriptor={sortDescriptor}
      topContent={topContent}
      topContentPlacement="outside"
      onSortChange={onSortChange}
    >
      <TableHeader columns={headerColumns}>
        {(column) => (
          <TableColumn key={column.key} allowsSorting={column.allowsSorting}>
            {column.label}
          </TableColumn>
        )}
      </TableHeader>
      <TableBody
        emptyContent={emptyContent || <p className="text-xl">暂无数据</p>}
        isLoading={isLoading}
        items={data}
        loadingContent={
          <div className="flex justify-center py-8">
            <LoadingSpinner size="large" />
          </div>
        }
      >
        {(item) => (
          <TableRow key={item.id?.toString()}>
            {(columnKey) => (
              <TableCell>{renderCell(item, columnKey.toString())}</TableCell>
            )}
          </TableRow>
        )}
      </TableBody>
    </Table>
  );

  // 主要渲染逻辑
  return (
    <div className="w-full">
      {error ? (
        <ErrorDisplay error={new Error(error?.message || `加载${title}失败`)} />
      ) : (
        renderTable()
      )}
    </div>
  );
};
