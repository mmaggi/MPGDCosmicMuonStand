from influxdb import InfluxDBClient

client = InfluxDBClient(
    host='influxdb',
    port=8086,
    username='admin',
    password='adminpass',
    database='mydb'
)

# Dummy test point
data = [{
    "measurement": "hv_status",
    "tags": {
        "channel": "ch1"
    },
    "fields": {
        "voltage": 1000,
        "current": 0.01
    }
}]

client.write_points(data)
print("Wrote sample HV point to InfluxDB.")
