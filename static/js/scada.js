const headers_post = {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': csrf_token
}

async function fetch_post(url, data) {
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
        sensors_list: [],
        rooms_list: [],
        vent: [],
        charts: [],
        listOfTypes: {'100': 'Температура', '200': 'CO2'},
        listOfMeters: {'100': 'C', '200': 'ppt'},
        listOfRooms: {'1': 'Гостиная', '2': 'Спальня'}
    },
    methods: {
        async ventManage(name, val) {
            this.vent[name] = val;
            let toSend = {};
            toSend[name] = val;
            await fetch_post('/scada_api/vent/', toSend)
        },
        async load_last() {
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
                data.sort((a, b) => (a.sensorId > b.sensorId) ? 1 : ((b.sensorId > a.sensorId) ? -1 : 0))
                let lastId = -1
                let tmp_arr = []
                for (let x = 0; x < data.length; x++) {
                    let tmp = {type: data[x].type, data: data[x].data, date: new Date(data[x].date.substring(0, 19))}
                    let now = new Date()
                    tmp.s_id = data[x].sensorId
                    tmp.s_type = this.listOfTypes[data[x].type]
                    tmp.meters = this.listOfMeters[data[x].type]
                    tmp.online = (now.getTime() - tmp.date.getTime() < 150000) ? 1 : 0
                    if (lastId !== data[x].sensorId) {
                        lastId = data[x].sensorId
                        this.rooms_list.push(this.listOfRooms[lastId] ? this.listOfRooms[lastId] : 'неизвестный датчик ' + lastId)
                        if (x !== 0) this.sensors_list.push(tmp_arr)
                        tmp_arr = [tmp]
                    } else
                        tmp_arr.push(tmp)
                }
                this.sensors_list.push(tmp_arr)
            });
        },
        async load_charts() {
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
                            dat.labels.push(tmp.getHours()-tmp.getTimezoneOffset()/60)
                            dat.data.push(data[x].data)

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
        await this.load_last();
        await this.load_charts()
        setInterval(function () {
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




