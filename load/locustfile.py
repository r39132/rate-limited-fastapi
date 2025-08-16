from locust import HttpUser, between, task


class APIUser(HttpUser):
    wait_time = between(0.0, 0.1)

    def on_start(self) -> None:
        """Called when a user starts before any task is scheduled."""
        pass

    @task
    def call_items(self) -> None:
        self.client.get("/items")
