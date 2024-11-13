const express = require('express');
const router = express.Router();
const {
  handleIncomingCall,
  updateResponseText,
} = require('../controllers/vonageController');

// Vonage 전화를 수신하기 위한 엔드포인트
router.post('/answer', handleIncomingCall); // Vonage에서 호출되는 엔드포인트

// Python에서 LangChain 응답을 업데이트하는 엔드포인트
// router.post('/update-text', updateResponseText);

module.exports = router;
