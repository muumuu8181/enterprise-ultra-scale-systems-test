from locust import HttpUser, task, between

class GachaUser(HttpUser):
    wait_time = between(1, 3)

    @task(7)
    def pull_gacha(self):
        self.client.post("/gacha/pull", json={"count": 10})

    @task(3)
    def view_rankings(self):
        self.client.get("/rankings/top100")
