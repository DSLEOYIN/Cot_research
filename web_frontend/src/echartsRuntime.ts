import * as echarts from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

let registered = false;

function registerEChartsModules() {
  if (registered) return;
  echarts.use([
    BarChart,
    LineChart,
    GridComponent,
    LegendComponent,
    TooltipComponent,
    CanvasRenderer,
  ]);
  registered = true;
}

export function initEChart(element: HTMLDivElement) {
  registerEChartsModules();
  return echarts.init(element);
}
