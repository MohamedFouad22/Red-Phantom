const mongoose = require('mongoose');
require('dotenv').config();
const Tool = require('../models/Tool');
const tools = require('./tools_seed.json');

async function run() {
  await mongoose.connect(process.env.MONGO_URI);
  console.log('connected');
  await Tool.deleteMany({});
  await Tool.insertMany(tools);
  console.log('seeded', tools.length);
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });