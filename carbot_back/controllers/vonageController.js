const { Vonage } = require('@vonage/server-sdk');
// const WebSocket = require('ws');
// const Speaker = require('speaker');
// const wav = require('wav');
// const fs = require('fs');
require('dotenv').config();

// const axios = require('axios');
// const { Auth } = require('@vonage/auth'); // JWT 생성을 위한 Auth 모듈
// const jwt = require('jsonwebtoken');

// Vonage API 설정
const vonage = new Vonage({
  applicationId: process.env.VONAGE_APPLICATION_ID,
  privateKey: process.env.VONAGE_APPLICATION_PRIVATE_KEY_PATH,
});

// NCCO 생성 함수 (WebSocket URI 유지) 1차 코드
function getNcco() {
  return [
    {
      action: 'talk',
      text: '안녕하세요! 카봇입니다. 무엇을 도와드릴까요?',
      // text: responseText,
      language: 'ko-KR',
      style: 1,
    },
    {
      action: 'connect',
      endpoint: [
        {
          type: 'websocket',
          uri: 'wss://1d33-222-112-27-104.ngrok-free.app/ws', // FastAPI WebSocket URI
          contentType: 'audio/l16;rate=16000',
          headers: {
            language: 'ko-KR',
          },
          keepAlive: true,
        },
      ],
    },
  ];
}

// Vonage에서 전화를 수신하기 위한 핸들러 여기만 주석
async function handleIncomingCall(req, res) {
  console.log('전화를 수신했습니다.');
  const ncco = getNcco();
  console.log('NCCO : ', JSON.stringify(ncco, null, 2));
  res.json(ncco); // NCCO를 반환하여 Vonage가 호출할 수 있도록 합니다.
}

module.exports = { handleIncomingCall };

// // WebSocket 메시지 처리 함수
// const ws = new WebSocket('wss://1d33-222-112-27-104.ngrok-free.app/ws');

// ws.on('open', () => {
//   console.log('WebSocket 연결이 수립되었습니다.');
// });

// ws.on('message', (data) => {
//   console.log(`수신된 TTS 데이터 길이: ${data.length}`);

//   if (!callUuid) {
//     console.error('UUID가 정의되지 않았습니다.');
//     return;
//   }

//   // Vonage API를 사용하여 TTS 데이터를 통화에 스트리밍
//   vonage.calls.stream.start(
//     callUuid,
//     {
//       streamUrl: [`data:audio/wav;base64,${data.toString('base64')}`],
//       loop: 1,
//     },
//     (error, response) => {
//       if (error) {
//         console.error(`TTS 스트리밍 오류: ${error}`);
//       } else {
//         console.log('TTS 스트리밍 시작:', response);
//       }
//     }
//   );
// });

// ws.on('error', (error) => {
//   console.error(`WebSocket 오류: ${error.message}`);
// });

// ws.on('close', () => {
//   console.log('WebSocket 연결이 종료되었습니다.');
// });

// // Vonage에서 통화 업데이트를 위한 엔드포인트
// const updateResponseText = async (req, res) => {
//   const { text } = req.body;
//   console.log(`응답 텍스트 업데이트: ${text}`);

//   if (!callUuid) {
//     console.error('UUID가 정의되지 않았습니다.');
//     return res.status(400).send('UUID가 없습니다.');
//   }

//   try {
//     vonage.calls.talk.start(
//       callUuid,
//       {
//         text,
//         language: 'ko-KR',
//         style: 1,
//       },
//       (error, response) => {
//         if (error) {
//           console.error(`TTS 재생 오류: ${error}`);
//           res.status(500).send(`TTS 재생 오류: ${error}`);
//         } else {
//           console.log('TTS 재생 시작:', response);
//           res.sendStatus(200);
//         }
//       }
//     );
//   } catch (error) {
//     console.error(`예외 처리 오류: ${error.message}`);
//     res.status(500).send(`예외 처리 오류: ${error.message}`);
//   }
// };

// module.exports = { handleIncomingCall, updateResponseText };

// 텍스트 응답을 Vonage TTS API를 통해 전화 통화로 재생 (수정 전)
// async function updateResponseText(req, res) {
//   const { text } = req.body;
//   console.log(`응답 텍스트 업데이트: ${text}`);

//   if (!callUuid) {
//     return res.status(400).send('UUID가 없습니다.');
//   }

//   try {
//     await vonage.voice.talk.start(callUuid, {
//       text,
//       language: 'ko-KR',
//       style: 1,
//     });
//     console.log('TTS 재생 시작');
//     res.sendStatus(200);
//   } catch (error) {
//     console.error(`TTS 재생 오류: ${error}`);
//     res.status(500).send(`TTS 재생 오류: ${error.message}`);
//   }
// }

