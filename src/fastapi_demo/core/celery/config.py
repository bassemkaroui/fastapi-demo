"""
This configuration is base on these recommendations:
https://gist.github.com/fjsj/da41321ac96cf28a96235cb20e7236f6
"""

from typing import Any

from kombu import Exchange, Queue

default_exchange = Exchange("default", type="direct", durable=True)
default_queue = Queue("default", exchange=default_exchange, routing_key="default", durable=True)


def make_config() -> dict[str, Any]:
    return {
        # serialization
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        # reliability
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        "task_default_delivery_mode": "persistent",
        "broker_transport_options": {"confirm_publish": True, "confirm_timeout": 5.0},
        "broker_connection_timeout": 30,
        # worker tuning
        "worker_prefetch_multiplier": 1,
        "broker_pool_limit": 10,
        "broker_heartbeat": 120,
        # "redis_max_connections": None,
        "worker_max_tasks_per_child": 1000,
        # queues (use kombu Queue objects)
        "task_default_queue": "default",
        "task_default_exchange": "default",
        "task_default_routing_key": "default",
        "task_queues": [default_queue],
        # helpful defaults
        "timezone": "UTC",
        "enable_utc": True,
        # flower
        "worker_send_task_events": True,
        "event_queue_expires": 60,
        "event_queue_ttl": 5,
    }
