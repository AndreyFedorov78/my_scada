// Минимальный MQTT 3.1.1 клиент поверх WebSocket — только подписка (QoS 0), без публикации:
// команды устройствам идут через Django (/scada_api/devmanage/), где проверяется вход.
// Сам переподключается; живость — по PINGRESP на keepalive.

class MqttWs {
    constructor(url, topic, on_message, on_state) {
        this.url = url
        this.topic = topic
        this.on_message = on_message      // (topic, payload-строка)
        this.on_state = on_state || (() => {})  // (true/false) — есть ли живое подключение
        this.keepalive = 20               // с
        this.retry = 1000                 // мс, растёт до 30 с
        this.alive = false
        this.last_seen = 0                // когда брокер последний раз что-то прислал
        this.last_sent = 0                // когда мы последний раз что-то отправили
        this.buffer = new Uint8Array(0)
        this.decoder = new TextDecoder()
        this.encoder = new TextEncoder()
        this.connect()
        setInterval(() => this.check(), 5000)
    }

    connect() {
        clearTimeout(this.retry_timer)
        let ws
        try {
            ws = new WebSocket(this.url, 'mqtt')
        } catch (error) {
            this.reconnect()
            return
        }
        this.ws = ws
        ws.binaryType = 'arraybuffer'
        this.buffer = new Uint8Array(0)
        ws.onopen = () => this.send(this.packet_connect())
        ws.onmessage = event => {
            this.last_seen = Date.now()
            this.receive(new Uint8Array(event.data))
        }
        ws.onclose = () => {
            if (this.ws !== ws) return
            this.set_alive(false)
            this.reconnect()
        }
        ws.onerror = () => ws.close()
    }

    send(packet) {
        this.last_sent = Date.now()
        this.ws.send(packet)
    }

    reconnect() {
        this.retry_timer = setTimeout(() => this.connect(), this.retry)
        this.retry = Math.min(this.retry * 2, 30000)
    }

    set_alive(alive) {
        if (this.alive === alive) return
        this.alive = alive
        this.on_state(alive)
    }

    // пинг и проверка, что брокер отвечает
    check() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
        if (this.alive && Date.now() - this.last_seen > this.keepalive * 1500) {
            this.ws.close()   // молчит дольше keepalive — соединение подвисло
            return
        }
        // брокер отключает клиента, от которого ничего не приходило 1.5 keepalive, даже если сам шлёт показания
        if (Date.now() - this.last_sent > this.keepalive * 500) this.send(new Uint8Array([0xC0, 0]))  // PINGREQ
    }

    // --- кодирование пакетов ---

    static length_bytes(length) {
        const bytes = []
        do {
            let byte = length % 128
            length = Math.floor(length / 128)
            if (length > 0) byte |= 0x80
            bytes.push(byte)
        } while (length > 0)
        return bytes
    }

    string_bytes(text) {
        const bytes = this.encoder.encode(text)
        return [bytes.length >> 8, bytes.length & 0xff, ...bytes]
    }

    static packet(type, body) {
        return new Uint8Array([type, ...MqttWs.length_bytes(body.length), ...body])
    }

    packet_connect() {
        const client_id = 'web-' + Math.random().toString(36).slice(2, 12)
        return MqttWs.packet(0x10, [
            ...this.string_bytes('MQTT'), 4,       // протокол 3.1.1
            0x02,                                  // clean session
            this.keepalive >> 8, this.keepalive & 0xff,
            ...this.string_bytes(client_id),
        ])
    }

    packet_subscribe() {
        return MqttWs.packet(0x82, [0, 1, ...this.string_bytes(this.topic), 0])
    }

    // --- разбор входящего потока (в одном сообщении WebSocket может быть несколько пакетов) ---

    receive(chunk) {
        const joined = new Uint8Array(this.buffer.length + chunk.length)
        joined.set(this.buffer)
        joined.set(chunk, this.buffer.length)
        let pos = 0
        while (joined.length - pos >= 2) {
            let length = 0, multiplier = 1, i = pos + 1, byte
            do {
                if (i >= joined.length) break
                byte = joined[i++]
                length += (byte & 0x7f) * multiplier
                multiplier *= 128
            } while (byte & 0x80)
            if (byte & 0x80 || i + length > joined.length) break  // пакет пришёл не целиком
            this.handle(joined[pos], joined.subarray(i, i + length))
            pos = i + length
        }
        this.buffer = joined.slice(pos)
    }

    handle(header, body) {
        const type = header >> 4
        if (type === 2) {                   // CONNACK
            if (body[1] === 0) {
                this.retry = 1000
                this.send(this.packet_subscribe())
            } else {
                this.ws.close()
            }
        } else if (type === 9) {            // SUBACK
            this.set_alive(body[2] !== 0x80)
        } else if (type === 3) {            // PUBLISH
            const topic_length = (body[0] << 8) | body[1]
            const topic = this.decoder.decode(body.subarray(2, 2 + topic_length))
            const qos = (header >> 1) & 3
            const payload = body.subarray(2 + topic_length + (qos ? 2 : 0))
            this.on_message(topic, this.decoder.decode(payload))
        }
    }
}
