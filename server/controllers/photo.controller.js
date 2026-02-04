const { getPhotoModel } = require('../models/photo');

const photoCtrl = {}

// Pick the dataset name based on DATASET env, defaulting to prod.
const resolveDataset = () => {
  const dataset = (process.env.DATASET || 'prod').toLowerCase();
  return dataset === 'test' ? 'test' : 'prod';
};

// Simple health/test endpoint to verify the photos API is reachable.
photoCtrl.getPrueba = (req, res) => {
    res.json({
        status: 'Photos goes here'
    });
}

// Return a random photo document that contains a year field.
photoCtrl.getYearPhoto = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const photo = await Photo.aggregate([{ $match: { year: { $exists: true } } }, { $sample: { size: 1 } }]);
    res.json(photo[0]);  
}

// Return a random photo document that contains a city field.
photoCtrl.getCityPhoto = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const photo = await Photo.aggregate([{ $match: { city: { $exists: true } } }, { $sample: { size: 1 } }]);
    res.json(photo[0]);  
}

// Return the total number of photo documents in the active dataset.
photoCtrl.getPhotosCount = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const count = await Photo.countDocuments({});
    res.json({ count });
}

// Return all the cities that appear in the photos dataset.
photoCtrl.getCities = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const cities = await Photo.distinct('city', { city: { $exists: true } });
    res.json(cities);
}

// Return a boolean indicating if there are at least one photo that has the field year.
photoCtrl.hasYearPhoto = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const count = await Photo.countDocuments({ year: { $exists: true } });
    res.json({ hasYearPhoto: count > 0 });
}

module.exports = photoCtrl;
