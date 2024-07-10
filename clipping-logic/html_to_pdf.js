const fs = require('fs');
const puppeteer = require('puppeteer');

async function htmlToPDF(filePath, outputFilename) {
    const htmlContent = fs.readFileSync(filePath, 'utf8');
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
    await page.pdf({
        path: outputFilename,
        format: 'A4',
        printBackground: true
    });
    await browser.close();
}

const outputFilename = process.argv[2];
const filePath = process.argv[3];

htmlToPDF(filePath, outputFilename);
