const headers_post = {                   // заголовок post запросов
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': csrf_token
}

async function fetch_post(url, data) {  // функция post запросов
    let response = await fetch(url, {
        method: 'post',
        headers: headers_post,
        body: JSON.stringify(data)
    });
    return (response);
}


new Vue({
    el: '#app',
    data: {
        sensors_list: [],        // список  всех датчиков
        rooms_list: [],          // список  помещений
        show_list: [false,false,false,false,false,false,false,false], // скрытие / открытие детальных графиков позже надо будет заполнять автоматически
        vent: [],  // данные венустанвки
        charts: [], // графики
        listOfTypes: {'100': 'Температура', '200': 'CO2', '300': 'Влажность'}, // Расшифровка данных датчиков, позже их надо будет читать из базы
        listOfMeters: {'100': 'C', '200': 'ppt', '300': '%'},
        listOfRooms: {'1953992342': 'Гостиная', '1953992341': 'Спальня'},
        listOfDivider: {'100': 10, '200': 1, '300': 10}   // делители (в БД все данные целочисленные

    },
    methods: {
        show_swich(num) {   //  переключатель отображения графиков
            this.show_list[num] = !this.show_list[num];
            this.load_last();   //   не рендерилася страница пришлось перечитывать данные. надо разбираться.....
            if  (this.show_list[num]) this.load_charts(num);
        },

        async ventManage(name, val) {      // переключение венташины
            this.vent[name] = val;
            let toSend = {};
            toSend[name] = val;
            await fetch_post('/scada_api/vent/', toSend)
        },
        async load_last() {  // чтение всех данных
            fetch('/scada_api/vent/').then((response) => {
                return response.json()
            }).then((data) => {
                this.vent = data;
            });
            await fetch('/scada_api/allsensors/').then((response) => {
                return response.json();
            }).then((data) => {
                this.sensors_list = []
                this.rooms_list = []

                data.sort((a, b) => (a.sensorId > b.sensorId) ? 1 : ((b.sensorId > a.sensorId) ? -1 : ((a.type > b.type) ? 1:((b.type > a.type) ? -1 :0))))
                let lastId = -1
                let tmp_arr = []
                for (let x = 0; x < data.length; x++) {
                    let tmp = {type: data[x].type, data: data[x].data, date: new Date(data[x].date.substring(0, 19))}
                    let now = new Date()
                    tmp.s_id = data[x].sensorId
                    tmp.data = tmp.data / (this.listOfDivider[data[x].type])
                    tmp.s_type = this.listOfTypes[data[x].type]
                    tmp.meters = this.listOfMeters[data[x].type]
                    tmp.online = (now.getTime() - tmp.date.getTime() < 150000) ? 1 : 0
                    if (lastId !== data[x].sensorId) {
                        lastId = data[x].sensorId
                        this.rooms_list.push(this.listOfRooms[lastId] ? this.listOfRooms[lastId] : 'неизвестный датчик ' + lastId)
                        //this.show_list.push(false)
                        if (x !== 0) this.sensors_list.push(tmp_arr)
                        tmp_arr = [tmp]
                    } else
                        tmp_arr.push(tmp)
                }
                this.sensors_list.push(tmp_arr)
            });
        },
        async load_charts(num) {
            tmp_arr = [];
            for (let i = 0; i < this.rooms_list.length; i++) {
                for (let j = 0; j < this.sensors_list[i].length; j++) {
                    await fetch('scada_api/sensor_last_days/' + this.sensors_list[i][j].s_id + '/' + this.sensors_list[i][j].type + '/1').then((response) => {
                        return response.json()
                    }).then((data) => {

                        let dat = {
                            id: 'chart_' + this.sensors_list[i][j].type + '_' + this.sensors_list[i][j].s_id,
                            u_type:  this.sensors_list[i][j].s_type,
                            labels: [],
                            data: [],
                        }

                        for (let x = 0; x < data.length; x++) {
                            tmp = new Date(data[x].date.substring(0, 19))
                            time=tmp.getHours()-tmp.getTimezoneOffset()/60
                            time -= (time < 24)? 0 : 24
                            dat.labels.push(time)
                            dat.data.push(data[x].data/(this.listOfDivider[this.sensors_list[i][j].type]))

                        }
                        tmp_arr.push(dat);
                    });
                }
            }
            for (let i = 0; i < tmp_arr.length; i++) {
                const ctx = document.getElementById(tmp_arr[i].id).getContext('2d');
                show_chart(ctx, tmp_arr[i])
            }
            return
        }
    },
    async created() {
        await this.load_last(); // загружаем данные
        await this.load_charts()  // рисуем графики
        setInterval(function () { // обновляем данные каждые 20 секунд
            this.load_last()
        }.bind(this), 20000);
    }
})

function show_chart(ctx, input_dat) {
    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: input_dat.labels,
            datasets: [{
                label: input_dat.u_type,
                data: input_dat.data,
                backgroundColor: "#AAFFAA",
                borderColor:  "#0000FF",
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
