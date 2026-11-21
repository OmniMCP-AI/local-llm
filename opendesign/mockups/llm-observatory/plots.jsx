import React from "react";
import { CoordinatePlot } from "./coordinate-plot";
import { quoteCurrency, useLocale } from "./locale";

function usePlotLabels(workload, region) {
  const { t, formatMoney, displayCurrency, locale } = useLocale();
  const currency = quoteCurrency(region);
  const yAxis = {
    label: workload.lowerBetter ? t("Time", "用时") : t("Decode speed", "解码速度"),
    unit: t(workload.unit, workload.unit),
    formatTick: new Intl.NumberFormat(locale, { maximumFractionDigits: 4 }).format,
  };
  const exactMoney = (value) => formatMoney(value, currency, { currencyDisplay: "code", maximumFractionDigits: 4 });
  const shortMoney = (value) => formatMoney(value, currency, { notation: "compact", maximumFractionDigits: 1 });
  const xAxis = { label: t("Build price", "整机价格"), unit: displayCurrency(currency), formatTick: shortMoney, formatValue: exactMoney };
  return { t, yAxis, xAxis, shortMoney, exactMoney, labelsLabel: t("Show point labels", "显示数据点标签") };
}

const targetIsKnown = target => Number.isFinite(target) && target >= 0;
const pointDetail = (point, t) => [point.detail, !point.eligible && t("Context only", "仅供参考")].filter(Boolean).join(" · ");

function efficientSetups(points, lowerBetter) {
  return points.filter(point => point.eligible && !points.some(other => {
    if (!other.eligible || other.id === point.id || other.price > point.price) return false;
    const atLeastAsFast = lowerBetter ? other.value <= point.value : other.value >= point.value;
    return atLeastAsFast && (other.value !== point.value || other.price < point.price);
  })).sort((a, b) => a.price - b.price).map(point => point.id);
}

export function ScatterPlot({ points, workload, region, budget, target, selectedId, onSelect, showFrontier }) {
  const { t, xAxis, yAxis, shortMoney, labelsLabel } = usePlotLabels(workload, region);
  const validBudget = targetIsKnown(budget);
  const validTarget = targetIsKnown(target);
  const guides = [];
  if (validBudget) guides.push({ axis: "x", value: budget, label: t("Budget", "预算") + " " + shortMoney(budget) });
  if (validTarget) guides.push({ axis: "y", value: target, label: t("Target", "目标") + " " + yAxis.formatTick(target) + " " + yAxis.unit });
  return <CoordinatePlot title={t("Build price and workload performance", "整机价格与工作负载性能")}
    xAxis={xAxis} yAxis={{ ...yAxis, reverse: workload.lowerBetter }}
    points={points.map(point => ({
      ...point, x: point.price, y: point.value, detail: pointDetail(point, t), context: !point.eligible,
    }))}
    guides={guides} targetArea={validBudget && validTarget ? { x: budget, y: target } : undefined}
    frontier={showFrontier ? efficientSetups(points, workload.lowerBetter) : []}
    selectedId={selectedId} onSelect={onSelect} labelsLabel={labelsLabel}
    emptyText={t("No setups with price and performance.", "暂无同时具备价格和性能的配置。")} />;
}

export function RankingPlot({ points, workload, region, target, selectedId, onSelect }) {
  const { t, yAxis, exactMoney, labelsLabel } = usePlotLabels(workload, region);
  const ranked = points.filter(({ eligible, value }) => eligible && Number.isFinite(value) && value >= 0)
    .sort((a, b) => workload.lowerBetter ? a.value - b.value : b.value - a.value);
  const names = new Map(ranked.map(({ id, short }) => [id, short]));
  const guides = targetIsKnown(target)
    ? [{ axis: "y", value: target, label: t("Target", "目标") + " " + yAxis.formatTick(target) + " " + yAxis.unit }]
    : [];
  return <CoordinatePlot title={workload.lowerBetter ? t("Ranked setups, fastest time first", "配置排名，用时从短到长") : t("Ranked setups, highest decode speed first", "配置排名，解码速度从高到低")}
    kind="bar" xAxis={{ label: t("Setup", "配置"), categorical: true, formatTick: id => names.get(id) }} yAxis={yAxis}
    points={ranked.map(point => ({
      ...point, x: point.id, xText: point.name, y: point.value,
      short: yAxis.formatTick(point.value) + " " + yAxis.unit,
      detail: [point.detail, Number.isFinite(point.price) && exactMoney(point.price)].filter(Boolean).join(" · "),
    }))}
    selectedId={selectedId} onSelect={onSelect} guides={guides} labelsLabel={labelsLabel}
    emptyText={t("No comparable measurements for this workload and price cohort.", "此工作负载和报价组暂无可比测试。")} />;
}

const historyDates = ["Aug 14", "Aug 28", "Sep 11", "Sep 25", "Oct 9", "Oct 23", "Nov 6", "Nov 20"];

export function PricePlot({ values = [], formatValue }) {
  const { t, displayCurrency, formatMoney } = useLocale();
  const label = index => historyDates[index] ?? t("Quote", "报价") + " " + (index + 1);
  return <CoordinatePlot title={t("Illustrative build quotes by observation date", "按观察日期查看示例整机报价")}
    kind="line" xAxis={{ label: t("Observation date", "观察日期"), categorical: true }}
    yAxis={{
      label: t("Build price", "整机价格"), unit: displayCurrency("USD"), zero: false,
      formatTick: quote => formatMoney(quote, "USD", { notation: "compact", maximumFractionDigits: 1 }),
      formatValue: formatValue ?? (quote => formatMoney(quote, "USD", { currencyDisplay: "code" })),
    }}
    points={values.map((y, index) => ({ id: String(index), name: label(index), x: label(index), y }))}
    labelsLabel={t("Show point labels", "显示数据点标签")}
    emptyText={t("No price history is available for this configuration.", "此配置暂无历史报价。")} />;
}
