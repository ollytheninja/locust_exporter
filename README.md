# Prometheus Metrics Exporter for Locust

A locust exporter for prometheus, forked from [mbolek/locust_exporter](https://github.com/mbolek/locust_exporter)

This is a simple exporter for http://locust.io metrics.
You get all the necessary details about current tests and the state of the locust.

Errors and requests stats are added with the method and path labels - BE CAREFUL - if you have a lot of endpoints.
It is probably better to group the endpoints in your locustfile (please
see: http://docs.locust.io/en/latest/writing-a-locustfile.html#grouping-requests-to-urls-with-dynamic-parameters).

## Setup

This project uses [UV](https://docs.astral.sh/uv/).

- Install uv
- run `uv sync`
- You can now `uv run locust_exporter.py <listen_port> <locust_host:port>`

## Usage

Run the exporter with:

`./locust_exporter.py`

## Configuration

| Environment Variable | Description                          | Default                 |
|:---------------------|:-------------------------------------|:------------------------|
| `LOCUST_URI`         | The locust address to connect to     | `http://localhost:8089` |
| `LISTEN_PORT`        | The port the exporter will listen on | `8088`                  |


![example metrics response](./docs/locust_exporter.png)
