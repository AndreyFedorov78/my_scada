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

new Vue({
    el: '#app',
    data: {
        widgets_list: [],   //
        widgets_new: [],   //
        vent: [],  // данные венустанвки
        charts: [], // графики


    },
    methods: {
        async exit(){
            await fetch('/api/logout/')
            window.location.href = "/"
            //router.push("/")
            /*/accounts/login/?next=/*/


        },


        async ventManage(name, val) {      // переключение венташины
            this.vent[name] = val;
            let toSend = {};
            toSend[name] = val;
            await fetch_post('/scada_api/vent/', toSend)
        },

        async delete_widget(id) {
            await fetch_delete('/scada_api/mywidgets/'+id+'/')
            this.load_last()

        },

        async add_widget(id) {
            await fetch_put('/scada_api/mywidgets/'+id+'/')
            this.load_last()

        },

        async move_widget(id, step) {
            await fetch_post('/scada_api/mywidgets/'+id+'/', {'step':step})
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
            fetch('/scada_api/vent/').then((response) => {return response.json()}).then((data) => {this.vent = data;});
            await this.load_widget_list(); // получаем перечень виджетов
            await this.load_widget_new();

        },
    },
    async created() {
        await this.load_last(); // загружаем данные

        setInterval(function () { // обновляем данные каждые 20 секунд
              this.load_last()
        }.bind(this), 20000);
    }
})



