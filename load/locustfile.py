
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(0.0, 0.1)

    @task
    def call_items(self):
        self.client.get("/items")