// const { Vonage } = require('@vonage/server-sdk');
// const WebSocket = require('ws');
// const textToSpeech = require('@google-cloud/text-to-speech');
// const fs = require('fs').promises;
// const { PassThrough } = require('stream');
// require('dotenv').config();

// // 환경 변수 설정 (Google Cloud 인증서 경로)
// process.env.GOOGLE_APPLICATION_CREDENTIALS =
//   '/Users/shimgeon-u/test/carbot_back_2/carbot_back/credentials.json';

// // Vonage API 설정
// const vonage = new Vonage({
//   applicationId: process.env.VONAGE_APPLICATION_ID,
//   privateKey: process.env.VONAGE_APPLICATION_PRIVATE_KEY_PATH,
// });

// const ttsClient = new textToSpeech.TextToSpeechClient();
// let callUuid = null;

// // NCCO 생성 함수
// function getNcco() {
//   return [
//     {
//       action: 'talk',
//       text: '안녕하세요! 카봇입니다. 무엇을 도와드릴까요?',
//       language: 'ko-KR',
//       style: 1,
//     },
//     {
//       action: 'connect',
//       endpoint: [
//         {
//           type: 'websocket',
//           // uri: 'wss://your-fastapi-websocket-url/ws',
//           uri: 'wss://1d33-222-112-27-104.ngrok-free.app/ws', // FastAPI WebSocket URI
//           contentType: 'audio/l16;rate=16000',
//           headers: {
//             language: 'ko-KR',
//           },
//           keepAlive: true,
//         },
//       ],
//     },
//   ];
// }

// // Vonage에서 전화를 수신하기 위한 핸들러
// async function handleIncomingCall(req, res) {
//   console.log('전화를 수신했습니다.');
//   const ncco = getNcco();

//   if (req.body && req.body.uuid) {
//     callUuid = req.body.uuid;
//     console.log(`callUuid 저장 완료: ${callUuid}`);
//   } else {
//     console.error('UUID가 제공되지 않았습니다.');
//   }

//   res.json(ncco);
// }

// // Google Cloud TTS로 텍스트를 음성으로 변환
// async function convertTextToSpeech(text) {
//   const request = {
//     input: { text },
//     voice: {
//       languageCode: 'ko-KR',
//       ssmlGender: 'NEUTRAL',
//     },
//     audioConfig: {
//       audioEncoding: 'LINEAR16',
//     },
//   };

//   try {
//     const [response] = await ttsClient.synthesizeSpeech(request);
//     console.log('TTS 변환 완료');
//     return response.audioContent;
//   } catch (error) {
//     console.error(`TTS 변환 오류: ${error.message}`);
//     return null;
//   }
// }

// // WebSocket을 통해 TTS 오디오 스트리밍 전송
// async function streamTtsAudio(ws, audioContent) {
//   const stream = new PassThrough();
//   stream.end(audioContent);

//   stream.on('data', (chunk) => {
//     ws.send(chunk);
//   });

//   stream.on('end', () => {
//     console.log('TTS 오디오 스트리밍 완료');
//     ws.close();
//   });

//   stream.on('error', (error) => {
//     console.error(`오디오 스트리밍 오류: ${error.message}`);
//   });
// }

// // LangChain 응답 텍스트 업데이트 및 TTS 재생
// async function updateResponseText(req, res) {
//   const { text } = req.body;
//   console.log(`응답 텍스트 업데이트: ${text}`);

//   if (!text) {
//     return res.status(400).send('텍스트가 없습니다.');
//   }

//   try {
//     const audioContent = await convertTextToSpeech(text);

//     if (!audioContent) {
//       return res.status(500).send('TTS 변환 실패');
//     }

//     const ws = new WebSocket('wss://your-fastapi-websocket-url/ws');
//     ws.on('open', () => {
//       console.log('WebSocket 연결이 열렸습니다. TTS 오디오 스트리밍 시작');
//       streamTtsAudio(ws, audioContent);
//     });

//     ws.on('error', (error) => {
//       console.error(`WebSocket 오류: ${error.message}`);
//     });

//     ws.on('close', () => {
//       console.log('WebSocket 연결이 닫혔습니다.');
//     });

//     res.sendStatus(200);
//   } catch (error) {
//     console.error(`응답 처리 오류: ${error.message}`);
//     res.status(500).send(`오류: ${error.message}`);
//   }
// }

// module.exports = { handleIncomingCall, updateResponseText };
