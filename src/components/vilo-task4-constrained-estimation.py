import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.metrics import accuracy_score
from scipy.special import rel_entr
from scipy.ndimage import gaussian_filter1d
import torch.nn.functional as F
import random
import itertools

random.seed(0)
np.random.seed(0)
torch.manual_seed(0)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(0)


# --- IFNeuron class as before (unchanged) ---
class IFNeuron:
    def __init__(
        self,
        pre_synaptic_neurons=None,
        pre_synaptic_weights=None,
        gain=0.1,
        dt=1,
        tau=20.0,
        tau_syn=5.0,
        V_rest=-65.0,
        V_reset=-70.0,
        V_th=-35.0,
        R=10.0,
        refractory_period=5.0,
        ou_theta=0.5,
        ou_mu=0.2,
        ou_sigma=2,
    ):
        self.pre_synaptic_neurons = pre_synaptic_neurons if pre_synaptic_neurons else []
        self.pre_synaptic_weights = pre_synaptic_weights if pre_synaptic_weights else []
        self.gain = gain
        self.dt = dt
        self.tau = tau
        self.tau_syn = tau_syn
        self.V_rest = V_rest
        self.V_reset = V_reset
        self.V_th = V_th
        self.R = R
        self.V = V_rest
        self.refractory_timer = 0.0
        self.refractory_period = refractory_period

        self.a = -1 / tau
        self.exp_ah = np.exp(self.a * dt)
        self.phi_1 = (1 - self.exp_ah) / self.a

        self.ou_theta = ou_theta
        self.ou_mu = ou_mu
        self.ou_sigma = ou_sigma
        self.noise_ou = 0.3

        self.I_syn = 0.0
        self.exp_syn = np.exp(-dt / tau_syn)

        self.spiked = False

        self.noise_ou_slow = 0.0
        self.current_time = 0.0

        self.I_sub_ss = 1.0
        self.tau_sub = 50.0
        self.I_sub = 0.0
        self.exp_sub = np.exp(-dt / self.tau_sub)

    def step(self, inputs):
        self.current_time += self.dt

        if self.refractory_timer > 0:
            self.refractory_timer -= self.dt
            self.V = self.V_reset
            self.spiked = False
            return False, self.V

        dW = np.random.normal(0, np.sqrt(self.dt))
        self.noise_ou += (
            self.ou_theta * (self.ou_mu - self.noise_ou) * self.dt + self.ou_sigma * dW
        )

        slow_theta = 0.1
        slow_sigma = 0.3
        dW_slow = np.random.normal(0, np.sqrt(self.dt))
        self.noise_ou_slow += (
            slow_theta * (self.ou_mu - self.noise_ou_slow) * self.dt
            + slow_sigma * dW_slow
        )

        weighted_spikes = 0.0
        for pre_idx, w in zip(self.pre_synaptic_neurons, self.pre_synaptic_weights):
            weighted_spikes += w * inputs[pre_idx]

        self.I_syn = self.I_syn * self.exp_syn + weighted_spikes

        osc_amplitude = 1.0
        osc_frequency = 0.05
        oscillation = osc_amplitude * np.sin(
            2 * np.pi * osc_frequency * self.current_time
        )

        self.I_sub = self.I_sub * self.exp_sub + (1 - self.exp_sub) * self.I_sub_ss

        I_total = (
            self.gain * self.I_syn
            + self.noise_ou
            + self.noise_ou_slow
            + oscillation
            + self.I_sub
        )

        b_t = (self.R * I_total + self.V_rest) / self.tau

        noise_voltage = np.random.normal(0, 0.5)
        self.V = self.exp_ah * self.V + self.phi_1 * b_t + noise_voltage

        random_threshold = self.V_th + np.random.normal(0, 3.0)
        if self.V >= random_threshold:
            self.spiked = True
            self.V = self.V_reset
            self.refractory_timer = self.refractory_period
            return True, -30
        else:
            self.spiked = False
            return False, self.V


