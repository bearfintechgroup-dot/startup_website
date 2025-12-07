particlesJS("particles-js", {
  particles: {
    number: {
      value: 140,
      density: {
        enable: true,
        value_area: 800
      }
    },
    color: {
      value: ["#b388ff", "#7f5cff", "#5b9dff"]
    },
    shape: {
      type: "circle"
    },
    opacity: {
      value: 0.6,
      random: true
    },
    size: {
      value: 3,
      random: true
    },
    line_linked: {
      enable: true,
      distance: 150,
      color: "#7f5cff",
      opacity: 0.4,
      width: 1
    },
    move: {
      enable: true,
      speed: 1.2,
      direction: "none",
      out_mode: "out"
    }
  },
  interactivity: {
    detect_on: "canvas",
    events: {
      onhover: { enable: true, mode: "repulse" },
      onclick: { enable: true, mode: "push" }
    },
    modes: {
      repulse: { distance: 120 },
      push: { particles_nb: 4 }
    }
  },
  retina_detect: true
});
