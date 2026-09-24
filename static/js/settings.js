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


async function fetch_get(url) {  // функция post запросов
    let response = await fetch(url, {
        method: 'get',
        headers: headers_post,

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
       sensor_list: [],


    },
    methods: {

        async load() {
                        await fetch_get('/scada_api/settings/').then((result) => {
                return result.json()
            }).then((result) => {
                this.sensor_list = result;
            })


        },
    },
    async created() {
        await this.load(); // загружаем данные




    }
})

