const headers_post = {                   // заголовок запросов
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': csrf_token
}

const VALUES_PERIOD = 2000      // мс: опрос текущих значений
const LAYOUT_PERIOD = 60000     // мс: перечитка структуры виджетов (названия, типы, новые датчики)
const STALE_AFTER = 10          // с без ответа сервера — показываем «нет связи»
const COMMAND_TIMEOUT = 90      // с: сколько ждём, что устройство выполнит команду (вентиляция ~70 с)
const ERROR_SHOW = 20           // с: сколько показываем ошибку команды


class SessionExpired extends Error {}

// запрос к API; при истёкшей сессии — SessionExpired, при ошибке сервера — Error
async function api(url, method = 'get', data = undefined) {
    const response = await fetch(url, {
        method: method,
        headers: headers_post,
        body: data === undefined ? undefined : JSON.stringify(data),
    });
    // LoginRequiredMixin отвечает редиректом на страницу входа, DRF — 403
    if (response.redirected || response.status == 401 || response.status == 403) throw new SessionExpired()
    if (!response.ok) throw new Error(url + ': HTTP ' + response.status)
    return response
}

async function api_json(url, method, data) {
    return (await api(url, method, data)).json()
}

function two_digits(value) {
    return (value < 10 ? '0' : '') + value
}

// ключ ожидаемого подтверждения команды
function pending_key(item, subtitle) {
    return item.sensor.id + '|' + subtitle
}


// Виджеты: каждый шаблон из index.html (script#widget-tpl-<id>) становится компонентом widget-<id>.
// В шаблонах доступны item, mb_element(item, subtitle) и devManage(item, name, val).
const widget_mixin = {
    props: ['item'],
    computed: {
        by_type() {  // {subtitle: значение} — чтобы не искать по массиву при каждой отрисовке
            const result = {}
            for (const sensor of this.item.data) {
                if (sensor.type) result[sensor.type.subtitle] = sensor.data
            }
            return result
        },
    },
    methods: {
        mb_element(item, subtitle) {
            return this.by_type[subtitle] / 1
        },
        devManage(item, name, val) {
            return this.$root.devManage(item, name, val)
        },
    },
}

document.querySelectorAll('script[id^="widget-tpl-"]').forEach(el => {
    Vue.component('widget-' + el.id.slice('widget-tpl-'.length), {mixins: [widget_mixin], template: '#' + el.id})
})


// --- График ---------------------------------------------------------------------------------------

// категориальная палитра (светлый фон окна): цвет закреплён за позицией параметра в виджете
const SERIES_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
const CHART_TEXT = '#52514e'
const CHART_GRID = '#e6e5e0'

function time_label(ms) {
    const date = new Date(ms)
    return two_digits(date.getHours()) + ':' + two_digits(date.getMinutes())
}

// у параметров разные моменты замеров: под курсором берём ближайшую точку каждого параметра
Chart.Interaction.modes.nearest_each = function (chart, event) {
    const items = []
    chart.data.datasets.forEach((dataset, datasetIndex) => {
        const meta = chart.getDatasetMeta(datasetIndex)
        if (meta.hidden) return
        let best = null
        meta.data.forEach((element, index) => {
            const distance = Math.abs(element.x - event.x)
            if (best === null || distance < best.distance) best = {element, datasetIndex, index, distance}
        })
        if (best) items.push(best)
    })
    return items
}

// вертикальная линия под курсором
const crosshair_plugin = {
    id: 'crosshair',
    afterDraw(chart) {
        const active = chart.tooltip && chart.tooltip.getActiveElements()
        if (!active || !active.length) return
        const x = chart.tooltip.caretX
        const {top, bottom} = chart.chartArea
        const ctx = chart.ctx
        ctx.save()
        ctx.strokeStyle = CHART_TEXT
        ctx.globalAlpha = 0.4
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.moveTo(x, top)
        ctx.lineTo(x, bottom)
        ctx.stroke()
        ctx.restore()
    },
}


