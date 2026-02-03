const { getPhotoModel } = require('../models/photo');

const photoCtrl = {}

const resolveDataset = () => {
  const dataset = (process.env.DATASET || 'prod').toLowerCase();
  return dataset === 'test' ? 'test' : 'prod';
};

photoCtrl.getPrueba = (req, res) => {
    res.json({
        status: 'Photos goes here'
    });
}

photoCtrl.getYearPhoto = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const photo = await Photo.aggregate([{ $match: { year: { $exists: true } } }, { $sample: { size: 1 } }]);
    res.json(photo[0]);  
}

photoCtrl.getPhotosCount = async (req, res) => {
    const Photo = getPhotoModel(resolveDataset());
    const count = await Photo.countDocuments({});
    res.json({ count });
}

module.exports = photoCtrl;
