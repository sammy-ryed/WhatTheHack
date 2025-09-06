const canvas = document.getElementById('background');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const stars = [];
const numStars = 300;

// Create stars
for(let i = 0; i < numStars; i++){
    stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 3.5,
        speed: Math.random() * 0.5 + 0.2
    });
}

// Animate stars
function animate() {
    ctx.fillStyle = 'rgba(0, 0, 20, 0.8)'; // Dark space background
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for(let star of stars){
        star.y += star.speed;
        if(star.y > canvas.height){
            star.y = 0;
            star.x = Math.random() * canvas.width;
        }
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'white';
        ctx.fill();
    }

    requestAnimationFrame(animate);
}

animate();

// Handle resizing
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
