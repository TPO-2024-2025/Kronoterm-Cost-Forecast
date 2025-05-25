import { html, css, LitElement } from "lit";
import ApexCharts from "apexcharts";

import flatpickr from "flatpickr/dist/flatpickr.min.js";
import flatpickr_css_dark from "flatpickr/dist/themes/dark.css";
import flatpickr_css_light from "flatpickr/dist/themes/light.css";

// import flatpickr from "flatpickr";
// import { HomeAssistant } from "custom-card-helpers";
// import { PropertyValues } from "@lit/reactive-element";

class CustomApexCard extends LitElement {
  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  constructor() {
    super();
    this.chart = null;
    this.chartData = [];
    this.series1 = [];
    this.series2 = [];
    this.picker_s1 = undefined;
    this.picker_s2 = undefined;
    this.darkMode = true;
    this.query = null;
    this.options = null;

    this.darkPallete = {
      chart_background: "#181818",
      tooltip_background: "rgba(30, 30, 30, 0.95)",
      range1_color: "#1E80EF",
      range2_color: "#DF3500",
      delta_color: "white",
      label_color: "white",
    };

    this.lightPallete = {
      chart_background: "#CCCCCC",
      tooltip_background: "rgba(224, 224, 224, 0.95)",
      range1_color: "#1E90FF",
      range2_color: "#FF4500",
      delta_color: "black",
      label_color: "black",
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Entity is required");
    }
    this.config = config;
  }

  /**
   *
   * @param {Date} from
   * @param {Date} to
   *
   * @returns {Promise<Array<{x: number, y: number, date: Date}>>}
   */
  async fetchHistory(from, to) {
    try {
      const history = await this.hass.connection.sendMessagePromise({
        type: "history/history_during_period",
        start_time: from.toISOString(),
        end_time: to.toISOString(),
        entity_ids: [this.config.entity],
        minimal_response: true,
      });

      let series = history[this.config.entity]
        .map((e, index) => {
          return {
            x: index,
            y: parseFloat(e.s),
            date: new Date(e.lu * 1000),
          };
        })
        .filter((v) => !isNaN(v.y));

      const step = 1;
      return this.transformSeriesWithTimeSpacing(series, "minute", step);
    } catch (e) {
      console.warn(e);
      return [];
    }
  }

  /**
   *
   * @param {Array<{x: number, y: number, date: Date}>} data
   * @param {string} unit
   * @param {number} step
   * @returns
   */
  transformSeriesWithTimeSpacing(data, unit = "minutes", step = 0.5) {
    if (data.length === 0) return [];

    const getTime = (d) => new Date(d.date).getTime();
    const baseTime = getTime(data[0]);

    return data.map((point) => {
      const elapsedMs = getTime(point) - baseTime;

      let scaledX;
      switch (unit) {
        case "seconds":
          scaledX = elapsedMs / 1000;
          break;
        case "minutes":
          scaledX = elapsedMs / (1000 * 60);
          break;
        case "hours":
          scaledX = elapsedMs / (1000 * 60 * 60);
          break;
        default:
          scaledX = elapsedMs;
      }

      return {
        ...point,
        x: scaledX / step, // adjust for your unit step size (0.5 for 30s intervals)
      };
    });
  }

  connectedCallback() {
    super.connectedCallback();
    this.query = window.matchMedia("(prefers-color-scheme: dark)");
    this.query.addEventListener("change", (e) => {
      this.darkMode = e.matches;
      this.updateChartData(e.matches);
    });
  }

