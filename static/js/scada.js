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
        pos : 'position: fixed',
        widgets_list: [],   //
        widgets_new: [],   //
        vent: [],  // данные венустанвки
        charts: [], // графики
        show_details: false,
        block_list: [],
        detail: {
            title: "",
            sensors: [],

        }


    },
    methods: {
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


        async devManage(item, name, val) {      // отправка данныйх в устройство
            let toSend = {
                'id': item.sensor.id,
                'name': name,
                'val': val
            };
            await fetch_post('/scada_api/devmanage/', toSend)
            let index = item.data.findIndex(obj => obj.type.subtitle === name)
            item.data[index].data = val;
            index = this.widgets_list.findIndex(obj => obj.id === item.id)
            this.widgets_list[index] = item;
            this.block_list = this.block_list.filter(element => {
                return element.item.id !== item.id;
            });
            this.block_list.push({'time': Math.floor(Date.now() / 1000) + 3, 'item': item})
            await this.load_last(); // загружаем данные

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
                * */

                // проверить на block
            })
        },

        // Получение списка виджетов
        async load_widget_new() {
            await fetch_post('/scada_api/getsensor/').then((result) => {
                return result.json()
            }).then((result) => this.widgets_new = result)
        },

        mb_element(item, j) {
            return (item.data.find(obj => obj.type.subtitle === j).data) / 1
        },


        // Получение списка виджетов

        async load_last() {  // чтение всех данных
            /* fetch('/scada_api/vent/').then((response) => {
                 return response.json()
             }).then((data) => {
                 this.vent = data;
             });*/
            await this.load_widget_list(); // получаем перечень виджетов
            await this.load_widget_new();

        },
    },
    async created() {
        await this.load_last(); // загружаем данные


        setInterval(function () { // обновляем данные каждые 20 секунд
            this.load_last()
        }.bind(this), 5000);


    }
})

