import { useEffect, useRef } from 'react';
import type { ECharts } from 'echarts/core';

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
  const chartRef = useRef<ECharts | null>(null);
  const dataKey = JSON.stringify(data);

  useEffect(() => {
    if (!chartElement.current) return undefined;

    let disposed = false;
    let resizeObserver: ResizeObserver | null = null;
    let mountedElement: HTMLDivElement | null = chartElement.current;

    void import('../echartsRuntime').then(({ initEChart }) => {
      if (disposed || !mountedElement) return;
      const chart = initEChart(mountedElement);
      chartRef.current = chart;
      resizeObserver = new ResizeObserver(() => chart.resize());
      resizeObserver.observe(mountedElement);
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
    });

    return () => {
      disposed = true;
      resizeObserver?.disconnect();
      const chart = chartRef.current;
      if (chart) chart.dispose();
      chartRef.current = null;
      mountedElement = null;
    };
  }, []);

  useEffect(() => {
    chartRef.current?.setOption({
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
  }, [dataKey]);

  return (
    <section className="echarts-card" aria-label="数据趋势图">
      <div className="echarts-card-title">数据趋势</div>
      <div ref={chartElement} className="echarts-panel" />
    </section>
  );
}
