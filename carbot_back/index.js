const express = require('express');
const pool = require('./database/database'); // database.js에서 pool 불러오기
const app = express();
const port = 8001;
const session = require('express-session');
const bodyParser = require('body-parser');
const cors = require('cors');

app.use(express.json()); // json파싱
app.use(express.urlencoded({ extended: true })); // URL-encoded 요청을 처리
app.use(bodyParser.json()); // JSON 요청을 처리하도록 body-parser 설정
app.use(cors());

app.use(
  session({
    secret: process.env.SECRET_KEY, // 비밀 키 설정
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 24 * 60 * 60 * 1000 }, // 쿠키 유효 기간 (1일)
  })
);

app.use(
  cors({
    origin: 'http://localhost:3001',
    credentials: true,
  })
);

app.get('/car_info', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM car_info'); // pool.query로 수정
    res.json(result.rows);
  } catch (err) {
    console.error('Error fetching data from PostgreSQL', err);
    res.status(500).send('Error fetching data');
  }
});

app.use(require('./routes/auth/authRoutes'));
app.use(require('./routes/user/userRoutes'));
// Vonage 라우트 추가
app.use('/api/vonage', require('./routes/vonageRoutes'));

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
