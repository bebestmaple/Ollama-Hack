import React, { useState, useEffect } from "react";
import Chart from "react-apexcharts";
import { ApexOptions } from "apexcharts";
import { useTheme } from "@heroui/use-theme";

interface ChartData {
  date: string;
  count: number;
}

interface RequestsChartProps {
  data: ChartData[];
}

const RequestsChart: React.FC<RequestsChartProps> = ({ data }) => {
  const [mounted, setMounted] = useState(false);
  const { theme } = useTheme();

  // 页面加载后再渲染图表，避免SSR问题
  useEffect(() => {
    setMounted(true);
  }, []);

  // 检查并格式化数据
  const validData = data
    .filter(
      (item) => typeof item.date === "string" && typeof item.count === "number",
    )
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // 如果没有数据，显示提示信息
  if (validData.length === 0) {
    return (
      <div className="flex justify-center items-center h-full">
        <p className="text-gray-500 dark:text-gray-400">暂无数据</p>
      </div>
    );
  }

  // 格式化日期
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);

    // return `${date.getDate()}`;
    return `${date.getMonth() + 1}/${date.getDate()}`;
    // const currentDate = new Date();
    // if (date.getMonth() === currentDate.getMonth()) {
    //   return `${date.getDate()}`;
    // } else {
    //   return `${date.getMonth() + 1}/${date.getDate()}`;
    // }
  };

  // 准备ApexCharts所需的数据
  const series = [
    {
      name: "请求数",
      data: validData.map((item) => ({
        x: formatDate(item.date),
        y: item.count,
      })),
    },
  ];

  // ApexCharts配置
  const options: ApexOptions = {
    theme: {
      mode: theme,
    },
    chart: {
      height: "100%",
      maxWidth: "100%",
      type: "area",
      background: "transparent",
      fontFamily: "Inter, sans-serif",
      dropShadow: {
        enabled: false,
      },
      toolbar: {
        show: false,
      },
      zoom: {
        enabled: false,
      },
    },
    tooltip: {
      enabled: true,
      x: {
        show: false,
      },
    },
    fill: {
      type: "gradient",
      gradient: {
        opacityFrom: 0.55,
        opacityTo: 0,
        // shade: "#1C64F2",
        // gradientToColors: ["#1C64F2"],
      },
    },
    dataLabels: {
      enabled: false,
    },
    grid: {
      show: true,
      strokeDashArray: 4,
      borderColor: "hsl(var(--heroui-default-500))",
      padding: {
        left: 2,
        right: 2,
        top: -26,
      },
    },
    legend: {
      show: true,
    },
    stroke: {
      curve: "monotoneCubic",
      width: 2,
    },
    series: [
      {
        name: "请求数",
        data: validData.map((item) => item.count),
      },
    ],
    xaxis: {
      categories: validData.map((item) => item.date),
      labels: {
        show: false,
      },
      axisBorder: {
        show: true,
        color: "hsl(var(--heroui-default-500))",
      },
      axisTicks: {
        show: true,
        color: "hsl(var(--heroui-default-500))",
      },
    },
    yaxis: {
      show: true,
      labels: {
        show: true,
        style: {
          cssClass: "fill-default-500 mr-4",
        },
        offsetX: -4,
      },
    },
  };

  // 等待客户端渲染后再显示图表
  if (!mounted) return <div className="h-full w-full" />;

  return (
    <div className="h-full w-full">
      <Chart
        height="100%"
        options={options}
        series={series}
        type="area"
        width="100%"
      />
    </div>
  );
};

export default RequestsChart;
