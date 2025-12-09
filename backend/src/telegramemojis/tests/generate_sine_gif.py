import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Parameters for the animation
fig, ax = plt.subplots(figsize=(6, 4))
x_data = np.linspace(0, 2 * np.pi, 100)
line, = ax.plot(x_data, np.sin(x_data), color='blue')

ax.set_xlim(0, 2 * np.pi)
ax.set_ylim(-1.5, 1.5)
ax.set_title('Evolving Sine Wave')
ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')

def update(frame):
    # Update the sine wave with a phase shift
    line.set_ydata(np.sin(x_data + frame * 0.1))
    return line,

# Create the animation
ani = FuncAnimation(
    fig,
    update,
    frames=range(50),  # Number of frames
    blit=True,
    interval=100,      # Delay between frames in ms
    repeat=True        # Loop the animation
)

# Save the animation as a GIF
gif_path = "sine_animation.gif"
ani.save(gif_path, writer='pillow', fps=10)

plt.close(fig)
print(f"Generated GIF: {gif_path}")
