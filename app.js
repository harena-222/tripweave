const express = require('express');
const cors = require('cors');
const axios = require('axios');
const app = express();
const port = 3000;

app.use(express.json());
app.use(cors());

// ★ここを追加：ルート（'/'）へのアクセスを許可する
app.get('/', (req, res) => {
  res.send('TripWeave Backend is running!');
});

// データの受け取り用API
app.post('/api/trip', async (req, res) => {
  const inputData = req.body.destination;
  console.log('受け取ったデータ:', inputData);
  try {
    const pythonResponse = await axios.post('http://localhost:8000/ai/process', {
      raw_prompt: inputData,
      traveller_id: "traveller:idiots" // temporary user ID
    });

    const aiResult = pythonResponse.data;
    console.log('result from python:', aiResult);

    res.json({
      message: `AI result: ${aiResult.data.intent}!`,
      details: aiResult.data
    });

  } catch (error) {
    console.error('python server connection failed:', error.message);
    res.status(500).json({ message: "we couldn't connect to the AI server." });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});