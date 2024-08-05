const { exec } = require('child_process');

const url = 'https://www.instagram.com/leomessi/';
const browser = 'Safari'; // You can specify other browsers like 'Safari', 'Firefox', etc.

exec(`open -a "${browser}" "${url}"`, (err) => {
  if (err) {
    console.error(`Error: ${err.message}`);
    return;
  }
  console.log(`Opened ${url} in ${browser}`);
});