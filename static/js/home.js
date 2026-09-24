const headers_post = {                   // заголовок post запросов
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': csrf_token
}


const vent_id = 950559233;



Vue.filter('twoDigits', function (value) {
  if (value < 10) {
    return '0' + value;
  }
  return value.toString();
});




async function fetch_post(url, data) {  // функция post запросов
    let response = await fetch(url, {
        method: 'post',
        headers: headers_post,
        body: JSON.stringify(data)
    });
    return (response);
}

async function fetch_delete(url) {  // функция post запросов
    let response = await fetch(url, {
        method: 'delete',
        headers: headers_post,

    });
    return (response);
}

async function fetch_put(url) {  // функция post запросов
    let response = await fetch(url, {
        method: 'put',
        headers: headers_post,

    });
    return (response);
}

function search_by_id(id, data) {
    for (i = 0; i < data.length; i++) {
        if (data[i].id == id) return data[i]
    }
    return null

}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        vent: [],  // данные венустанвки
        minutes: 0,
        hours: 0,
        out_temp: 0,
        temp: 0,
        CO: 0,
        humidity: 0,
        vent_speed:0,
        vent_heat:0,
        load_delay: 0,

    },
    methods: {

        clock(){
          const now = new Date();
          this.hours = now.getHours();
          this.minutes = now.getMinutes();

        },

        async show_charts(id, dat, type) {
            while (null == document.getElementById(id)) {
                console.log(id);
            }
            const ctx = document.getElementById(id).getContext('2d');
            let yArr = []
            let xArr = []
            for (let i = 0; i < dat.length; i++) {
                yArr.push({x: new Date(dat[i]["date"]), y: dat[i]["data"] / type.divider});
                // yArr.push( dat[i]["data"]);
                let h = "" + new Date(dat[i]["date"]).getHours();
                let m = "" + new Date(dat[i]["date"]).getMinutes();
                if (h.length == 1) h = "0" + h;
                if (m.length == 1) m = "0" + m;
                xArr.push(h + ':' + m)
                //xArr.push(new Date(dat[i]["date"]))
            }

            const options = {
                spanGaps: 1000 * 60,
                responsive: true,
                plugins: {
                    legend: {
                        align: 'start',
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            color: '#007bff',

                        },
                    }
                },
                animation: false,
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                scales: {
                    x: {


                        display: true,
                        title: {
                            display: true
                        },


                        ticks: {
                            maxRotation: 0,
                            minRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 30,

                        }
                    },
                    y: {
                        beginAtZero: true,
                        display: true,
                        title: {
                            display: true,
                            text: type.units
                        }
                    }
                }
            }

            new Chart(ctx, {
                type: 'line',
                fill: false,
                data: {
                    labels: xArr,
                    datasets: [{
                        borderWidth: 1,
                        radius: 0,
                        label: type.title,
                        data: yArr,
                        borderColor: "#007bff",
                        backgroundColor: "#007bff",
                        //backgroundColor: "#AAFFAA",
                        //borderColor: "#0000FF",
                        pointStyle: false,
                        borderWidth: 1
                    }]
                },
                options: options,
            });
        },


        details(id) {

            console.log(id)
            this.show_details = true
            let data = search_by_id(id, this.widgets_list)
            this.detail.title = data.title
            for (let i = 0; i < data.data.length; i++) {
                this.detail.sensors.push(data.data[i])
                fetch('scada_api/sensor_last_days/' + data.data[i].sensorId.id + '/' + data.data[i].type.id + '/1').then((response) => {
                    return response.json()
                }).then((dat) => {
                    setTimeout(() => {
                        this.show_charts(data.data[i].type.id, dat, data.data[i].type)
                    }, 50)
                })
            }

/*
            for (let i = 0; i < data.data.length; i++) {
                this.detail.sensors.push(data.data[i])


                fetch('scada_api/sensor_last_days/' + data.data[i].sensorId.id + '/' + data.data[i].type.id + '/1').then((response) => {
                    return response.json()
                }).then((dat) => {
                    setTimeout(() => {
                        console.log("1:",data.data[i].type.id)
                        this.detail.sensors[this.detail.sensors.length - 1].type.id += "Y"
                        console.log("2:",data.data[i].type.id)
                         //this.show_charts(data.data[i].type.id , dat, data.data[i].type)
                    }, 50)
                })

            } */





        },

        details_clear() {
            this.show_details = false
            this.detail.title = ""
            this.detail.sensors = []

        },


        async exit() {
            await fetch('/api/logout/')
            window.location.href = "/"
        },

        title_edit(id) {
            fetch_post('/scada_api/mywidgets/' + id + '/', {'title': search_by_id(id, this.widgets_list).title})

        },










        async devManage(name, val) {      // отправка данныйх в устройство
            let toSend = {
                'id': vent_id,
                'name': name,
                'val': val
            };
            await fetch_post('/scada_api/devmanage/', toSend)
            this.load_delay=3;

        },