class SpikeRNN(nn.Module):
    def __init__(
        self,
        input_size,
        hidden_size=128,
        num_layers=2,
        dropout=0.2,
        noise_std=0.05,
        cell_type="LSTM",  # 'LSTM' or 'GRU'
    ):
        super().__init__()
        self.cell_type = cell_type.upper()
        self.noise_std = noise_std

        # RNN Cell selection
        if self.cell_type == "LSTM":
            self.rnn = nn.LSTM(
                input_size,
                hidden_size,
                num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )
        elif self.cell_type == "GRU":
            self.rnn = nn.GRU(
                input_size,
                hidden_size,
                num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )
        else:
            raise ValueError(f"Unsupported cell type: {cell_type}")

        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        h, _ = self.rnn(x)  # [B, T, H]

        if self.training and self.noise_std > 0:
            noise = torch.randn_like(h) * self.noise_std
            h = h + noise

        out = self.fc(h)  # [B, T, 1]
        out = self.sigmoid(out).squeeze(-1)  # [B, T]
        return out


def add_weight_noise(model, std=0.01):
    for param in model.parameters():
        if param.requires_grad:
            noise = torch.randn_like(param) * std
            param.data.add_(noise)


def correlation_loss(y_true, y_pred):
    # Ensure both inputs are 2D (batch, time)
    y_true = y_true.unsqueeze(1)
    y_pred = y_pred.unsqueeze(1)

    y_true_centered = y_true - y_true.mean(dim=1, keepdim=True)
    y_pred_centered = y_pred - y_pred.mean(dim=1, keepdim=True)

    numerator = (y_true_centered * y_pred_centered).sum(dim=1)
    denominator = torch.sqrt(
        (y_true_centered**2).sum(dim=1) * (y_pred_centered**2).sum(dim=1) + 1e-8
    )
    corr = numerator / denominator
    return 1 - corr.mean()  # Want to maximize correlation → minimize 1 - corr


