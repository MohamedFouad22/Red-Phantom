const router = require('express').Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const User = require('../models/User');

const ADMIN_INVITE = process.env.ADMIN_INVITE_CODE;
const JWT_SECRET = process.env.JWT_SECRET;

router.post('/signup', async (req,res) => {
  try {
    const { name, email, password, inviteCode } = req.body;
    if (!name || !email || !password) return res.json({ success:false, message:'الحقول ناقصة' });
    const exists = await User.findOne({ email });
    if (exists) return res.json({ success:false, message:'المستخدم موجود' });
    const hash = await bcrypt.hash(password, 10);
    const role = (inviteCode && inviteCode === ADMIN_INVITE) ? 'admin' : 'user';
    const u = await User.create({ name, email, passwordHash: hash, role });
    res.json({ success:true, user:{ id:u._id, email:u.email, name:u.name } });
  } catch (e) {
    res.status(500).json({ success:false, message:'خطأ' });
  }
});

router.post('/login', async (req,res) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user) return res.json({ success:false, message:'غير موجود' });
    const ok = await bcrypt.compare(password, user.passwordHash);
    if (!ok) return res.json({ success:false, message:'بيانات خاطئة' });
    const token = jwt.sign({ id:user._id, role:user.role }, JWT_SECRET, { expiresIn:'7d' });
    res.json({ success:true, token, user:{ name:user.name, email:user.email, role:user.role } });
  } catch (e) {
    res.status(500).json({ success:false, message:'خطأ' });
  }
});

router.get('/me', async (req,res) => {
  try {
    const auth = req.headers.authorization;
    if (!auth) return res.json({ success:false, message:'no auth' });
    const token = auth.split(' ')[1];
    const payload = jwt.verify(token, JWT_SECRET);
    const user = await User.findById(payload.id).select('-passwordHash');
    res.json({ success:true, user });
  } catch (e) {
    res.status(401).json({ success:false, message:'unauth' });
  }
});

module.exports = router;
