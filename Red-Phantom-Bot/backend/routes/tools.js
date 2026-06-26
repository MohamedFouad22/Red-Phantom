const router = require('express').Router();
const Tool = require('../models/Tool');
const jwt = require('jsonwebtoken');
const JWT_SECRET = process.env.JWT_SECRET || 'change_this';

router.get('/', async (req,res) => {
  const tools = await Tool.find().sort({ name:1 });
  res.json(tools);
});

async function requireAdmin(req,res,next) {
  try {
    const auth = req.headers.authorization;
    if (!auth) return res.status(401).json({ message:'no auth' });
    const token = auth.split(' ')[1];
    const payload = jwt.verify(token, JWT_SECRET);
    if (!payload) return res.status(401).json({ message:'invalid' });
    if (payload.role !== 'admin') return res.status(403).json({ message:'forbidden' });
    req.user = payload;
    next();
  } catch (e) {
    res.status(401).json({ message:'unauth' });
  }
}

router.post('/', requireAdmin, async (req,res) => {
  const { name, slug, description, tags } = req.body;
  const t = await Tool.create({ name, slug, description, tags });
  res.json(t);
});

router.delete('/:id', requireAdmin, async (req,res) => {
  await Tool.findByIdAndDelete(req.params.id);
  res.json({ ok:true });
});

module.exports = router;
