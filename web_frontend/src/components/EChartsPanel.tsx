import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type ChartData = {
  categories: string[];
  series: Array<{
    name: string;
    values: number[];
  }>;
};

type Props = {
  data: ChartData;
};

export function EChartsPanel({ data }: Props) {
  const chartElement = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartElement.current) return;

    const chart = echarts.init(chartElement.current);
    chart.setOption({
      animationDuration: 500,
      color: ['#111111', '#d63b32', '#64748b', '#f59e0b'],
      grid: { left: 18, right: 18, top: 48, bottom: 24, containLabel: true },
      legend: { top: 8, right: 12, textStyle: { color: '#667085', fontSize: 11 } },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: data.categories,
        axisTick: { show: false },
        axisLine: { lineStyle: { color: '#d9dee6' } },
        axisLabel: { color: '#667085', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#edf1f7' } },
        axisLabel: { color: '#8f97a5', fontSize: 11 },
      },
      series: data.series.map((series, index) => ({
        name: series.name,
        type: index === 0 ? 'bar' : 'line',
        data: series.values,
        barMaxWidth: 36,
        smooth: true,
        symbolSize: 6,
      })),
    });

    const resizeObserver = new ResizeObserver(() => chart.resize());
    resizeObserver.observe(chartElement.current);
    return () => {
      resizeObserver.disconnect();
      chart.dispose();
    };
  }, [data]);

  return (
    <section className="echarts-card" aria-label="数据趋势图">
      <div className="echarts-card-title">数据趋势</div>
      <div ref={chartElement} className="echarts-panel" />
    </section>
  );
}