def moving_average(x, window=20):
    # x is [batch], or [batch, 1] — make it [batch, 1, time]
    if x.dim() == 1:
        x = x.unsqueeze(1)  # [batch, 1]
    if x.size(1) != 1:
        x = x.unsqueeze(1)  # [batch, 1, time]
    else:
        x = x.unsqueeze(2)  # [batch, 1, time]

    weights = torch.ones(1, 1, window, device=x.device) / window
    smoothed = F.conv1d(x, weights, padding=window // 2)
    return smoothed.squeeze(1)  # → back to [batch, time]


def smoothness_loss(y_pred):
    if y_pred.dim() == 1:
        y_pred = y_pred.unsqueeze(0)  # convert to shape [1, time]
    return ((y_pred[:, 1:] - y_pred[:, :-1]) ** 2).mean()


def temporal_precision_loss(y_true, y_pred, lag=3):
    # y_true, y_pred shape: [batch, time]
    loss = 0
    for d in range(-lag, lag + 1):
        if d < 0:
            shifted_true = y_true[:, :d]
            shifted_pred = y_pred[:, -d:]
        elif d > 0:
            shifted_true = y_true[:, d:]
            shifted_pred = y_pred[:, :-d]
        else:
            shifted_true = y_true
            shifted_pred = y_pred

        loss += 1 - torch.mean(shifted_true * shifted_pred)
    return loss / (2 * lag + 1)


def train_rnn_estimators(
    spike_matrix,
    neurons,
    window_size=10,
    epochs=10,
    batch_size=32,
    noise_std=0.0,
    constrained=False,
    alpha=1.0,
    beta=1.0,
    gamma=0.1,
    delta=0.5,
    epsilon=0.05,
):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    models = []

    num_neurons = len(neurons)
    timesteps = spike_matrix.shape[1]

    for neuron_idx in range(num_neurons):
        # Prepare input sequences X and targets y
        seq_len = window_size  # target length
        neuron = neurons[neuron_idx]
        pre_neurons = neuron.pre_synaptic_neurons
        X = []
        y = []

        for t in range(window_size, timesteps - seq_len):
            seq = []
            for i in pre_neurons:
                seq.append(spike_matrix[i, t - window_size : t])
            X.append(np.array(seq).T)  # shape: [window_size, num_inputs]

            y_seq = spike_matrix[neuron_idx, t : t + seq_len]  # target spike sequence
            y.append(y_seq)

        X = torch.tensor(
            np.array(X), dtype=torch.float32
        )  # shape: [samples, window_size, num_inputs]
        y = torch.tensor(np.array(y), dtype=torch.float32)  # shape: [samples, seq_len]

        print(f"Neuron {neuron_idx}: pre_neurons count = {len(pre_neurons)}")
        print(f"X shape: {X.shape}")

        dataset = TensorDataset(X, y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        model = SpikeRNN(input_size=len(pre_neurons)).to(
            device
        )  # input size = total neurons
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        for epoch in range(epochs):
            model.train()
            for xb, yb in loader:
                xb, yb = xb.to(device), yb.to(device)

                if noise_std > 0 and not constrained:
                    noise = torch.randn_like(xb) * noise_std
                    xb = xb + noise

                preds = model(xb)
                bce_loss = F.binary_cross_entropy(preds, yb)

                if constrained:
                    corr_loss = correlation_loss(preds, yb)
                    y_rate_true = moving_average(yb, window=20)
                    y_rate_pred = moving_average(preds, window=20)
                    kl_loss = F.kl_div(
                        torch.log(torch.clamp(y_rate_pred, min=1e-8)),
                        y_rate_true,
                        reduction="batchmean",
                    )
                    smooth_loss = smoothness_loss(preds)
                    rate_loss = F.mse_loss(y_rate_pred, y_rate_true)

                    total_loss = (
                        bce_loss
                        + alpha * corr_loss
                        + beta * kl_loss
                        + gamma * smooth_loss
                        + delta * rate_loss  # stricter firing rate constraint
                        + epsilon
                        * temporal_precision_loss(
                            yb, preds
                        )  # spike timing precision loss
                    )
                else:
                    total_loss = bce_loss

                optimizer.zero_grad()
                total_loss.backward()
                optimizer.step()

        model.eval()
        with torch.no_grad():
            preds = model(X.to(device)).cpu().numpy()
            binary_preds = (preds > 0.5).astype(int)
            print(
                f"Accuracy for neuron {neuron_idx} ({'constrained' if constrained else 'unconstrained'}):",
                accuracy_score(y.numpy(), binary_preds),
            )
        print(
            f"Trained RNN model for neuron {neuron_idx} ({'constrained' if constrained else 'unconstrained'})"
        )
        models.append(model)

    return models


# End of System constraint stuff.

# --- Simulate network ---
neurons = [
    IFNeuron(pre_synaptic_neurons=[1, 2], pre_synaptic_weights=[1.0, 1.0]),
    IFNeuron(pre_synaptic_neurons=[0, 2], pre_synaptic_weights=[0.7, 0.4]),
    IFNeuron(pre_synaptic_neurons=[0, 1], pre_synaptic_weights=[0.5, 0.5]),
]

timesteps = 2000
voltages = np.zeros((len(neurons), timesteps))
external_drive = np.zeros((timesteps, len(neurons)))
external_drive[20:25, 0] = 1.0  # Pulse input neuron 0

inputs = np.zeros(len(neurons))
spike_matrix = np.zeros((len(neurons), timesteps))

for t in range(timesteps):
    new_spikes = []
    for i, neuron in enumerate(neurons):
        spiked, voltage = neuron.step(inputs)
        voltages[i, t] = voltage
        spike_matrix[i, t] = 1 if spiked else 0
        new_spikes.append(1 if spiked else 0)
    inputs = np.array(new_spikes) + external_drive[t]

# --- 1) Estimate weights per neuron via logistic regression ---


class RNNEmulatedNetwork:
    def __init__(self, models, neurons, window_size=10):
        self.models = models
        self.neurons = neurons
        self.window_size = window_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def run(self, initial_spikes, timesteps):
        num_neurons = len(self.neurons)
        emulated_spikes = np.zeros((num_neurons, timesteps))
        emulated_spikes[:, : self.window_size] = initial_spikes[:, : self.window_size]

        for t in range(self.window_size, timesteps):
            for n, model in enumerate(self.models):
                if model is None:
                    continue
                pre_neurons = self.neurons[
                    n
                ].pre_synaptic_neurons  # get indices of presynaptic neurons
                input_seq = [
                    emulated_spikes[i, t - self.window_size : t]
                    for i in pre_neurons  # only pre-neurons, not all neurons
                ]
                input_seq = np.array(input_seq).T[
                    np.newaxis, :, :
                ]  # shape: (1, window_size, len(pre_neurons))
                input_tensor = torch.tensor(input_seq, dtype=torch.float32).to(
                    self.device
                )
                model.eval()
                with torch.no_grad():
                    output = model(input_tensor)  # shape [1, T] (T=window_size)
                    prob = output[
                        0, -1
                    ].item()  # take last timestep output for current prediction
                emulated_spikes[n, t] = 1 if np.random.rand() < prob else 0

        return emulated_spikes  # <--- Make sure this return statement is here!


def moving_firing_rate(spikes, window=50):
    rates = []
    for neuron_i in range(spikes.shape[0]):
        rate = np.convolve(spikes[neuron_i], np.ones(window), mode="valid") / window
        rates.append(rate)
    return np.array(rates)


# Start if Comparision Metrics for Step 5
def compare_spike_accuracy(original_spikes, emulated_spikes):
    print("\nPer-neuron Spike Accuracy:")
    for i in range(original_spikes.shape[0]):
        acc = accuracy_score(original_spikes[i], emulated_spikes[i])
        print(f"Neuron {i}: Accuracy = {acc:.4f}")


def compare_spike_correlation(original_spikes, emulated_spikes):
    print("\nPer-neuron Spike Correlation:")
    for i in range(original_spikes.shape[0]):
        corr = np.corrcoef(original_spikes[i], emulated_spikes[i])[0, 1]
        print(f"Neuron {i}: Correlation = {corr:.4f}")


def plot_spike_raster(spike_matrix, title="Spike Raster"):
    plt.figure(figsize=(10, 4))
    for neuron_i in range(spike_matrix.shape[0]):
        spike_times = np.where(spike_matrix[neuron_i] == 1)[0]
        plt.vlines(spike_times, neuron_i + 0.5, neuron_i + 1.5)
    plt.xlabel("Time step")
    plt.ylabel("Neuron")
    plt.title(title)
    plt.ylim(0.5, spike_matrix.shape[0] + 0.5)
    plt.show()


def kl_divergence(p, q, eps=1e-10):
    p = np.clip(p, eps, 1)
    q = np.clip(q, eps, 1)
    return np.sum(rel_entr(p, q))


def compare_kl(original_spikes, emulated_spikes):
    print("\nKL Divergence per Neuron:")
    for i in range(original_spikes.shape[0]):
        p = (
            original_spikes[i] / np.sum(original_spikes[i])
            if np.sum(original_spikes[i]) > 0
            else np.ones_like(original_spikes[i]) / len(original_spikes[i])
        )
        q = (
            emulated_spikes[i] / np.sum(emulated_spikes[i])
            if np.sum(emulated_spikes[i]) > 0
            else np.ones_like(emulated_spikes[i]) / len(emulated_spikes[i])
        )
        dkl = kl_divergence(p, q)
        print(f"Neuron {i}: KL Divergence = {dkl:.6f}")


def smooth_spikes(spike_matrix, sigma=1.5):
    return gaussian_filter1d(spike_matrix.astype(float), sigma=sigma, axis=1)


def evaluate_models(models, spike_matrix, neurons, window_size=10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_neurons = len(neurons)
    timesteps = spike_matrix.shape[1]

    accuracies = []
    correlations = []
    kl_divs = []

    for neuron_idx, model in enumerate(models):
        neuron = neurons[neuron_idx]
        pre_neurons = neuron.pre_synaptic_neurons

        X = []
        y_true = []

        # Prepare inputs and targets same way as training
        seq_len = window_size
        for t in range(window_size, timesteps - seq_len):
            seq = []
            for i in pre_neurons:
                seq.append(spike_matrix[i, t - window_size : t])
            X.append(np.array(seq).T)  # [window_size, num_inputs]
            y_seq = spike_matrix[neuron_idx, t : t + seq_len]
            y_true.append(y_seq)

        X = torch.tensor(np.array(X), dtype=torch.float32).to(device)
        y_true = np.array(y_true)

        model.eval()
        with torch.no_grad():
            preds = model(X).cpu().numpy()  # shape [samples, seq_len]

        # Binarize predictions
        binary_preds = (preds > 0.5).astype(int)

        # Flatten for accuracy calculation
        acc = accuracy_score(y_true.flatten(), binary_preds.flatten())
        accuracies.append(acc)

        # Compute per-neuron spike train correlation
        flat_true = y_true.flatten()
        flat_pred = binary_preds.flatten()

        if np.std(flat_true) == 0 or np.std(flat_pred) == 0:
            corr = 0.0  # No variability → no correlation
        else:
            corr = np.corrcoef(flat_true, flat_pred)[0, 1]
        if np.isnan(corr):
            corr = 0.0  # handle constant arrays
        correlations.append(corr)

        # Compute KL divergence between spike rates (histograms) over full sequence
        rate_true = y_true.mean(axis=0) + 1e-8  # avoid zeros
        rate_pred = preds.mean(axis=0) + 1e-8

        kl = np.sum(rate_true * np.log(rate_true / rate_pred))
        kl_divs.append(kl)

    # Return lists or average values
    return accuracies, correlations, kl_divs


# End of Comparison Metrics


# Step 6: Add Noise


window_size = 5
noise_std = 0.2  # tweak noise level here
original_rates = moving_firing_rate(spike_matrix, window=window_size)


rnn_models_clean = train_rnn_estimators(
    spike_matrix, neurons, noise_std=0, constrained=False
)


rnn_models_noisy = train_rnn_estimators(
    spike_matrix, neurons, noise_std=noise_std, constrained=False
)


rnn_models_constraint = train_rnn_estimators(
    spike_matrix,
    neurons,
    constrained=True,
    alpha=2,  # Slightly reduced L1
    beta=0.5,  # Slightly reduced L2
    gamma=2.0,  # Penalize firing more
    delta=0.5,  # Encourage smoothness
    epsilon=0.1,  # Penalize high activity (or co-firing)
)


# Emulate network using RNNs
emulator_clean = RNNEmulatedNetwork(rnn_models_clean, neurons, window_size=20)
rnn_emulated_spikes_clean = emulator_clean.run(spike_matrix, timesteps)

emulator_noisy = RNNEmulatedNetwork(rnn_models_noisy, neurons, window_size=20)
rnn_emulated_spikes_noisy = emulator_noisy.run(spike_matrix, timesteps)

emulator_constrained = RNNEmulatedNetwork(
    rnn_models_constraint, neurons, window_size=20
)
rnn_emulated_spikes_emulator_constrained = emulator_constrained.run(
    spike_matrix, timesteps
)

# Compare firing rates
print("Original firing rate:", spike_matrix.mean())
print("RNN-emulated firing rate(clean):", rnn_emulated_spikes_clean.mean())
print("RNN-emulated firing rate(noisy):", rnn_emulated_spikes_noisy.mean())
print(
    "RNN-emulated firing rate(constrained):",
    rnn_emulated_spikes_emulator_constrained.mean(),
)

print("----------------For clean RNN emulated Spikes--------------------")
# Clean Comparisons
compare_spike_accuracy(spike_matrix, rnn_emulated_spikes_clean)
compare_spike_correlation(
    smooth_spikes(spike_matrix), smooth_spikes(rnn_emulated_spikes_clean)
)
compare_kl(spike_matrix, rnn_emulated_spikes_clean)

print("---------------For noisy RNN emulated Spikes----------------")
compare_spike_accuracy(spike_matrix, rnn_emulated_spikes_noisy)
compare_spike_correlation(
    smooth_spikes(spike_matrix), smooth_spikes(rnn_emulated_spikes_noisy)
)
compare_kl(spike_matrix, rnn_emulated_spikes_noisy)

print("-------------For constrained RNN emulated Spikes--------------------")
compare_spike_accuracy(spike_matrix, rnn_emulated_spikes_emulator_constrained)
compare_spike_correlation(
    smooth_spikes(spike_matrix), smooth_spikes(rnn_emulated_spikes_emulator_constrained)
)
compare_kl(spike_matrix, rnn_emulated_spikes_emulator_constrained)

# Plot
rnn_rates_clean = moving_firing_rate(rnn_emulated_spikes_clean, window=50)
rnn_rates_noisy = moving_firing_rate(rnn_emulated_spikes_noisy, window=50)
rnn_rates_constrained = moving_firing_rate(
    rnn_emulated_spikes_emulator_constrained, window=50
)

plt.figure(figsize=(12, 5))
plt.plot(original_rates[0], label="Original neuron 0")
plt.plot(rnn_rates_clean[0], label="RNN emulated neuron 0")
plt.legend()
plt.title("Firing rates (Original vs Clean RNN emulation)")
plt.show()

plt.figure(figsize=(12, 5))
plt.plot(original_rates[0], label="Original neuron 0")
plt.plot(rnn_rates_noisy[0], label="RNN emulated neuron 0")
plt.legend()
plt.title("Firing rates (Original vs Noisy RNN emulation)")
plt.show()

plt.figure(figsize=(12, 5))
plt.plot(original_rates[0], label="Original neuron 0")
plt.plot(rnn_rates_constrained[0], label="RNN emulated neuron 0")
plt.legend()
plt.title("Firing rates (Original vs Constrained RNN emulation)")
plt.show()
