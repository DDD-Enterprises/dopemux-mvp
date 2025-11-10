from locust import HttpUser, task, between

class DopemuxUser(HttpUser):
    wait_time = between(1, 3)  # Random wait between 1-3 seconds

    @task(3)
    def test_adhd_engine_health(self):
        """Test ADHD Engine health endpoint"""
        self.client.get("http://localhost:18001/health", name="ADHD Engine Health")

    @task(2)
    def test_conport_health(self):
        """Test ConPort health endpoint"""
        self.client.get("http://localhost:13004/health", name="ConPort Health")

    @task(2)
    def test_serena_health(self):
        """Test Serena MCP health endpoint"""
        self.client.get("http://localhost:13001/health", name="Serena MCP Health")

    @task(1)
    def test_task_orchestrator_health(self):
        """Test Task Orchestrator health endpoint"""
        self.client.get("http://localhost:18002/health", name="Task Orchestrator Health")

    @task(1)
    def test_prometheus_health(self):
        """Test Prometheus health endpoint"""
        self.client.get("http://localhost:19090/-/healthy", name="Prometheus Health")

    @task(1)
    def test_qdrant_collections(self):
        """Test Qdrant collections endpoint"""
        self.client.get("http://localhost:16333/collections", name="Qdrant Collections")