const express = require('express');
const router = express.Router();

const photo = require('../controllers/photo.controller');

router.get('/helloWorld', (req, res) => {
    res.send('Hello World!');
})

router.get('/', photo.getPrueba);
router.get('/year', photo.getYearPhoto);

module.exports = router;
