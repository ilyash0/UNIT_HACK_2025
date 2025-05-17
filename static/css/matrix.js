const canvas = document.getElementById('matrix');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const columns = Math.floor(canvas.width / 20);
const drops = Array(columns).fill(1);

function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#0f0';
    ctx.font = '15px monospace';

    drops.forEach((y, i) => {
        const text = String.fromCharCode(Math.floor(Math.random() * 128));
        ctx.fillText(text, i * 20, y * 20);

        if (y * 20 > canvas.height && Math.random() > 0.975) {
            drops[i] = 0;
        } else {
            drops[i]++;
        }
    });
}

setInterval(draw, 33);