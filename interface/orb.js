/**
 * F.R.I.D.A.Y 2.0 // Holographic Arc-Reactor & Quantum Plasma Visualizer
 * Clean, subtle, elegant futuristic glow and smooth harmonic waveforms.
 * Ultra-lightweight with zero DOM reflow.
 */

class FridayOrb {
  constructor(canvasId, freqCanvasId) {
    this.canvas = document.getElementById(canvasId);
    this.freqCanvas = document.getElementById(freqCanvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d', { alpha: true });
    this.freqCtx = this.freqCanvas ? this.freqCanvas.getContext('2d', { alpha: true }) : null;

    // Dimensions
    this.width = 340;
    this.height = 190;
    this.cx = 170;
    this.cy = 95;
    this.freqWidth = 340;
    this.freqHeight = 32;

    // States: 'idle', 'listening', 'thinking', 'speaking'
    this.state = 'idle';
    this.isPaused = false;
    this.activeTask = '';

    // Theme colors
    this.themeColors = {
      primary: '#00f0ff',
      secondary: '#8a2be2',
      glow: 'rgba(0, 240, 255, 0.35)'
    };

    // Smooth particle swarm
    this.particles = [];
    this.initParticles(24);

    // Wave parameters (Smooth & subtle)
    this.phase = 0;
    this.speed = 0.018;
    this.intensity = 1.0;
    this.targetIntensity = 1.0;
    this.targetSpeed = 0.018;

    // Ring angles
    this.ringAngle1 = 0;
    this.ringAngle2 = 0;

    // Smooth audio frequency bars
    this.freqBars = Array.from({ length: 24 }, () => ({
      height: 4,
      target: 4
    }));

    // Capped at 30 FPS to maintain ~0% CPU
    this.lastFrameTime = 0;
    this.fpsInterval = 1000 / 30;

    this.setupDPI();
    window.addEventListener('resize', () => this.setupDPI());

    this.render = this.render.bind(this);
    requestAnimationFrame(this.render);
  }

  setTheme(themeName) {
    if (themeName === 'gold') {
      this.themeColors = { primary: '#ffd700', secondary: '#ff3b30', glow: 'rgba(255, 215, 0, 0.35)' };
    } else if (themeName === 'purple') {
      this.themeColors = { primary: '#c084fc', secondary: '#3b82f6', glow: 'rgba(192, 132, 252, 0.35)' };
    } else if (themeName === 'green') {
      this.themeColors = { primary: '#00ff9d', secondary: '#00b4d8', glow: 'rgba(0, 255, 157, 0.35)' };
    } else if (themeName === 'dark-sky-blue') {
      this.themeColors = { primary: '#38bdf8', secondary: '#0284c7', glow: 'rgba(56, 189, 248, 0.35)' };
    } else {
      this.themeColors = { primary: '#00f0ff', secondary: '#8a2be2', glow: 'rgba(0, 240, 255, 0.35)' };
    }
  }

  setupDPI() {
    if (!this.canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const rect = this.canvas.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      this.width = rect.width;
      this.height = rect.height;
      this.cx = this.width / 2;
      this.cy = this.height / 2;
      this.canvas.width = Math.round(this.width * dpr);
      this.canvas.height = Math.round(this.height * dpr);
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    if (this.freqCanvas) {
      const fRect = this.freqCanvas.getBoundingClientRect();
      if (fRect.width > 0 && fRect.height > 0) {
        this.freqWidth = fRect.width;
        this.freqHeight = fRect.height;
        this.freqCanvas.width = Math.round(this.freqWidth * dpr);
        this.freqCanvas.height = Math.round(this.freqHeight * dpr);
        this.freqCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    }
  }

  pause() {
    this.isPaused = true;
  }

  resume() {
    if (this.isPaused) {
      this.isPaused = false;
      this.setupDPI();
      requestAnimationFrame(this.render);
    }
  }

  initParticles(count) {
    this.particles = [];
    for (let i = 0; i < count; i++) {
      this.particles.push({
        radius: 22 + Math.random() * 40,
        angle: Math.random() * Math.PI * 2,
        speed: (Math.random() * 0.016 + 0.005) * (Math.random() > 0.5 ? 1 : -1),
        size: Math.random() * 1.8 + 0.8,
        alpha: Math.random() * 0.5 + 0.25
      });
    }
  }

  setState(newState, taskName = '') {
    this.state = newState;
    this.activeTask = taskName || '';

    switch (newState) {
      case 'idle':
        this.targetSpeed = 0.015;
        this.targetIntensity = 1.0;
        break;
      case 'listening':
        this.targetSpeed = 0.03;
        this.targetIntensity = 1.6;
        break;
      case 'thinking':
        this.targetSpeed = 0.035;
        this.targetIntensity = 1.8;
        break;
      case 'speaking':
        this.targetSpeed = 0.032;
        this.targetIntensity = 2.0;
        break;
    }
  }

  // =========================================================================
  // RENDER LOOP
  // =========================================================================
  render(timestamp) {
    if (this.isPaused) return;

    const elapsed = timestamp - this.lastFrameTime;
    if (elapsed < this.fpsInterval) {
      requestAnimationFrame(this.render);
      return;
    }
    this.lastFrameTime = timestamp - (elapsed % this.fpsInterval);

    // Smooth speed & intensity interpolation
    this.speed += (this.targetSpeed - this.speed) * 0.1;
    this.intensity += (this.targetIntensity - this.intensity) * 0.1;
    this.phase += this.speed;

    // Calm, graceful ring rotation
    this.ringAngle1 += (this.state === 'thinking' ? 0.02 : 0.006);
    this.ringAngle2 -= (this.state === 'thinking' ? 0.015 : 0.004);

    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Soft Ambient Radial Glow
    this.drawAmbientGlow(ctx);

    // 2. Subtle Circular Reticle Rings
    this.drawHudRings(ctx);

    // 3. Gentle Floating Particles
    this.drawParticles(ctx);

    // 4. Smooth Harmonic Fluid Waves
    this.drawFluidCore(ctx);

    // 5. Breathing Core Nucleus
    this.drawNucleus(ctx);

    // 6. Smooth Audio Frequency Bars
    if (this.freqCtx) {
      this.drawFrequencyBars(this.freqCtx);
    }

    requestAnimationFrame(this.render);
  }

  // =========================================================================
  // 1. SOFT AMBIENT GLOW
  // =========================================================================
  drawAmbientGlow(ctx) {
    const isSpeaking = this.state === 'speaking';
    const isThinking = this.state === 'thinking';
    const pulse = Math.sin(this.phase * 2) * 0.12 + 0.88;
    const baseRadius = (isSpeaking ? 58 : isThinking ? 52 : 44) * this.intensity * 0.65;

    const gradient = ctx.createRadialGradient(
      this.cx, this.cy, 4,
      this.cx, this.cy, Math.max(16, baseRadius * pulse)
    );

    const pri = this.themeColors.primary;
    if (isSpeaking) {
      gradient.addColorStop(0, 'rgba(0, 240, 255, 0.35)');
      gradient.addColorStop(0.6, 'rgba(0, 180, 255, 0.12)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (isThinking) {
      gradient.addColorStop(0, 'rgba(192, 132, 252, 0.35)');
      gradient.addColorStop(0.6, 'rgba(138, 43, 226, 0.12)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else if (this.state === 'listening') {
      gradient.addColorStop(0, 'rgba(0, 255, 157, 0.35)');
      gradient.addColorStop(0.6, 'rgba(0, 240, 255, 0.1)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    } else {
      gradient.addColorStop(0, this.themeColors.glow);
      gradient.addColorStop(0.6, 'rgba(138, 43, 226, 0.08)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
    }

    ctx.save();
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(this.cx, this.cy, baseRadius * pulse, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // =========================================================================
  // 2. SUBTLE CIRCULAR HUD RINGS
  // =========================================================================
  drawHudRings(ctx) {
    ctx.save();
    const pri = this.themeColors.primary;
    const isSpeaking = this.state === 'speaking';
    const isThinking = this.state === 'thinking';

    // Ring 1: Thin outer guide
    ctx.strokeStyle = isThinking ? this.themeColors.secondary : pri;
    ctx.lineWidth = 0.8;
    ctx.globalAlpha = isSpeaking ? 0.45 : (isThinking ? 0.4 : 0.2);
    ctx.beginPath();
    ctx.arc(this.cx, this.cy, 62, this.ringAngle1, this.ringAngle1 + Math.PI * 1.4);
    ctx.stroke();

    // Ring 2: Subtle counter ring
    ctx.strokeStyle = pri;
    ctx.lineWidth = 0.8;
    ctx.globalAlpha = isSpeaking ? 0.35 : 0.15;
    ctx.beginPath();
    ctx.arc(this.cx, this.cy, 50, this.ringAngle2, this.ringAngle2 + Math.PI * 0.9);
    ctx.stroke();

    ctx.restore();
  }

  // =========================================================================
  // 3. GENTLE PARTICLES
  // =========================================================================
  drawParticles(ctx) {
    ctx.save();
    const pri = this.themeColors.primary;
    ctx.fillStyle = pri;
    const isSpeaking = this.state === 'speaking';

    for (let p of this.particles) {
      p.angle += p.speed * (isSpeaking ? 1.4 : 1.0);
      const dist = p.radius + Math.sin(this.phase * 2 + p.angle) * (isSpeaking ? 3 : 2);
      const x = this.cx + Math.cos(p.angle) * dist;
      const y = this.cy + Math.sin(p.angle) * dist;

      ctx.beginPath();
      ctx.arc(x, y, p.size, 0, Math.PI * 2);
      ctx.globalAlpha = Math.min(1.0, p.alpha * (isSpeaking ? 0.65 : 0.4));
      ctx.fill();
    }
    ctx.restore();
  }

  // =========================================================================
  // 4. SMOOTH HARMONIC FLUID CORE WAVES
  // =========================================================================
  drawFluidCore(ctx) {
    ctx.save();
    const waves = 3;
    const points = 24;
    const pri = this.themeColors.primary;
    const isSpeaking = this.state === 'speaking';

    for (let w = 0; w < waves; w++) {
      ctx.beginPath();
      const wavePhase = this.phase + (w * Math.PI) / 2.5;
      const baseR = 22 + w * 4;

      for (let i = 0; i <= points; i++) {
        const theta = (i / points) * Math.PI * 2;
        // Calm, smooth sine oscillations (no violent spikes)
        const harm1 = Math.sin(theta * 3 + wavePhase * 1.6) * (isSpeaking ? 3.6 : 2.0 * this.intensity);
        const harm2 = Math.cos(theta * 4 - wavePhase * 1.8) * (isSpeaking ? 2.2 : 1.2 * this.intensity);
        const r = Math.max(10, baseR + harm1 + harm2);

        const x = this.cx + Math.cos(theta) * r;
        const y = this.cy + Math.sin(theta) * r;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.closePath();

      ctx.strokeStyle = this.state === 'thinking' ? this.themeColors.secondary : pri;
      ctx.globalAlpha = 0.35 + w * 0.18 + (isSpeaking ? 0.15 : 0);
      ctx.lineWidth = isSpeaking ? 1.5 : 1.2;
      ctx.stroke();
    }
    ctx.restore();
  }

  // =========================================================================
  // 5. BREATHING CORE NUCLEUS
  // =========================================================================
  drawNucleus(ctx) {
    ctx.save();
    const isSpeaking = this.state === 'speaking';
    const pulse = Math.sin(this.phase * 3) * (isSpeaking ? 0.15 : 0.08) + 1;
    const r = (isSpeaking ? 10 : 8) * pulse;

    const grad = ctx.createRadialGradient(
      this.cx, this.cy, 0,
      this.cx, this.cy, r
    );
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.5, this.themeColors.primary);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(this.cx, this.cy, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // =========================================================================
  // 6. SMOOTH AUDIO FREQUENCY BARS
  // =========================================================================
  drawFrequencyBars(ctx) {
    const w = this.freqWidth || 340;
    const h = this.freqHeight || 32;
    ctx.clearRect(0, 0, w, h);

    const count = this.freqBars.length;
    const barW = Math.max(3, (w - (count * 3)) / count);
    const pri = this.themeColors.primary;
    const isSpeaking = this.state === 'speaking';

    ctx.save();
    for (let i = 0; i < count; i++) {
      const b = this.freqBars[i];
      let maxH = 4;

      if (isSpeaking) {
        // Smooth gentle vocal bounce
        maxH = Math.sin(this.phase * 3.2 + i * 0.38) * 7 + 10;
      } else if (this.state === 'listening') {
        maxH = Math.sin(this.phase * 3 + i * 0.45) * 6 + 8;
      } else if (this.state === 'thinking') {
        maxH = Math.sin(this.phase * 3.8 + i * 0.5) * 5 + 7;
      } else {
        maxH = Math.sin(this.phase * 1.2 + i * 0.2) * 2.5 + 4.5;
      }

      b.target = Math.max(3, Math.min(h - 4, maxH));
      b.height += (b.target - b.height) * 0.2;

      const x = i * (barW + 3) + 4;
      const y = (h - b.height) / 2;

      ctx.fillStyle = pri;
      ctx.globalAlpha = 0.35 + (b.height / h) * 0.55;

      ctx.beginPath();
      ctx.roundRect(x, y, barW, b.height, [2]);
      ctx.fill();
    }
    ctx.restore();
  }
}

window.FridayOrb = FridayOrb;
