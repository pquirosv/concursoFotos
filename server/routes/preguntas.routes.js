const express = require('express');
const router = express.Router();

const photo = require('../controllers/photo.controller');

router.get('/helloWorld', (req, res) => {
    res.send('Hello World!');
})

router.get('/', photo.getPrueba);
router.get('/year', photo.getYearPhoto);
router.get('/city', photo.getCityPhoto);
router.get('/cities', photo.getCities);
router.get('/photos/count', photo.getPhotosCount);
router.get('/photos/hasYearPhoto', photo.hasYearPhoto);

module.exports = router;
