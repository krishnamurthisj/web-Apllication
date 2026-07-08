// ---------- Nav background on scroll ----------
const nav = document.getElementById("siteNav");
if (nav) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 40) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  });
}

// ---------- Hero auto-scrolling carousel ----------
(function () {
  const slides = document.querySelectorAll(".hero-slide");
  const dots = document.querySelectorAll(".hero-cat-dot");
  if (!slides.length) return;

  let current = 0;
  const total = slides.length;
  const INTERVAL_MS = 5000;
  let timer;

  function goTo(index) {
    slides[current].classList.remove("active");
    dots[current] && dots[current].classList.remove("active");
    current = (index + total) % total;
    slides[current].classList.add("active");
    dots[current] && dots[current].classList.add("active");
  }

  function next() {
    goTo(current + 1);
  }

  function startAutoplay() {
    timer = setInterval(next, INTERVAL_MS);
  }

  function stopAutoplay() {
    clearInterval(timer);
  }

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      stopAutoplay();
      goTo(parseInt(dot.dataset.index, 10));
      startAutoplay();
    });
  });

  const prevBtn = document.getElementById("heroPrev");
  const nextBtn = document.getElementById("heroNext");

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      stopAutoplay();
      goTo(current - 1);
      startAutoplay();
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      stopAutoplay();
      next();
      startAutoplay();
    });
  }

  startAutoplay();
})();
