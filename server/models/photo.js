const mongoose = require('mongoose');
const { Schema } = mongoose;

const PhotoSchema = new Schema({
    name: {type: String, required: true},
    year: {type: Number, required: false},
    city: {type: String, required: false}
});

const collectionFor = (dataset) => {
  if (dataset === 'test') return process.env.PHOTOS_COLLECTION_TEST || 'photos_test';
  return process.env.PHOTOS_COLLECTION_PROD || 'photos_prod';
};

const getPhotoModel = (dataset) => {
  const collection = collectionFor(dataset);
  const modelName = `Photo_${collection}`;
  return mongoose.models[modelName] || mongoose.model(modelName, PhotoSchema, collection);
};

module.exports = { getPhotoModel };
