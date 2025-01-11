import json
import logging
import os
import time

import requests
from prometheus_client import start_http_server, REGISTRY
from prometheus_client.metrics_core import GaugeMetricFamily, CounterMetricFamily

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LocustCollector:
    def __init__(self, uri):
        self._uri = uri

    def collect(self):
        # Fetch the JSON
        url = self._uri + "/stats/requests"
        try:
            response = requests.get(url).content.decode("Utf-8")
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Locust:", url)
            return None

        response = json.loads(response)

        # User count
        yield GaugeMetricFamily(
            "locust_user_count", "Swarmed users", value=response["user_count"]
        )

        if "slave_count" in response:
            yield GaugeMetricFamily(
                "locust_slave_count",
                "Locust number of slaves",
                value=response["slave_count"],
            )

        # Errors
        for err in response["errors"]:
            metric = GaugeMetricFamily(
                "locust_errors", "Locust requests errors", labels=["path", "method"]
            )
            metric.add_metric(
                [str(err["name"]), err["method"]], value=err["occurrences"]
            )
            yield metric

        yield GaugeMetricFamily(
            "locust_fail_ratio", "Locust failure ratio", value=response["fail_ratio"]
        )

        metric = GaugeMetricFamily(
            "locust_state", "State of the locust swarm", labels=["state"]
        )
        metric.add_metric([str(response["state"])], 1)
        yield metric

        stats_metrics_gauge = [
            "avg_content_length",
            "avg_response_time",
            "current_rps",
            "max_response_time",
            "median_response_time",
            "min_response_time",
        ]
        stats_metrics_count = ["num_failures", "num_requests"]
        for mtr in stats_metrics_gauge:
            metric = GaugeMetricFamily(
                "locust_requests_" + mtr,
                "locust requests " + mtr,
                labels=["path", "method"],
            )
            for stat in response["stats"]:
                if "Total" not in stat["name"]:
                    metric.add_metric(
                        [str(stat["name"]), str(stat["method"])], stat[mtr]
                    )
            yield metric
            for mtr in stats_metrics_count:
                metric = CounterMetricFamily(
                    "locust_requests_" + mtr,
                    "locust requests " + mtr,
                    labels=["path", "method"],
                )
                for stat in response["stats"]:
                    if "Total" not in stat["name"]:
                        metric.add_metric(
                            [str(stat["name"]), str(stat["method"])], stat[mtr]
                        )
                yield metric

        percentiles = ["50", "95", "99"]
        for percentile in percentiles:
            if f"current_response_time_percentile_{percentile}" in response.keys():
                yield GaugeMetricFamily(
                    f"locust_response_time_{percentile}",
                    f"Response Time {percentile}th Percentile",
                    value=response[f"current_response_time_percentile_{percentile}"],
                )


if __name__ == "__main__":
    listen_port = os.environ.get("LISTEN_PORT", 8088)
    locust_uri = os.environ.get("LOCUST_URI", "http://localhost:8089")

    try:
        start_http_server(listen_port)
        REGISTRY.register(LocustCollector(locust_uri))
        logger.info("Connecting to locust at: " + locust_uri)
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        exit(0)
