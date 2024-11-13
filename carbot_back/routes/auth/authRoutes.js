const router = require('express').Router();
const {
  signUp,
  customLogin,
  adminLogin,
  dealerLogin,
  logoutAll,
  findId,
  emailAuth,
  verifyNumber,
  updatePassword,
  verifyUser,
} = require('../../controllers/auth/authController');

router.post('/sign_up', signUp);
router.post('/customer_login', customLogin);
router.post('/admin_login', adminLogin);
router.post('/dealer_login', dealerLogin);
router.post('/all_logout', logoutAll);
router.post('/find_id', findId);
router.post('/send_email', emailAuth);
router.post('/verify_email', verifyNumber);
router.post('/update_pass', updatePassword);
router.post('/verify_user', verifyUser);

module.exports = router;
