const headers_post = {                   // заголовок post запросов
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-CSRFToken': csrf_token
}


function show_chart(ctx, input_dat) {


    console.log("1111")

    const myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['1', '2', '3'],//input_dat.labels,
            datasets: [{
                label: '123',//input_dat.u_type,
                data: [1, 2, 3],// input_dat.data,
                backgroundColor: "#AAFFAA",
                borderColor: "#0000FF",
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
    data: {
        widgets_list: [],   //
        widgets_new: [],   //
        vent: [],  // данные венустанвки
        charts: [], // графики
        show_details: false,
        detail: {
            title: "",
            sensors: [],

        }


    },
    methods: {
        async show_charts(id, dat) {

            while (null == document.getElementById(id)) {
            }
            const ctx = document.getElementById(id).getContext('2d');
            let yArr = []
                let xArr = []
                for (let i = 0; i < dat.length; i++) {
                    yArr.push({x: new Date(dat[i]["date"]), y: dat[i]["data"]});
                    // yArr.push( dat[i]["data"]);
                    xArr.push(new Date(dat[i]["date"]).toLocaleDateString("ru-RU"))
                }

            const options = {
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
                            maxTicksLimit: 5
                        }
                    },

                }
            }
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: xArr,
                    datasets: [{
                        borderWidth: 1,
                            radius: 0,
                        // label: input_dat.u_type,
                        data: yArr,
                        backgroundColor: "#AAFFAA",
                        borderColor: "#0000FF",
                        borderWidth: 1
                    }]
                },
                options: options,
            });


            //console.log(data.data[i])
            //for (let i = 0; i < tmp_arr.length; i++) {
            //const ctx = document.getElementById(tmp_arr[i].id).getContext('2d');
            // show_chart(ctx, data)

            //console.log(document.getElementById(id))


        },


        charttset() {
            const ctx = document.getElementById('chart_test').getContext('2d');
            fetch('/scada_api/sensor_last_days/1953992342/125/10').then((response) => {
                return response.json()
            }).then((dat) => {
                let yArr = []
                let xArr = []
                for (let i = 0; i < dat.length; i++) {
                    yArr.push({x: new Date(dat[i]["date"]), y: dat[i]["data"]});
                    // yArr.push( dat[i]["data"]);
                    xArr.push(new Date(dat[i]["date"]).toLocaleDateString("ru-RU"))
                }
                options = {
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
                                maxTicksLimit: 5
                            }
                        },

                    }
                }


                const myChart = new Chart(ctx, {
                    type: 'line',

                    data: {

                        labels: xArr,

                        datasets: [{
                            label: "Данные",
                            borderColor: '#FF0000',
                            borderWidth: 1,
                            radius: 0,
                            data: yArr,

                        }],
                    },
                    options: options,


                })

            })


        },

        details(id) {

            let data = search_by_id(id, this.widgets_list)
            this.detail.title = data.title
            for (let i = 0; i < data.data.length; i++) {
                this.detail.sensors.push(data.data[i])

                var chartData = {
                    u_type: data.data[i].type.title + " (" + data.data[i].type.units + ")",
                    labels: [],
                    data: [],

                };
                fetch('scada_api/sensor_last_days/' + data.data[i].sensorId.id + '/' + data.data[i].type.id + '/1').then((response) => {
                    return response.json()
                }).then((dat) => {
                    /*for (let j = 0; j < dat.length; j++) {
                        chartData.data.push(dat[j].data / data.data[i].type.divider)
                        let tmp = new Date(dat[j].date.substring(0, 19))
                         chartData.labels.push(tmp.getHours())}
                        */
                    setTimeout(() => {
                        this.show_charts(data.data[i].type.id, dat)
                    }, 50)


                })


            }


            this.show_details = true


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


        async ventManage(name, val) {      // переключение венташины
            this.vent[name] = val;
            let toSend = {};
            toSend[name] = val;
            await fetch_post('/scada_api/vent/', toSend)
        },

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
            }).then((result) => this.widgets_list = result)
        },

        // Получение списка виджетов
        async load_widget_new() {
            await fetch_post('/scada_api/getsensor/').then((result) => {
                return result.json()
            }).then((result) => this.widgets_new = result)
        },

        // Получение списка виджетов

        async load_last() {  // чтение всех данных
            fetch('/scada_api/vent/').then((response) => {
                return response.json()
            }).then((data) => {
                this.vent = data;
            });
            await this.load_widget_list(); // получаем перечень виджетов
            await this.load_widget_new();

        },
    },
    async created() {
        await this.load_last(); // загружаем данные

        setInterval(function () { // обновляем данные каждые 20 секунд
            this.load_last()
        }.bind(this), 20000);

        this.charttset();

    }
})


/*
*
*         async load_charts() {
             tmp_arr = [];
             for (let i = 0; i < this.rooms_list.length; i++) {
                 for (let j = 0; j < this.sensors_list[i].length; j++) {
                     await fetch('scada_api/sensor_last_days/' + this.sensors_list[i][j].s_id + '/' + this.sensors_list[i][j].type + '/1').then((response) => {
                         return response.json()
                     }).then((data) => {

             fetch('/scada_api/vent/').then((response) => {
                 return response.json()}).then((data) => {
                 this.vent = data;
             });

                         let dat = {
                             id: 'chart_' + this.sensors_list[i][j].type + '_' + this.sensors_list[i][j].s_id,
                             u_type:  this.sensors_list[i][j].s_type,
                             labels: [],
                             data: [],
                         }




                         for (let x = 0; x < data.length; x++) {
                             tmp = new Date(data[x].date.substring(0, 19))
                             dat.labels.push(tmp.getHours())
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
*
* */