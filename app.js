const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;

app.use(express.json());
app.use(cors());

// ★ここを追加：ルート（'/'）へのアクセスを許可する
app.get('/', (req, res) => {
  res.send('TripWeave Backend is running!');
});

// データの受け取り用API
app.post('/api/trip', (req, res) => {
  const inputData = req.body.destination;
  console.log('受け取ったデータ:', inputData);
  res.json({ message: "I love you too! あなたが選んだのは: " + inputData });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});