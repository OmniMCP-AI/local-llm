import React from "react";
import { useLocale } from "./locale";
import { cardRatings } from "./catalog-position.mjs";
import { CoordinatePlot } from "./coordinate-plot";

export function CatalogCompare({ kind, chosen, modelStats, clear, remove }) {
  const { locale, t } = useLocale();
  const number = new Intl.NumberFormat(locale, { maximumFractionDigits: 2 });
  const compact = new Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 2 });
  const isModel = kind === "models";
  const metrics = isModel ? [
    ["parameters", t("Model parameters", "模型参数量"), "", compact],
    ["downloads", t("Hub downloads", "Hub 下载量"), "", compact],
  ] : [
    ["capacity", t("Nominal memory", "标称显存"), "GB", number],
    ["bandwidth", t("Rated memory bandwidth", "标称显存带宽"), "GB/s", number],
    ["power", t("Rated graphics power", "标称显卡功耗"), "W", number],
  ];
  const entries = chosen.map(row => ({
    id: row.id, name: isModel ? row.id : row.name,
    ...(isModel ? modelStats.get(row.id) : cardRatings(row)),
  }));

  const names = new Map(entries.map(({ id, name }) => [id, name]));
  const profileLabel = isModel ? t("Model", "模型") : t("GPU", "显卡");

  return <section className="catalog-comparison" id="catalog-comparison" aria-labelledby="catalog-comparison-title">
    <header>
      <div><h3 id="catalog-comparison-title">{isModel ? t("Compare models", "对比模型") : t("Compare GPUs", "对比显卡")}</h3>
        <p>{isModel
          ? t("Parameter counts and downloads use the dated Hub snapshot.", "参数量与下载量来自有日期的 Hub 快照。")
          : t("Manufacturer ratings for the selected identities.", "所选型号的厂商标称规格。")}</p></div>
      <button className="text-button" onClick={clear}>{t("Clear selection", "清除选择")}</button>
    </header>
    <ul className="catalog-comparison-picks" aria-label={t("Selected records", "已选记录")}>
      {entries.map(({ id, name }) => <li key={id}>
        <button className="catalog-tab" onClick={() => remove(id)}
          aria-label={t("Remove {name}", "移除 {name}", { name })}><bdi>{name}</bdi><span aria-hidden="true">×</span></button>
      </li>)}
    </ul>
    {entries.length < 2 ? <p>{t("Select one more row to compare.", "再选择一条记录进行对比。")}</p> :
      <div className="catalog-comparison-plots">{metrics.map(([metric, label, unit, formatter]) => {
        const points = entries.flatMap((row, index) => Number.isFinite(row[metric]) ? [{
          id: row.id, name: row.name, short: formatter.format(row[metric]), series: index,
          x: row.id, xText: row.name, y: row[metric],
          yText: `${number.format(row[metric])}${unit ? " " + unit : ""}`,
        }] : []);
        return <figure className="catalog-comparison-plot" aria-label={label} key={metric}>
          <CoordinatePlot title={label} kind="bar" points={points}
            xAxis={{ label: profileLabel, categorical: true, formatTick: id => names.get(id) }}
            yAxis={{ label, unit, formatTick: formatter.format }}
            labelsLabel={t("Show point labels", "显示数据点标签")}
            emptyText={label + " · " + t("Unavailable", "暂不可用")} />
          <ul aria-label={t("Exact comparison values", "比较明细数值")}>{entries.map(row => {
            const value = row[metric];
            return <li key={row.id}>
              <div><bdi>{row.name}</bdi><strong>
                {value == null ? t("Unavailable", "暂不可用") : number.format(value) + (unit ? " " + unit : "")}
              </strong></div>
            </li>;
          })}</ul>
        </figure>;
      })}</div>}
  </section>;
}
