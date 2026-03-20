import matplotlib.pyplot as plt
import numpy as np

# Parameters
S0 = 1.20  # Initial exchange rate (e.g., USD/EUR)
K = 1.25  # Strike price
T = 1.0  # Time to expiration (in years)
r_d = 0.03  # Domestic risk-free rate (e.g., USD rate)
r_f = 0.01  # Foreign risk-free rate (e.g., EUR rate)
sigma = 0.15  # Volatility of the exchange rate
N_paths = 10000  # Number of Monte Carlo paths
N_steps = 252  # Number of time steps (e.g., daily steps for 1 year)
dt = T / N_steps  # Time step size

# Set random seed for reproducibility (optional)
np.random.seed(41)


# Simulate exchange rate paths
def simulate_fx_paths(S0, r_d, r_f, sigma, T, N_steps, N_paths):
    # Preallocate array for final values S(T)
    S_T = np.zeros(N_paths)

    # Time step
    dt = T / N_steps

    # Simulate paths (using vectorized operations for efficiency)
    for i in range(N_paths):
        # Generate random increments for one path
        Z = np.random.normal(0, 1, N_steps)
        # Cumulative log-returns
        log_returns = (r_d - r_f - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
        # Exponentiate to get S(T)
        S_T[i] = S0 * np.exp(np.sum(log_returns))

    return S_T


# Price the option
def price_fx_call_option(S0, K, T, r_d, r_f, sigma, N_paths, N_steps):
    # Simulate exchange rates at maturity
    S_T = simulate_fx_paths(S0, r_d, r_f, sigma, T, N_steps, N_paths)

    # Calculate payoffs for a call option
    payoffs = np.maximum(S_T - K, 0)

    # Discounted average payoff (option price)
    option_price = np.exp(-r_d * T) * np.mean(payoffs)

    # Standard error for confidence
    std_error = np.std(payoffs) / np.sqrt(N_paths)

    return option_price, std_error


# Run the pricing
option_price, std_error = price_fx_call_option(S0, K, T, r_d, r_f, sigma, N_paths, N_steps)
print(f"Monte Carlo FX Call Option Price: {option_price:.4f}")
print(f"Standard Error: {std_error:.4f}")


# Optional: Simulate and plot a few sample paths for visualization
def plot_sample_paths(S0, r_d, r_f, sigma, T, N_steps, N_samples=5):
    t = np.linspace(0, T, N_steps + 1)
    paths = np.zeros((N_samples, N_steps + 1))
    paths[:, 0] = S0

    for i in range(N_samples):
        Z = np.random.normal(0, 1, N_steps)
        log_returns = (r_d - r_f - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
        paths[i, 1:] = S0 * np.exp(np.cumsum(log_returns))

    plt.figure(figsize=(10, 6))
    for i in range(N_samples):
        plt.plot(t, paths[i], label=f"Path {i+1}")
    plt.axhline(y=K, color="r", linestyle="--", label=f"Strike = {K}")
    plt.title("Sample FX Rate Paths (Geometric Brownian Motion)")
    plt.xlabel("Time (Years)")
    plt.ylabel("Exchange Rate")
    plt.legend()
    plt.grid(True)
    plt.show()


# Plot sample paths
plot_sample_paths(S0, r_d, r_f, sigma, T, N_steps)
