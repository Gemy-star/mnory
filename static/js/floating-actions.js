document.addEventListener('DOMContentLoaded', function() {
    const fabMenu = document.querySelector('.fab-menu');
    const fabMain = document.querySelector('.fab-main');

    if (fabMain) {
        fabMain.addEventListener('click', function() {
            fabMenu.classList.toggle('active');
        });
    }
});
