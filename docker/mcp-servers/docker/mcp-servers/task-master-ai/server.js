const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'task-master-ai' });
});

app.get('/api/tasks', (req, res) => {
  res.json({ tasks: [], message: 'Task Master AI service ready' });
});

const port = process.env.PORT || 3005;
app.listen(port, () => {
  console.log(`Task Master AI service listening on port ${port}`);
});