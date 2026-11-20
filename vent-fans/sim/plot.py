"""Plot the ngspice results. Run ./run_all.sh first, then: python3 plot.py"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load(name, n):
    a = np.loadtxt(name)
    return a[:, 0], [a[:, 2 * k + 1] for k in range(n)]

duties = [0.3, 0.4, 0.6, 0.8, 1.0]
labels = {"spec": "Original spec (cap across fans, no inductor)",
          "railcaps": "Caps moved to rail, no inductor",
          "buck": "Proposed: + 100 µH inductor (low-side buck)"}
plt.rcParams.update({"font.size": 9})

# 1. speed proxy (average motor current) vs commanded duty
fig, ax = plt.subplots(figsize=(6, 4))
full = None
for c in labels:
    i = []
    for d in duties:
        t, (g, dr, vb, vs, ifet, imot, *_) = load(f"wave_{c}_{d}.dat", 6)
        i.append(imot.mean())
    full = full or i[-1]
    ax.plot([d * 100 for d in duties], [100 * x / i[-1] for x in i], "o-", label=labels[c])
ax.plot([0, 100], [0, 100], "k:", lw=0.8, label="ideal (speed tracks duty)")
ax.set(xlabel="PWM duty commanded (%)", ylabel="fan motor current, % of full", xlim=(0, 105), ylim=(0, 105),
       title="Does the speed setting actually change fan speed?")
ax.grid(alpha=0.3); ax.legend(fontsize=7, loc="lower right")
fig.tight_layout(); fig.savefig("plot_speed_vs_duty.png", dpi=150)

# 2. waveforms at 60 % duty, three PWM periods
fig, axs = plt.subplots(2, 3, figsize=(11, 5), sharex=True)
for col, c in enumerate(labels):
    n = 8 if c == "buck" else 6
    t, v = load(f"wave_{c}_0.6.dat", n)
    m = (t > 11.9e-3) & (t < 11.9e-3 + 75e-6)
    tt = (t[m] - t[m][0]) * 1e6
    vfan = v[2][m] - v[1][m] if c != "buck" else v[6][m]
    axs[0, col].plot(tt, v[0][m], label="gate", lw=0.8)
    axs[0, col].plot(tt, vfan, label="voltage across fans", lw=1.2)
    axs[0, col].plot(tt, v[3][m], label="Pico VSYS", lw=0.8)
    axs[0, col].set(title=labels[c], ylabel="V", ylim=(-0.5, 6))
    axs[1, col].plot(tt, v[4][m], color="C3", lw=0.8)
    axs[1, col].set(xlabel="µs", ylabel="MOSFET current (A)")
    axs[0, col].grid(alpha=0.3); axs[1, col].grid(alpha=0.3)
axs[0, 0].legend(fontsize=7)
fig.suptitle("60 % duty: the fans see chopped 5 V (left, middle) or smooth DC (right)")
fig.tight_layout(); fig.savefig("plot_waveforms_60pct.png", dpi=150)

# 3. power-up: one-step vs firmware slew limit
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
for ax, (f, title) in zip(axs, [("wave_buck_start.dat", "Jump straight to 60 %"),
                                ("wave_buck_softstart.dat", "ESPHome slew limiter (2 % steps)")]):
    t, (vfan, il, vb, vs) = load(f, 4)
    ax.plot(t * 1e3, vfan, label="fan voltage (V)")
    ax.plot(t * 1e3, il, label="inductor current (A)")
    ax.plot(t * 1e3, vs, label="Pico VSYS (V)", lw=0.8)
    ax.set(title=title, xlabel="ms"); ax.grid(alpha=0.3)
axs[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig("plot_powerup.png", dpi=150)
print("wrote plot_*.png")
