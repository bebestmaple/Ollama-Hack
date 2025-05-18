import { Card, CardBody } from "@heroui/card";
import { Chip } from "@heroui/chip";
import { Tooltip } from "@heroui/tooltip";

import { EndpointStatusEnum, AIModelStatusEnum } from "@/types";

// 通用状态接口
interface PerformanceStatus {
  status: EndpointStatusEnum | AIModelStatusEnum;
  created_at: string;
}

interface StatusTimelineProps<T extends PerformanceStatus> {
  performanceTests: T[];
  type?: "endpoint" | "model";
}

const StatusTimeline = <T extends PerformanceStatus>({
  performanceTests,
  type = "endpoint",
}: StatusTimelineProps<T>) => {
  // 最多显示10个状态
  const maxStatus = 10;

  // 获取胶囊颜色
  const getStatusColor = (
    status: EndpointStatusEnum | AIModelStatusEnum | undefined,
  ) => {
    switch (status) {
      case EndpointStatusEnum.AVAILABLE:
      case AIModelStatusEnum.AVAILABLE:
        return "success";
      case EndpointStatusEnum.UNAVAILABLE:
      case AIModelStatusEnum.UNAVAILABLE:
        return "danger";
      case EndpointStatusEnum.FAKE:
      case AIModelStatusEnum.FAKE:
        return "warning";
      case AIModelStatusEnum.MISSING:
        return "secondary";
      default:
        return "default";
    }
  };

  // 格式化日期时间
  const formatDateTime = (dateTimeStr: string) => {
    const date = new Date(dateTimeStr + "Z");

    return date.toLocaleString({
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  // 创建显示的状态数组
  const getStatusList = () => {
    // 复制并限制到最多10个项目
    const statusItems = [...performanceTests].slice(0, maxStatus);

    // 如果不足10个，用空状态填充
    const fillerCount = maxStatus - statusItems.length;
    const fillerItems = Array(fillerCount > 0 ? fillerCount : 0).fill(null);

    return [...statusItems, ...fillerItems];
  };

  return (
    <Card className="w-full" shadow="none">
      <CardBody className="flex flex-row items-center justify-center w-full">
        <div className="flex flex-row-reverse w-full justify-end items-center gap-2">
          {getStatusList().map((test, index) => (
            <Tooltip
              key={index}
              content={
                test ? (
                  <div className="text-sm flex flex-col gap-1 items-center">
                    {type === "model" && (
                      <span>
                        {test.token_per_second
                          ? `${test.token_per_second.toFixed(1)} tps`
                          : "0 tps"}
                      </span>
                    )}
                    <span>{formatDateTime(test.created_at)}</span>
                  </div>
                ) : (
                  "无数据"
                )
              }
              placement="top"
            >
              <Chip
                className="w-2 h-6 min-w-0 min-h-0 p-0"
                color={getStatusColor(test?.status)}
                variant="solid"
              />
            </Tooltip>
          ))}
        </div>
      </CardBody>
    </Card>
  );
};

export default StatusTimeline;
