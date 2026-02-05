const mongoose = require('mongoose');
const { Schema } = mongoose;

const PhotoSchema = new Schema({
    name: {type: String, required: true},
    year: {type: Number, required: false},
    city: {type: String, required: false}
});

const getPhotoModel = () => {
  const collection = process.env.PHOTOS_COLLECTION || 'photos';
  const modelName = `Photo_${collection}`;
  return mongoose.models[modelName] || mongoose.model(modelName, PhotoSchema, collection);
};

module.exports = { getPhotoModel };