new Vue({
    el: '#app',
    data: {
        widgets_list: [],   // виджеты пользователя
        widgets_new: [],    // датчики, которые можно добавить
        charts: [],         // графики в окне подробностей
        show_details: false,
        detail: {
            title: "",
            sensors: [],
            empty: false,
        },
        detail_seq: 0,      // номер открытия окна: ответы для закрытого окна отбрасываем

        values: null,       // последний ответ /scada_api/values/
        values_loading: false,
        layout_loading: false,
        last_ok: 0,         // когда последний раз сервер ответил (Date.now())
        now: Date.now(),    // тикает раз в секунду — для признака «нет связи»

        pending: {},        // ожидаемые результаты команд: {датчик|subtitle: {target, until, widget}}
        cmd_errors: {},     // {id виджета: текст ошибки}

        editing: null,      // виджет, чьё название сейчас редактируют
        title_orig: "",

        drag_id: null,      // перетаскиваемый мышкой виджет
        drag_moved: false,  // порядок за время перетаскивания изменился
        drag_last: null,    // с каким виджетом только что поменялись местами
        drag_from_input: false,  // нажали в поле названия — это выделение текста, а не перенос
    },
    computed: {
        stale() {
            return this.now - this.last_ok > STALE_AFTER * 1000
        },
        last_ok_time() {
            const date = new Date(this.last_ok)
            return two_digits(date.getHours()) + ':' + two_digits(date.getMinutes()) + ':' + two_digits(date.getSeconds())
        },
    },
    methods: {
        // любая ошибка запроса: истёкшая сессия — на вход, остальное — в консоль (связь покажет stale)
        failed(error) {
            if (error instanceof SessionExpired) {
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname)
                return
            }
            console.error(error)
        },

        // --- Данные -------------------------------------------------------------------------------

        // структура виджетов с текущими значениями
        async load_layout() {
            if (this.layout_loading || this.drag_id !== null || this.editing) return
            this.layout_loading = true
            try {
                const [widgets_list, widgets_new] = await Promise.all([
                    api_json('/scada_api/mywidgets/', 'post'),
                    api_json('/scada_api/getsensor/', 'post'),
                ])
                // пока ждали ответ, могли начать перенос или правку названия — не затираем
                if (this.drag_id !== null || this.editing) return
                this.widgets_list = widgets_list
                this.widgets_new = widgets_new
                this.last_ok = Date.now()
                if (this.values) this.apply_values(this.values, false)
            } catch (error) {
                this.failed(error)
            } finally {
                this.layout_loading = false
            }
        },

        // только текущие значения — лёгкий частый запрос
        async load_values() {
            if (this.values_loading) return
            this.values_loading = true
            try {
                const values = await api_json('/scada_api/values/')
                this.values = values
                this.last_ok = this.now = Date.now()
                if (this.apply_values(values, true)) this.load_layout()  // появился новый тип данных
            } catch (error) {
                this.failed(error)
            } finally {
                this.values_loading = false
            }
        },

        // разложить значения по виджетам; true — если нужна перечитка структуры
        apply_values(values, fresh) {
            const server_now = Date.parse(values.now)
            let need_layout = false
            for (const item of this.widgets_list) {
                const fields = values.values[item.id] || {}
                let last = 0
                for (const sensor of item.data) {
                    if (!sensor.type) continue  // показание неизвестного типа — без subtitle
                    const value = fields[sensor.type.subtitle]
                    if (value && fresh) {
                        sensor.data = value[0]
                        sensor.date = value[1]
                    }
                }
                // у датчика появилось новое показание — структуру надо перечитать
                if (Object.keys(fields).length > item.data.length) need_layout = true
                for (const subtitle in fields) {
                    last = Math.max(last, Date.parse(fields[subtitle][1]))
                }
                this.apply_pending(item, fields)
                if (last) {
                    item.online = server_now - last < values.offline_after * 1000
                    const date = new Date(last)
                    item.date = server_now - last > 24 * 60 * 60 * 1000
                        ? date.getDate() + '/' + (date.getMonth() + 1) + '/' + date.getFullYear()
                        : two_digits(date.getHours()) + ':' + two_digits(date.getMinutes())
                }
            }
            return need_layout
        },

        // --- Команды устройствам ------------------------------------------------------------------

        data_entry(item, subtitle) {
            return item.data.find(obj => obj.type && obj.type.subtitle === subtitle)
        },

        // ждём, что показание дойдёт до значения команды; до тех пор показываем значение команды.
        // fields — показания с сервера: сравниваем с ними, а не с тем, что сейчас на экране
        apply_pending(item, fields) {
            for (const key in this.pending) {
                const pending = this.pending[key]
                if (pending.widget !== item.id) continue
                const sensor = this.data_entry(item, pending.subtitle)
                const actual = fields[pending.subtitle]
                if (!sensor || (actual && actual[0] == pending.target)) {
                    this.$delete(this.pending, key)
                } else if (Date.now() > pending.until) {
                    this.$delete(this.pending, key)
                    if (actual) sensor.data = actual[0]
                    this.show_error(item, 'устройство не выполнило команду')
                } else {
                    sensor.data = pending.target
                }
            }
        },

        cmd_pending(item) {
            return Object.values(this.pending).some(pending => pending.widget === item.id)
        },

        show_error(item, text) {
            this.$set(this.cmd_errors, item.id, text)
            setTimeout(() => {
                if (this.cmd_errors[item.id] === text) this.$delete(this.cmd_errors, item.id)
            }, ERROR_SHOW * 1000)
        },

        async devManage(item, name, val) {      // отправка данных в устройство
            // состояние реле C-1..C-3 приходит битовой маской в C-0
            let subtitle = name
            let target = val
            if (name[0] == 'C' && name.length > 2) {
                subtitle = 'C-0'
                const relays = this.data_entry(item, subtitle)
                target = relays ? relays.data ^ (1 << (name[2] / 1)) : null
            }
            const sensor = this.data_entry(item, subtitle)
            if (sensor && sensor.data == target) return  // уже в этом состоянии

            const key = pending_key(item, subtitle)
            const previous = sensor ? sensor.data : null
            this.$delete(this.cmd_errors, item.id)
            if (sensor && target !== null) {
                this.$set(this.pending, key, {
                    widget: item.id, subtitle: subtitle, target: target,
                    until: Date.now() + COMMAND_TIMEOUT * 1000,
                })
                sensor.data = target
            }
            try {
                await api('/scada_api/devmanage/', 'post', {'id': item.sensor.id, 'name': name, 'val': val})
            } catch (error) {
                this.$delete(this.pending, key)
                if (sensor) sensor.data = previous
                this.show_error(item, 'команда не отправлена')
                this.failed(error)
            }
        },

        // --- Список виджетов ----------------------------------------------------------------------

        async exit() {
            await fetch('/api/logout/')
            window.location.href = "/"
        },

        title_focus(item) {
            this.editing = item.id
            this.title_orig = item.title
        },

        title_cancel(item, event) {
            item.title = this.title_orig
            event.target.blur()
        },

        async title_edit(item) {
            this.editing = null
            if (item.title === this.title_orig) return
            try {
                await api('/scada_api/mywidgets/' + item.id + '/', 'post', {'title': item.title})
            } catch (error) {
                this.failed(error)
                this.load_layout()
            }
        },

        async delete_widget(id) {
            try {
                await api('/scada_api/mywidgets/' + id + '/', 'delete')
            } catch (error) {
                this.failed(error)
            }
            await this.load_layout()
        },

        async add_widget(id) {
            try {
                await api('/scada_api/mywidgets/' + id + '/', 'put')
            } catch (error) {
                this.failed(error)
            }
            await this.load_layout()
        },

        // перенос виджетов мышкой
        drag_start(id, event) {
            if (this.drag_from_input) {
                event.preventDefault()
                return
            }
            event.dataTransfer.effectAllowed = 'move'
            event.dataTransfer.setData('text/plain', id)  // без данных Firefox не начинает перенос
            this.drag_id = id
            this.drag_moved = false
            this.drag_last = null
        },

        drag_over(id) {
            if (this.drag_id === null) return
            // карточки разного размера: после обмена соседняя может остаться под курсором —
            // не меняемся с ней снова, пока курсор не уйдёт на другую карточку
            if (id == this.drag_id || id == this.drag_last) {
                if (id == this.drag_id) this.drag_last = null
                return
            }
            const from = this.widgets_list.findIndex(obj => obj.id == this.drag_id)
            const to = this.widgets_list.findIndex(obj => obj.id == id)
            if (from < 0 || to < 0) return
            const [moved] = this.widgets_list.splice(from, 1)
            this.widgets_list.splice(to, 0, moved)
            this.drag_moved = true
            this.drag_last = id
        },

        async drag_end() {
            if (this.drag_id === null) return  // drop и dragend приходят оба
            this.drag_id = null
            if (!this.drag_moved) return
            try {
                await api('/scada_api/mywidgets/', 'post', {'order': this.widgets_list.map(obj => obj.id)})
            } catch (error) {
                this.failed(error)
                this.load_layout()  // вернуть порядок с сервера
            }
        },

        // --- Графики ------------------------------------------------------------------------------

        async details(id, event) {
            if (['INPUT', 'A'].includes(event.target.tagName)) return  // двойной клик по названию — выделение слова
            const item = this.widgets_list.find(obj => obj.id == id)
            if (!item) return
            this.details_clear()
            const seq = ++this.detail_seq
            this.show_details = true
            this.detail.title = item.title
            this.detail.sensors = item.data.filter(sensor => sensor.type)
            try {
                const series = await Promise.all(this.detail.sensors.map(sensor =>
                    api_json('/scada_api/sensor_last_days/' + sensor.sensorId.id + '/' + sensor.type.id + '/1')))
                await this.$nextTick()
                if (seq !== this.detail_seq || !this.show_details) return  // окно уже закрыли
                this.detail.empty = series.every(rows => !rows.length)
                if (!this.detail.empty) this.show_chart(this.$refs.chart, this.detail.sensors, series)
            } catch (error) {
                this.failed(error)
            }
        },

        // один график: общая ось времени, у каждого параметра своя шкала слева/справа своего цвета
        show_chart(canvas, sensors, series) {
            const datasets = []
            const scales = {
                x: {
                    type: 'linear',
                    grid: {color: CHART_GRID},
                    ticks: {
                        color: CHART_TEXT, maxRotation: 0, autoSkip: true, maxTicksLimit: 12,
                        callback: value => time_label(value),
                    },
                },
            }
            sensors.forEach((sensor, index) => {
                const color = SERIES_COLORS[index % SERIES_COLORS.length]
                const axis = 'y' + index
                datasets.push({
                    label: sensor.type.title + (sensor.type.units ? ', ' + sensor.type.units : ''),
                    data: series[index].map(row => ({x: Date.parse(row.date), y: row.data / sensor.type.divider})),
                    yAxisID: axis,
                    borderColor: color,
                    backgroundColor: color,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    tension: 0,
                })
                scales[axis] = {
                    position: index % 2 ? 'right' : 'left',
                    grid: {display: index === 0, color: CHART_GRID},  // сетка только от первой шкалы
                    border: {color: color, width: 2},  // цвет оси связывает шкалу с её линией
                    ticks: {color: CHART_TEXT, maxTicksLimit: 6},
                    title: {display: !!sensor.type.units, text: sensor.type.units, color: CHART_TEXT},
                }
            })
            this.charts.push(new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {datasets: datasets},
                options: {
                    responsive: true,
                    animation: false,
                    parsing: false,
                    interaction: {mode: 'nearest_each', intersect: false},
                    plugins: {
                        legend: {
                            align: 'start',
                            position: 'top',
                            labels: {usePointStyle: true, pointStyle: 'line', color: CHART_TEXT},
                        },
                        tooltip: {
                            callbacks: {
                                title: items => items.length ? time_label(items[0].parsed.x) : '',
                                label: item => ' ' + item.dataset.label + ': ' + (Math.round(item.parsed.y * 100) / 100)
                                    + '  (' + time_label(item.parsed.x) + ')',
                            },
                        },
                    },
                    scales: scales,
                },
                plugins: [crosshair_plugin],
            }));
        },

        details_clear() {
            this.charts.forEach(chart => chart.destroy())   // иначе Chart.js держит canvas и данные в памяти
            this.charts = []
            this.show_details = false
            this.detail.title = ""
            this.detail.sensors = []
            this.detail.empty = false
        },
    },
    async created() {
        await this.load_layout()
        this.load_values()

        setInterval(() => {
            if (!document.hidden) this.now = Date.now()  // в фоне опроса нет — и «нет связи» не копим
            if (this.values) this.apply_values(this.values, false)  // истечение ожидания команд
        }, 1000);
        // пока вкладка видна: значения часто, структуру редко
        setInterval(() => {
            if (!document.hidden) this.load_values()
        }, VALUES_PERIOD);
        setInterval(() => {
            if (!document.hidden) this.load_layout()
        }, LAYOUT_PERIOD);
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) this.load_values()
        });
    }
})
