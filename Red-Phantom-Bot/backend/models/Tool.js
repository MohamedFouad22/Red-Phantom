const mongoose = require('mongoose');

const ToolSchema = new mongoose.Schema({
  slug: { type:String, lowercase:true, index:true },
  name: String,
  description: String,
  examples: [String],
  commands: [{ title:String, cmd:String }],
  tags: [String],
  addedBy: { type: mongoose.Schema.Types.ObjectId, ref:'User' },
  createdAt: { type:Date, default:Date.now }
});

module.exports = mongoose.model('Tool', ToolSchema);