/*
        async delete_widget(id) {
            await fetch_delete('/scada_api/mywidgets/' + id + '/')
            this.load_last()

        },

        async add_widget(id) {
            await fetch_put('/scada_api/mywidgets/' + id + '/')
            this.load_last()

        },

        async move_widget(id, step) {
            await fetch_post('/scada_api/mywidgets/' + id + '/', {'step': step})
            this.load_last()
        },

        // Получение списка виджетов
        async load_widget_list() {
            await fetch_post('/scada_api/mywidgets/').then((result) => {

                return result.json()
            }).then((result) => {

                let widgets_list = result;
                this.block_list = this.block_list.filter(element => {
                    return element.time > (Math.floor(Date.now() / 1000));
                });
                for (let i = 0; i < widgets_list.length; i++) {
                    let blocked = this.block_list.filter(element => {
                        return element.item.id == widgets_list[i].id;
                    });
                    if (blocked.length) {
                        widgets_list[i] = blocked[0]['item']
                        blocked = []

                    }

                    //console.log(widgets_list[i])
                }
                this.widgets_list = widgets_list;

                /*
                *
                *this.block_list=this.block_list.filter(element => {return element.item.id !== item.id;});
            this.block_list.push({'time':Math.floor(Date.now() / 1000)+20, 'item':item})
            console.log(this.block_list);
            console.log(this.block_list.map(elem => elem.item.id));


                // проверить на block
            })
        },*/

        /*/ Получение списка виджетов
        async load_widget_new() {
            await fetch_post('/scada_api/getsensor/').then((result) => {
                return result.json()
            }).then((result) => this.widgets_new = result)
        },

        mb_element(item, j) {
            return (item.data.find(obj => obj.type.subtitle === j).data) / 1
        },


        // Получение списка виджетов
*/
        async dataLoad() {  // чтение всех данных
            if (this.load_delay) {
                this.load_delay--;
                return
            }

            await fetch_post('/scada_api/sensor_data/1953992321/T/').then((result) => {
                return result.json() }).then((result) => { this.out_temp = result.data/result.type.divider; });
            await fetch_post('/scada_api/sensor_data/1953992342/T/').then((result) => {
                return result.json() }).then((result) => { this.temp = result.data/result.type.divider; });
             await fetch_post('/scada_api/sensor_data/1953992342/H/').then((result) => {
                return result.json() }).then((result) => { this.humidity = result.data/result.type.divider; });
             await fetch_post('/scada_api/sensor_data/1953992342/CO/').then((result) => {
                return result.json() }).then((result) => { this.CO = result.data/result.type.divider; });
             await fetch_post('/scada_api/sensor_data/'+vent_id+'/R-100/').then((result) => {

                return result.json() }).then((result) => {this.vent_speed = result.data});
             await fetch_post('/scada_api/sensor_data/'+vent_id+'/R-206/').then((result) => {
                return result.json() }).then((result) => { this.vent_heat = result.data/1; });





        },
    },
    async created() {

        setInterval(function () {
            this.clock();
        }.bind(this), 500);


        await this.dataLoad(); // загружаем данные
        setInterval(function () { // обновляем данные каждые 20 секунд
            this.dataLoad()
        }.bind(this), 5000);


    }
})

