new Vue({
    el: '#app',
    data: {
        sensors_list: [],
        rooms_list: [],
	vent: [],
        listOfTypes : {'100': 'Температура', '200': 'CO2'},
        listOfMeters : {'100': 'C', '200': 'ppt'},
        listOfRooms : {'1' : 'Гостиная', '2' : 'Спальня'}
    },
    async created() {

        fetch('/scada_api/allsensors/').then((response) => {
            return response.json();
        }).then((data) => {
            data.sort((a, b) => (a.sensorId > b.sensorId) ? 1 : ((b.sensorId > a.sensorId) ? -1 : 0))
            let lastId = -1
            let tmp_arr = []

            for (x = 0; x < data.length; x++) {
                let tmp = {type: data[x].type, data: data[x].data, date: new Date(data[x].date.substring(0,19))}
                var now = new  Date()
                tmp.s_type = this.listOfTypes[data[x].type]
                tmp.meters = this.listOfMeters[data[x].type]
                tmp.online = (now.getTime()-tmp.date.getTime() < 150000)? 1 : 0
                if (lastId != data[x].sensorId) {
                    lastId = data[x].sensorId
                    this.rooms_list.push(this.listOfRooms[lastId])
                    if (x != 0) this.sensors_list.push(tmp_arr)
                    tmp_arr = [tmp]
                } else
                    tmp_arr.push(tmp)
            }

            this.sensors_list.push(tmp_arr)


        });
	fetch('/scada_api/vent/').then((response) => {
            return response.json();
        }).then((data) => {
	    this.vent = data;
	    
	})
    }
})

/*

const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
        datasets: [{
            label: '# of Votes',
            data: [12, 19, 3, 150, 2, 3],
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
                'rgba(153, 102, 255, 0.2)',
                'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
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
*/
