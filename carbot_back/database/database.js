const { Pool } = require('pg'); // postgres 모듈 불러오기
require('dotenv').config(); // .env 파일 불러오기

const pool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
});

module.exports = pool; // {}로 감쌀 경우 index.js 작성 시 database.pool.query 변수를 함께 작성할 것