  async firstUpdated(changedProperties) {
    if (!this.hass) {
      this.hass = changedProperties.get("hass");
    }

    let now = new Date();
    let today = new Date(now.toDateString());
    let yesterday = new Date(now.toDateString());
    let tomorow = new Date(now.toDateString());
    yesterday.setDate(now.getDate() - 1);
    tomorow.setDate(now.getDate() + 1);

    if (!this.picker_s1) {
      this.picker_s1 = this.createPickerIfExist(
        "series1",
        [yesterday, today],
        (dates) => {
          if (!dates || dates.length < 2) {
            return;
          }
          this.fetchHistory(dates[0], dates[1]).then((vals) => {
            this.series1 = vals;
            if (vals && vals.length > 0) {
              this.series1 = vals.map((v) => {
                return { x: v.x, y: v.y - vals[0].y, date: v.date };
              });
            }
            this.updateSeries();
          });
        }
      );
    }
    if (!this.picker_s2) {
      this.picker_s2 = this.createPickerIfExist(
        "series2",
        [today, tomorow],
        (dates) => {
          if (!dates || dates.length < 2) {
            return;
          }
          this.fetchHistory(dates[0], dates[1]).then((vals) => {
            this.series2 = vals;
            if (vals && vals.length > 0) {
              this.series2 = vals.map((v) => {
                return { x: v.x, y: v.y - vals[0].y, date: v.date };
              });
            }
            this.updateSeries();
          });
        }
      );
    }

    this.picker_s1.close();
    this.picker_s2.close();
    this.renderChart();
  }

  updateSeries() {
    this.chart.updateSeries([
      {
        name: "Range 1",
        data: this.series1,
      },
      {
        name: "Range 2",
        data: this.series2,
      },
    ]);
  }

  /**
   * @param {PropertyValues} changedProps
   */
  updated(changedProps) {
    /**
     * @type {HomeAssistant}
     */
    const hass = changedProps.get("hass");
    if (!hass) return;
    this.darkMode = hass.themes.darkMode;
    // console.log("MODE: ", this.darkMode);
    this.updateChartData();
  }

  /**
   *
   * @param {string} elementId
   * @param {Date[]} default_date
   * @param {flatpickr.Options.Hook} onClose
   * @returns
   */
  createPickerIfExist(elementId, default_date, onClose) {
    const el = this.shadowRoot.getElementById(elementId);
    if (el === undefined || el === null) {
      console.log("No element");
      return undefined;
    }

    const style = document.createElement("style");
    style.textContent = `
    @media (prefers-color-scheme: dark) {${flatpickr_css_dark}}
    @media (prefers-color-scheme: light) {${flatpickr_css_light}}`;
    this.renderRoot.appendChild(style);

    return flatpickr(el, {
      animate: true,
      closeOnSelect: true,
      enableTime: true,
      mode: "range",
      appendTo: this.renderRoot,
      time_24hr: true,
      dateFormat: "Y-m-d H:00",
      minuteIncrement: 60,
      onClose,
      autoFillDefaultTime: true,
      defaultDate: default_date,
      positionElement: el,
      static: true,
    });
  }

  updateChartData(dm) {
    if (!this.chart) return;

    if (dm) {
      this.darkMode = dm;
    }

    // console.log("Dark Mode:", this.darkMode);
    const pallete = this.darkMode ? this.darkPallete : this.lightPallete;
    this.options.chart.background.color = pallete.chart_background;
    this.options.title.style.color = pallete.label_color;
    if (this.options.xaxis.labels) {
      this.options.xaxis.labels.style.colors = pallete.label_color;
    } else {
      this.options.xaxis = {
        ...this.options.xaxis,
        labels: {
          show: false,
          style: {
            colors: pallete.label_color,
          },
        },
      };
    }

    if (this.options.yaxis.labels) {
      this.options.yaxis.labels.style.colors = pallete.label_color;
    } else {
      this.options.yaxis = {
        ...this.options.yaxis,
        labels: {
          style: {
            colors: pallete.label_color,
          },
          formatter: (v, w) => {
            if (!v) return v;
            const unit = this.options.unit;
            return `${v.toFixed(2)} ${unit}`;
          },
        },
      };
    }

    this.chart.updateOptions(this.options);
    this.updateSeries();
  }

  /**
   *
   * @param {Date} date
   * @returns {string}
   */
  dateToString(date) {
    return `${date.getFullYear().toString().padStart(4, "0")}-${date
      .getMonth()
      .toString()
      .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")} ${date
      .getHours()
      .toString()
      .padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}:${date
      .getSeconds()
      .toString()
      .padStart(2, "0")}`;
  }

