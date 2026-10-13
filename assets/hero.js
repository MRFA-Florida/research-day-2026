// Random header photo on each visit. To add a photo: upload a wide image to assets/img/hero/
// (plus an optional "-sm" phone version) and add a line below. "pos" is the horizontal focus
// point used when phones crop the photo (0% = left edge, 100% = right edge).
(function () {
  var photos = [
    { name: "campus-facade",     pos: "70%" },
    { name: "campus-palms",      pos: "55%" },
    { name: "campus-tower",      pos: "62%" },
    { name: "campus-hospital",   pos: "62%" },
    { name: "campus-palms-sky",  pos: "50%" },
    { name: "campus-sculpture",  pos: "78%" }
  ];
  var p = photos[Math.floor(Math.random() * photos.length)];
  // Absolute URLs: a relative url() inside a CSS variable would resolve against styles.css, not the page.
  var r = document.documentElement.style, base = new URL("assets/img/hero/" + p.name, document.baseURI).href;
  r.setProperty("--hero-lg", 'url("' + base + '.jpg")');
  r.setProperty("--hero-sm", 'url("' + base + '-sm.jpg")');
  r.setProperty("--hero-pos", p.pos);
})();
