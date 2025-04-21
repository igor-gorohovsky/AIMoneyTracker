from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisAsyncResultBackend, RedisStreamBroker

from env import REDIS_URL

broker = RedisStreamBroker(url=REDIS_URL).with_result_backend(
    RedisAsyncResultBackend(redis_url=REDIS_URL),
)

scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
