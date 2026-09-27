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

// последнее значение датчика
async function sensor_data(sensor_id, type) {
    const result = await fetch_post('/scada_api/sensor_data/' + sensor_id + '/' + type + '/')
    return result.json()
}


new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        minutes: 0,
        hours: 0,
        out_temp: 0,
        temp: 0,
        CO: 0,
        humidity: 0,
        vent_speed:0,
        vent_heat:0,
        load_delay: 0,
        loading: false,     // идёт опрос — новый не запускаем, чтобы запросы не копились

    },
    methods: {

        clock(){
          const now = new Date();
          this.hours = now.getHours();
          this.minutes = now.getMinutes();

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

        async dataLoad() {  // чтение всех данных
            if (this.load_delay) {
                this.load_delay--;
                return
            }
            if (this.loading) return
            this.loading = true
            try {
                // запросы независимы — шлём параллельно, а не по очереди
                const [out_temp, temp, humidity, CO, vent_speed, vent_heat] = await Promise.all([
                    sensor_data(1953992321, 'T'),
                    sensor_data(1953992342, 'T'),
                    sensor_data(1953992342, 'H'),
                    sensor_data(1953992342, 'CO'),
                    sensor_data(vent_id, 'R-100'),
                    sensor_data(vent_id, 'R-206'),
                ])
                this.out_temp = out_temp.data / out_temp.type.divider;
                this.temp = temp.data / temp.type.divider;
                this.humidity = humidity.data / humidity.type.divider;
                this.CO = CO.data / CO.type.divider;
                if (!this.load_delay) {  // пока грузили, могли переключить скорость — не затираем
                    this.vent_speed = vent_speed.data;
                    this.vent_heat = vent_heat.data / 1;
                }
            } finally {
                this.loading = false
            }

        },
    },
    async created() {

        this.clock();
        setInterval(function () {
            this.clock();
        }.bind(this), 1000);


        await this.dataLoad(); // загружаем данные
        setInterval(function () { // обновляем данные каждые 5 секунд, пока вкладка видна
            if (!document.hidden) this.dataLoad()
        }.bind(this), 5000);
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) this.dataLoad()
        });


    }
})