  renderChart() {
    const entity = this.hass.states[this.config.entity];
    const unit = entity.attributes.unit_of_measurement;

    const pallete = this.darkMode ? this.darkPallete : this.lightPallete;

    this.options = {
      chart: {
        type: "line",
        height: 350,
        width: "100%",
        animations: {
          enabeled: false,
          dynamicAnimation: {
            enabled: false,
          },
        },
        background: {
          color: pallete.chart_background,
        },
      },
      title: {
        text: this.config.title,
        style: {
          color: pallete.label_color,
        },
      },
      unit: unit,
      tooltip: {
        theme: false,
        shared: true,
        intersect: false,
        x: {
          show: false,
        },
        custom: ({ series, seriesIndex, dataPointIndex, w }) => {
          const value1 = series[0][dataPointIndex];
          const value2 = series[1][dataPointIndex];

          const unit = w.config.unit || "units"; // fallback if no unit
          const pallete = this.darkMode ? this.darkPallete : this.lightPallete;

          let ret = `<div style="padding: 8px; font-family: sans-serif; background-color: ${pallete.tooltip_background};">`;

          if (value1) {
            ret = `${ret}
            <div style="color: ${
              pallete.range1_color
            };"><strong>Range 1: ${value1.toFixed(2)} ${unit}</strong></div>
            `;
          }

          if (value2) {
            ret = `${ret}
            <div style="color: ${
              pallete.range2_color
            };"><strong>Range 2: ${value2.toFixed(2)} ${unit}</strong></div>
            `;
          }

          if (value1 && value2) {
            const delta = (value2 - value1).toFixed(2);
            ret = `${ret}
            <div style="margin-top: 4px; color: ${pallete.delta_color};">
              <strong>Δ: ${(delta > 0 ? "+" : "") + delta} ${unit}</strong>
            </div>`;
          }

          ret = `${ret}</div>`;

          return ret;
        },
      },
      // colors: ["blue"],
      series: [
        {
          name: "Range 1",
          data: this.series1,
        },
        {
          name: "Range 2",
          data: this.series2,
        },
      ],
      xaxis: {
        type: "numeric",
        min: 0,
        tooltip: {
          enabled: false,
        },
        labels: {
          show: false,
          style: {
            colors: pallete.label_color,
          },
        },
      },
      yaxis: {
        unit: entity.attributes.unit_of_measurement,
        labels: {
          style: {
            colors: pallete.label_color,
          },
          formatter: (v, w) => {
            if (!v) return v;
            return `${v.toFixed(2)} ${unit}`;
          },
        },
      },
    };

    const chartDiv = this.renderRoot.querySelector("#chart");
    this.chart = new ApexCharts(chartDiv, this.options);
    this.chart.render();
    this.chart.resetSeries();
  }

  render() {
    return html`
      <table class="date-range-picker" style="width: 100%;">
        <tr>
          <th>Range 1</th>
          <th>Range 2</th>
        </tr>
        <tr>
          <td><input type="text" id="series1" /></td>
          <td><input type="text" id="series2" /></td>
        </tr>
      </table>
      <div id="chart"></div>
    `;
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }
      #chart {
        width: 100%;
      }
      .apexcharts-toolbar {
        z-index: 0;
      }
      .flatpickr-time .flatpickr-time-separator + .numInputWrapper {
        display: none !important;
      }
      .flatpickr-time .flatpickr-minute,
      .flatpickr-time .flatpickr-time-separator {
        display: none !important;
      }
      .flatpickr-calendar {
      }
      .date-range-picker td {
        padding: 5px;
      }
      .date-range-picker td {
        text-align: center;
        vetrical-align: center;
      }
      #series1,
      #series2 {
        width: 100%;
      }
    `;
  }
}

customElements.define("custom-apex-card", CustomApexCard);
