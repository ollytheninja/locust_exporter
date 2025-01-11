import json
import sys
import time

import requests
from prometheus_client import start_http_server, Metric, REGISTRY


class LocustCollector:
    def __init__(self, ep):
        self._ep = ep

    def collect(self):
        # Fetch the JSON
        url = "http://" + self._ep + "/stats/requests"
        try:
            response = requests.get(url).content.decode("Utf-8")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to Locust:", url)
            exit(2)

        response = json.loads(response)

        stats_metrics = [
            "avg_content_length",
            "avg_response_time",
            "current_rps",
            "max_response_time",
            "median_response_time",
            "min_response_time",
            "num_failures",
            "num_requests",
        ]

        metric = Metric("locust_user_count", "Swarmed users", "gauge")
        metric.add_sample("locust_user_count", value=response["user_count"], labels={})
        yield metric

        metric = Metric("locust_errors", "Locust requests errors", "gauge")
        for err in response["errors"]:
            labels = {
                "path": err["name"] or "unknown",
                "method": err["method"] or "unknown",
            }
            metric.add_sample(
                "locust_errors",
                value=err["occurences"],
                labels=labels,
            )
        yield metric

        if "slave_count" in response:
            metric = Metric("locust_slave_count", "Locust number of slaves", "gauge")
            metric.add_sample(
                "locust_slave_count", value=response["slave_count"], labels={}
            )
            yield metric

        metric = Metric("locust_fail_ratio", "Locust failure ratio", "gauge")
        metric.add_sample("locust_fail_ratio", value=response["fail_ratio"], labels={})
        yield metric

        metric = Metric("locust_state", "State of the locust swarm", "gauge")
        metric.add_sample("locust_state", value=1, labels={"state": response["state"]})
        yield metric

        for mtr in stats_metrics:
            mtype = "gauge"
            if mtr in ["num_requests", "num_failures"]:
                mtype = "counter"
            metric = Metric("locust_requests_" + mtr, "Locust requests " + mtr, mtype)
            for stat in response["stats"]:
                if "Total" not in stat["name"]:
                    labels = {
                        "path": stat["name"] or "unknown",
                        "method": stat["method"] or "unknown",
                    }
                    metric.add_sample(
                        "locust_requests_" + mtr,
                        value=stat[mtr],
                        labels=labels,
                    )
            yield metric


if __name__ == "__main__":
    # Usage: locust_exporter.py <port> <locust_host:port>
    if len(sys.argv) != 3:
        print("Usage: locust_exporter.py <port> <locust_host:port>")
        exit(1)

    try:
        server_port = int(sys.argv[1])
        locust_host_port = str(sys.argv[2])
        start_http_server(server_port)
        REGISTRY.register(LocustCollector(locust_host_port))
        print("Connecting to locust on: " + sys.argv[2])
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        exit(0)
