// Theme toggle — Dark/Light Mode
(function () {
    const tt = document.getElementById('themeToggle');
    const im = document.getElementById('iconMoon');
    const is = document.getElementById('iconSun');
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-mode');
        if (im) im.style.display = 'none';
        if (is) is.style.display = 'block';
    }
    if (tt) {
        tt.addEventListener('click', () => {
            document.body.classList.toggle('light-mode');
            if (document.body.classList.contains('light-mode')) {
                localStorage.setItem('theme', 'light');
                if (im) im.style.display = 'none';
                if (is) is.style.display = 'block';
            } else {
                localStorage.setItem('theme', 'dark');
                if (im) im.style.display = 'block';
                if (is) is.style.display = 'none';
            }
        });
    }
})();
