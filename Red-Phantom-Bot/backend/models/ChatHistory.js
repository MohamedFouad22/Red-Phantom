const mongoose = require('mongoose');

const ChatHistorySchema = new mongoose.Schema({
  sessionId: String,
  userId: { type: mongoose.Schema.Types.ObjectId, ref:'User', default:null },
  messages: [{ from: String, text: String, timestamp: Date }]
});

module.exports = mongoose.model('ChatHistory', ChatHistorySchema);
