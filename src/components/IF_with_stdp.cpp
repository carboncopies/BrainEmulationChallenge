#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <map>
#include <string>
#include <chrono>
#include <stdexcept>

// Simulation parameters
const double dt = 1.0;  // ms
// const double T = 950;
const double T = 4000;
const size_t n_steps = static_cast<size_t>(T / dt);

// Configuration flags
const bool burst_drive = false; // default: false
const bool compact_burst_driver = true; // default: true
const int compact_driver_spikes = 10;
const int long_driver_spikes = 200;

const bool Cm_option = true; // default: true
const bool use_exponential_Euler = true; // default: true

const bool quantal_trigger = false; // input just enough to trigger a spike

bool include_inhibition = true; // Otherwise, no input from IntIn
const bool long_regular_input = true; // Otherwise a single input from PyrIn and one from IntIn
const bool simulate_recurrent_inhibition = true; // but from only a single interneuron!

const bool with_explicit_voltage_gating = true; // default: true
const bool with_adp = true; // Applies to pyramidal neurons
const bool with_stdp = true; // Applies to AMPA receptors onto pyramidal neurons
const bool clipping_AHP_and_ADP = true; // default: true
const bool with_dynamic_threshold_floor = true; // default: true
const bool with_fatigue_threshold = true; // default: false

bool classical_IF = false; // default: false

// Spike reset options
enum class SpikeOption { RESET_ONSET, RESET_AFTER, NO_RESET };
SpikeOption spike_option = SpikeOption::NO_RESET; // 'reset-onset', 'reset-after', 'no-reset'

// Helper function to compute normalization factor
double compute_normalization(double tau_rise, double tau_decay) {
    if (tau_rise == tau_decay) {
        throw std::invalid_argument("tau_rise must be different from tau_decay for normalization.");
    }
    double t_peak = (tau_rise * tau_decay) / (tau_decay - tau_rise) * log(tau_decay / tau_rise);
    double norm = exp(-t_peak / tau_decay) - exp(-t_peak / tau_rise);
    return norm;
}

// Function to compute normalized synaptic conductance
double g_norm(double t, const std::vector<double>& spike_times, double tau_rise, double tau_decay, 
              double norm, double onset_delay, double spike_dt_delta = 1000, double history_delta = 0.001) {
    t -= onset_delay;
    history_delta *= norm;
    double gnorm = 0;
    
    // Iterate in reverse to process most recent spikes first
    for (auto it = spike_times.rbegin(); it != spike_times.rend(); ++it) {
        double spike_dt = t - *it;
        if (spike_dt >= 0) {
            double g_norm_contribution = exp(-spike_dt / tau_decay) - exp(-spike_dt / tau_rise);
            if (spike_dt > spike_dt_delta && g_norm_contribution < history_delta) {
                return gnorm / norm;
            }
            gnorm += g_norm_contribution;
        }
    }
    return gnorm / norm;
}

// Forward declaration of Neuron class
class IF_neuron;

class Netmorph_Syn {
public:
    std::string n_from;
    std::string n_to;
    std::string receptor;
    int quantity;
    bool voltage_gated;
    double g_rec_peak; // nS (nano Siemens)
    double tau_rise;
    double tau_decay;
    double hilloc_distance; // um
    double velocity; // m/s
    double synaptic_delay; // ms
    double onset_delay;
    
    Netmorph_Syn(const std::string& from, const std::string& to, const std::string& rec, 
                 double PSD_area_um2, double g_rec, double trise, double tdecay, 
                 double hilloc_dist, double vel, double syn_delay, bool vgated)
        : n_from(from), n_to(to), receptor(rec), voltage_gated(vgated), 
          tau_rise(trise), tau_decay(tdecay), hilloc_distance(hilloc_dist), 
          velocity(vel), synaptic_delay(syn_delay) {
        
        quantity = static_cast<int>(PSD_area_um2 / 0.0086);
        g_rec_peak = g_rec;
        if (voltage_gated) {
            // Adjusted to achieve desired g_peak with voltage-gated Mg2++ block modulation
            g_rec_peak *= 5.0;
        }
        onset_delay = synaptic_delay + ((hilloc_distance*1e-6)/velocity) * 1000; // convert to ms
    }
};

class PreSyn {
public:
    std::string receptor;
    IF_neuron* source;
    double tau_rise;
    double tau_decay;
    double E; // mV
    double g_peak; // Also considered g_peak_max (weight=1.0)
    double weight;
    double onset_delay; // ms
    bool voltage_gated;
    double g; // current conductance
    
    // STDP parameters
    std::string STDP_type; // 'Hebbian', 'Anti-Hebbian', or 'None'
    double A_pos;
    double A_neg;
    double tau_pos;
    double tau_neg;
    
    double norm; // normalization factor
    std::vector<double> g_k; // conductance history
    
    PreSyn(const std::string& rec, IF_neuron* src, double trise, double tdecay, 
           double e, double g_p, double w, double delay, const std::string& stdp_type,
           double a_pos, double a_neg, double t_pos, double t_neg, bool vgated)
        : receptor(rec), source(src), tau_rise(trise), tau_decay(tdecay), E(e), 
          g_peak(g_p), weight(w), onset_delay(delay), voltage_gated(vgated), g(0.0),
          STDP_type(stdp_type), A_pos(a_pos), A_neg(a_neg), tau_pos(t_pos), tau_neg(t_neg) {
        
        norm = compute_normalization(tau_rise, tau_decay);
        std::cout << "g_peak_" << receptor << ": " << g_peak << std::endl;
        std::cout << "norm_" << receptor << ": " << norm << std::endl;
        
        g_k.resize(n_steps, 0.0);
    }
    
    // Effect of voltage-gated Mg2+ block.
    double B_NMDA(double V, double Mg = 1.0) {
        double gamma = 0.33;  // per mM
        double beta = 0.062;  // per mV
        return 1.0 / (1.0 + gamma * Mg * exp(-beta * V));
    }
    
    void update(size_t i, double t, double Vm) {
        auto& syn_times = source->t_postspikes;
        if (voltage_gated) {
            g = std::min(g_peak, B_NMDA(Vm) * weight * g_peak * 
                         g_norm(t, syn_times, tau_rise, tau_decay, norm, onset_delay));
        } else {
            g = std::min(g_peak, weight * g_peak * 
                         g_norm(t, syn_times, tau_rise, tau_decay, norm, onset_delay));
        }
        g_k[i] = g;
    }
    
    double stdp_update(double t) {
        if (source->t_postspikes.empty()) return 0;
        double t_pre = source->t_postspikes.back();
        
        if (STDP_type == "None") return 0;
        
        double dt_spikes;
        if (STDP_type == "Anti-Hebbian") {
            dt_spikes = t_pre - t;
        } else {
            dt_spikes = t - t_pre;
        }
        
        double dw;
        if (dt_spikes > 0) {
            dw = A_pos * exp(-dt_spikes / tau_pos);
        } else {
            dw = -A_neg * exp(dt_spikes / tau_neg);
        }
        
        weight += dw;
        weight = std::max(0.0, std::min(1.0, weight));
        return dw;
    }
};

class IF_neuron {
public:
    std::string id;
    std::vector<double> force_spikes;
    std::vector<PreSyn*> presyn;
    
    // Neuron parameters
    double V_rest = -70;  // mV
    double V_th = -50;    // spike threshold mV (base value)
    double V_reset = -55; // mV after spike
    double R_m = 100.0/1000; // in GΩ, 100-300 MΩ pyramidal
    double C_m = 100; // 100-300 pF pyramidal
    double tau_m; // ms
    double g_L; // nS
    double refractory_period = 2;  // ms
    double V_spike_depol = 30; // mV - voltage at which to depict spike
    bool reset_done = true; // Only used for 'reset-after'
    
    // Fast after-hyperpolarization
    double E_AHP = -90; // mV reversal potential
    double tau_rise_fAHP = 2.5, tau_decay_fAHP = 30; // ms
    double g_peak_fAHP = 3.0;  // nS
    double g_peak_fAHP_max = 5; // nS
    double Kd_fAHP = 1.5; // nS half-activation constant
    double g_fAHP = 0.0;
    
    // Slow after-hyperpolarization
    double tau_rise_sAHP = 30, tau_decay_sAHP = 300; // ms
    double g_peak_sAHP = 1.0; // nS
    double g_peak_sAHP_max = 2.0; // nS
    double Kd_sAHP = 0.3; // nS half-activation constant
    double g_sAHP = 0.0;
    
    std::string AHP_saturation_model; // 'clip' or 'sigmoidal'
    
    // Hard-cap fatigue threshold
    double fatigue = 0.0;
    double fatigue_threshold = 300;
    double tau_fatigue_recovery = 1000; // ms
    
    // After-depolarization
    double E_ADP = -20; // mV reversal potential
    double tau_rise_ADP = 20, tau_decay_ADP = 200; // ms
    double g_peak_ADP; // nS
    double ADP_saturation_multiplier = 2.0;
    double g_peak_ADP_max;
    double tau_recovery_ADP = 300; // ms
    double ADP_depletion = 0.3;
    double a_ADP = 1.0;
    double g_ADP = 0.0;
    
    std::string ADP_saturation_model; // 'clip' or 'resource'
    
    // Parameters for adaptive threshold modeling
    double h_spike = 1.0;
    double dh_spike = 0.2;
    double tau_h = 50; // ms
    double dV_th = 10; // mV
    
    double V_th_floor; // Dynamic threshold floor
    double delta_floor_per_spike = 1.0; // mV
    double tau_floor_decay = 500; // ms
    
    // State variables
    double Vm;
    double last_spike_idx = -INFINITY;
    double t_last_spike = -1000;
    std::vector<double> t_postspikes;
    
    // Recordings
    struct {
        std::vector<double> fAHP;
        std::vector<double> sAHP;
        std::vector<double> ADP;
        std::vector<double> Vm;
        std::vector<double> dV;
        std::vector<double> V_th_adaptive;
    } samples;
    
    std::vector<bool> spike_train;
    
    // Normalization factors
    double norm_fAHP;
    double norm_sAHP;
    double norm_ADP;
    
    IF_neuron(const std::string& neuron_id, const std::vector<double>& f_spikes, 
              const std::vector<PreSyn*>& p_syn)
        : id(neuron_id), force_spikes(f_spikes), presyn(p_syn) {
        
        tau_m = R_m * C_m;
        std::cout << "tau_m = " << tau_m << " ms" << std::endl;
        g_L = 1.0 / R_m;
        std::cout << "g_L = " << g_L << " nS" << std::endl;
        
        if (clipping_AHP_and_ADP) {
            AHP_saturation_model = "clip";
        } else {
            AHP_saturation_model = "sigmoidal";
        }
        
        if (with_adp) {
            g_peak_ADP = 0.3;
        } else {
            g_peak_ADP = 0.0;
        }
        g_peak_ADP_max = g_peak_ADP * ADP_saturation_multiplier;
        
        if (clipping_AHP_and_ADP) {
            ADP_saturation_model = "clip";
        } else {
            ADP_saturation_model = "resource";
        }
        
        V_th_floor = V_th;
        Vm = V_rest;
        
        // Initialize recording vectors
        samples.fAHP.resize(n_steps, 0.0);
        samples.sAHP.resize(n_steps, 0.0);
        samples.ADP.resize(n_steps, 0.0);
        samples.Vm.resize(n_steps, 0.0);
        samples.dV.resize(n_steps, 0.0);
        samples.V_th_adaptive.resize(n_steps, 0.0);
        spike_train.resize(n_steps, false);
        
        // Pre-calculate normalizations
        norm_fAHP = compute_normalization(tau_rise_fAHP, tau_decay_fAHP);
        norm_sAHP = compute_normalization(tau_rise_sAHP, tau_decay_sAHP);
        norm_ADP = compute_normalization(tau_rise_ADP, tau_decay_ADP);
        
        std::cout << "norm_fAHP: " << norm_fAHP << std::endl;
        std::cout << "norm_sAHP: " << norm_sAHP << std::endl;
        std::cout << "norm_ADP: " << norm_ADP << std::endl;
    }
    
    void set_presyn(const std::vector<PreSyn*>& p_syn) {
        presyn = p_syn;
    }
    
    void spike(size_t i, double t) {
        // Spike logging
        spike_train[i] = true;
        last_spike_idx = static_cast<double>(i);
        t_last_spike = t;
        t_postspikes.push_back(t_last_spike);
        
        // Membrane potential reset
        if (classical_IF) {
            Vm = V_reset;
        } else {
            if (spike_option == SpikeOption::NO_RESET) {
                V_reset = Vm; // Remember value before AP
            }
            Vm = V_spike_depol;
        }
        reset_done = false;
        
        // Threshold effects
        // a. nonlinear hard-cap
        if (with_fatigue_threshold) {
            fatigue += 1;
        }
        // b. Adaptive threshold models sodium channel inactivation
        h_spike -= dh_spike;
        // c. Dynamic threshold floor
        if (with_dynamic_threshold_floor) {
            V_th_floor += delta_floor_per_spike;
        }
        
        // ADP saturation
        if (ADP_saturation_model != "clip") {
            a_ADP -= ADP_depletion;
        }
        
        // STDP
        if (with_stdp) {
            for (auto p : presyn) {
                p->stdp_update(t);
            }
        }
    }
    
    void check_spiking(size_t i, double t, double V_th_adaptive) {
        if (!force_spikes.empty()) {
            if (t >= force_spikes[0]) {
                spike(i, force_spikes[0]);
                force_spikes.erase(force_spikes.begin());
                return;
            }
        }
        
        if (with_fatigue_threshold && (fatigue > fatigue_threshold)) {
            return;
        }
        
        if (Vm >= V_th_adaptive) {
            spike(i, t);
        }
    }
    
    void update_conductances(size_t i, double t) {
        // Update PSP conductances
        for (auto p : presyn) {
            p->update(i, t, Vm);
        }
        
        // Update fAHP, sAHP, ADP conductances
        double g_fAHP_linear = g_peak_fAHP * g_norm(t, t_postspikes, tau_rise_fAHP, tau_decay_fAHP, norm_fAHP, 0);
        if (AHP_saturation_model == "clip") {
            g_fAHP = std::min(g_fAHP_linear, g_peak_fAHP_max);
        } else {
            g_fAHP = g_peak_fAHP_max * (g_fAHP_linear / (g_fAHP_linear + Kd_fAHP));
        }
        
        double g_sAHP_linear = g_peak_sAHP * g_norm(t, t_postspikes, tau_rise_sAHP, tau_decay_sAHP, norm_sAHP, 0);
        if (AHP_saturation_model == "clip") {
            g_sAHP = std::min(g_sAHP_linear, g_peak_sAHP_max);
        } else {
            g_sAHP = g_peak_sAHP_max * (g_sAHP_linear / (g_sAHP_linear + Kd_sAHP));
        }
        
        double g_ADP_linear = g_peak_ADP * g_norm(t, t_postspikes, tau_rise_ADP, tau_decay_ADP, norm_ADP, 0);
        if (ADP_saturation_model == "clip") {
            g_ADP = std::min(g_ADP_linear, g_peak_ADP_max);
        } else {
            a_ADP = a_ADP + (1 - a_ADP) * dt / tau_recovery_ADP;
            a_ADP = std::max(0.0, std::min(1.0, a_ADP));
            g_ADP = a_ADP * g_ADP_linear;
        }
    }
    
    double update_currents(size_t i) {
        double I = g_fAHP * (Vm - E_AHP) +
                  g_sAHP * (Vm - E_AHP) +
                  g_ADP * (Vm - E_ADP);
        
        for (auto p : presyn) {
            I += p->g * (Vm - p->E);
        }
        
        return I;
    }
    
    double update_membrane_potential_forward_Euler(double I) {
        double dV = (-(Vm - V_rest) + R_m * (-I)) * dt / tau_m;
        samples.dV[i] = dV;
        Vm += dV;
        return dV;
    }
    
    void update_membrane_potential_exponential_Euler_Rm(size_t i) {
        double tau_eff = tau_m / (1 + R_m * (g_fAHP + g_sAHP + g_ADP));
        double sum_g = 0.0;
        double sum_gE = 0.0;
        
        for (auto p : presyn) {
            sum_g += p->g;
            sum_gE += p->g * p->E;
        }
        
        double V_inf = (g_fAHP * E_AHP + g_sAHP * E_AHP + g_ADP * E_ADP + sum_gE + (1 / R_m) * V_rest) /
                      (g_fAHP + g_sAHP + g_ADP + sum_g + (1 / R_m));
        
        Vm = V_inf + (Vm - V_inf) * exp(-dt / tau_eff);
    }
    
    void update_membrane_potential_exponential_Euler_Cm(size_t i) {
        double sum_g = 0.0;
        double sum_gE = 0.0;
        
        for (auto p : presyn) {
            sum_g += p->g;
            sum_gE += p->g * p->E;
        }
        
        double g_total = g_L + g_fAHP + g_sAHP + g_ADP + sum_g;
        double E_total = (g_L * V_rest +
                         g_fAHP * E_AHP +
                         g_sAHP * E_AHP +
                         g_ADP * E_ADP +
                         sum_gE) / g_total;
        
        double tau_eff = C_m / g_total;
        Vm = E_total + (Vm - E_total) * exp(-dt / tau_eff);
    }
    
    double update_adaptive_threshold(size_t i) {
        h_spike += dt * (1 - h_spike) / tau_h;
        if (with_dynamic_threshold_floor) {
            V_th_floor -= dt * (V_th_floor - V_th) / tau_floor_decay;
        }
        double V_th_adaptive = std::max(
            V_th + dV_th * (1 - h_spike),
            V_th_floor
        );
        samples.V_th_adaptive[i] = V_th_adaptive;
        return V_th_adaptive;
    }
    
    void update_with_classical_reset_clamp(size_t i, double t) {
        double I = update_currents(i);
        
        if (t < (t_last_spike + refractory_period)) {
            Vm = V_reset;
            return;
        }
        
        double dV = update_membrane_potential_forward_Euler(I);
        
        double V_th_adaptive = update_adaptive_threshold(i);
        
        // Check possible spiking:
        check_spiking(i, t, V_th_adaptive);
    }
    
    void update_with_reset_options(size_t i, double t) {
        // (Option:) Spike onset drives membrane potential below threshold.
        if (spike_option == SpikeOption::RESET_ONSET) {
            if ((last_spike_idx + 1) == static_cast<double>(i)) {
                Vm = V_reset;
            }
        }
        
        double dV = 0;
        if (use_exponential_Euler) {
            if (!Cm_option) {
                update_membrane_potential_exponential_Euler_Rm(i);
            } else {
                update_membrane_potential_exponential_Euler_Cm(i);
            }
        } else {
            double I = update_currents(i);
            dV = update_membrane_potential_forward_Euler(I);
        }
        
        double V_th_adaptive = update_adaptive_threshold(i);
        
        if (t >= (t_last_spike + refractory_period)) {
            // (Option:) Drive membrane potential below threshold after absolute refractory period.
            if (spike_option != SpikeOption::RESET_ONSET && !reset_done) {
                Vm = V_reset + dV;
                reset_done = true;
            }
            
            // Check possible spiking:
            check_spiking(i, t, V_th_adaptive);
        }
    }
    
    void update(size_t i, double t) {
        // Hard-cap nonlinear spiking fatigue threshold.
        if (with_fatigue_threshold) {
            fatigue -= dt / tau_fatigue_recovery;
            fatigue = std::max(fatigue, 0.0);
        }
        
        update_conductances(i, t);
        
        if (classical_IF) {
            update_with_classical_reset_clamp(i, t);
        } else {
            update_with_reset_options(i, t);
        }
    }
    
    void record(size_t i) {
        samples.Vm[i] = Vm;
        samples.fAHP[i] = g_fAHP;
        samples.sAHP[i] = g_sAHP;
        samples.ADP[i] = g_ADP;
    }
};

// Initial weights and reversal potentials
std::map<std::string, std::vector<double>> initial_weights_and_Erev = {
    {"AMPA", {0.5, 0}},
    {"NMDA", {0.5, 0}},
    {"GABA", {0.5, -70}}
};

std::map<std::string, std::map<std::string, double>> initial_weights;

// STDP parameters by receptor type
std::map<std::string, std::vector<double>> receptor_STDP = {
    {"AMPA", {0.01, 0.01, 20.0, 20.0}}, // A_pos, A_neg, tau_pos, tau_neg, type
    {"NMDA", {0, 0, 0, 0}},
    {"GABA", {0, 0, 0, 0}}
};

int main() {
    auto start_time = std::chrono::high_resolution_clock::now();
    
    if (burst_drive) {
        include_inhibition = false;
    }
    
    if (classical_IF) {
        use_exponential_Euler = false;
    }
    
    if (quantal_trigger) {
        initial_weights = {
            {"PyrOut", {{"PyrIn", 0.3}, {"IntIn", 0.3}}}
        };
    }
    
    // Create neurons
    std::map<std::string, IF_neuron*> neurons;
    std::vector<double> t_in;
    
    if (burst_drive) {
        if (compact_burst_driver) {
            for (int t = 0; t < compact_driver_spikes; ++t) {
                t_in.push_back((t + 1) * 5);
            }
        } else {
            for (int t = 0; t < long_driver_spikes; ++t) {
                t_in.push_back((t + 1) * 10);
            }
        }
    } else {
        if (long_regular_input) {
            for (int t = 0; t < static_cast<int>(0.75 * T / 100); ++t) {
                t_in.push_back((t + 1) * 100);
            }
        } else {
            t_in = {100};
        }
    }
    
    IF_neuron* PyrIn = new IF_neuron("PyrIn", t_in, {});
    neurons[PyrIn->id] = PyrIn;
    
    std::vector<double> intin_spikes;
    if (include_inhibition) {
        if (simulate_recurrent_inhibition) {
            for (double t : t_in) {
                intin_spikes.push_back(t + 3);
            }
        } else {
            for (double t : t_in) {
                intin_spikes.push_back(t + 150);
            }
        }
    }
    
    IF_neuron* IntIn = new IF_neuron("IntIn", intin_spikes, {});
    IntIn->g_peak_sAHP = 0.0; // no slow AHP for interneurons
    IntIn->g_peak_ADP = 0.0; // no ADP for interneurons
    neurons[IntIn->id] = IntIn;
    
    IF_neuron* PyrOut = new IF_neuron("PyrOut", {}, {});
    neurons[PyrOut->id] = PyrOut;
    
    // Create synapses
    double NMDA_g_rec_peak;
    if (with_explicit_voltage_gating) {
        NMDA_g_rec_peak = 50e-3; // 50 pS intended peak at average open receptor gated fraction
    } else {
        NMDA_g_rec_peak = 50e-3/2; // Adjusted to account for the absence of voltage-gated modulation
    }
    
    std::vector<Netmorph_Syn> nmsyn;
    for (int i = 0; i < 21; ++i) {
        nmsyn.emplace_back(PyrIn->id, PyrOut->id, "AMPA", 0.83*60*0.0086, 20e-3, 0.5, 3, 100, 1, 1.0, false);
        nmsyn.emplace_back(PyrIn->id, PyrOut->id, "NMDA", 0.17*60*0.0086, NMDA_g_rec_peak, 2, 100, 100, 1, 1.0, with_explicit_voltage_gating);
        nmsyn.emplace_back(IntIn->id, PyrOut->id, "GABA", 10*0.0086, 80e-3, 0.5, 10, 100, 1, 1.0, false);
    }
    
    // Organize synapses by target neuron, receptor type, and source neuron
    std::map<std::string, std::map<std::string, std::map<std::string, std::vector<Netmorph_Syn>>>> nmsyn_by_neuron;
    
    for (auto& s : nmsyn) {
        auto target = s.n_to;
        if (neurons.find(target) != neurons.end()) {
            nmsyn_by_neuron[target][s.receptor][s.n_from].push_back(s);
        }
    }
    
    // Create PreSyn objects for each neuron
    std::map<std::string, std::vector<PreSyn*>> presyn_by_neuron;
    PreSyn* SynRef = nullptr;
    
    for (auto& [n_id, neuron] : neurons) {
        auto& n_nmsyn = nmsyn_by_neuron[n_id];
        for (auto& [receptor, sources] : n_nmsyn) {
            for (auto& [source_id, synapses] : sources) {
                std::vector<double> receptor_onset_delay;
                std::vector<double> receptor_tau_rise;
                std::vector<double> receptor_tau_decay;
                double total_g_peak = 0;
                bool voltage_gated = false;
                
                for (auto& s : synapses) {
                    double g_peak = s.quantity * s.g_rec_peak;
                    total_g_peak += g_peak;
                    if (s.voltage_gated) {
                        voltage_gated = true;
                    }
                    receptor_onset_delay.push_back(s.onset_delay);
                    receptor_tau_rise.push_back(s.tau_rise);
                    receptor_tau_decay.push_back(s.tau_decay);
                }
                
                double median_onset_delay = 0;
                if (!receptor_onset_delay.empty()) {
                    std::sort(receptor_onset_delay.begin(), receptor_onset_delay.end());
                    median_onset_delay = receptor_onset_delay[receptor_onset_delay.size() / 2];
                }
                
                double median_tau_rise = 0;
                if (!receptor_tau_rise.empty()) {
                    std::sort(receptor_tau_rise.begin(), receptor_tau_rise.end());
                    median_tau_rise = receptor_tau_rise[receptor_tau_rise.size() / 2];
                }
                
                double median_tau_decay = 0;
                if (!receptor_tau_decay.empty()) {
                    std::sort(receptor_tau_decay.begin(), receptor_tau_decay.end());
                    median_tau_decay = receptor_tau_decay[receptor_tau_decay.size() / 2];
                }
                
                double weight;
                if (quantal_trigger) {
                    weight = initial_weights[n_id][source_id];
                } else {
                    weight = initial_weights_and_Erev[receptor][0];
                }
                
                std::string stdp_type;
                if (receptor == "AMPA") {
                    stdp_type = "Hebbian";
                } else if (receptor == "GABA") {
                    stdp_type = "None"; // This circuit does not include (Anti-Hebbian) GABA updates
                } else {
                    stdp_type = "None";
                }
                
                auto* ps = new PreSyn(
                    receptor,
                    neurons[source_id],
                    median_tau_rise,
                    median_tau_decay,
                    initial_weights_and_Erev[receptor][1],
                    total_g_peak,
                    weight,
                    median_onset_delay,
                    stdp_type,
                    receptor_STDP[receptor][0],
                    receptor_STDP[receptor][1],
                    receptor_STDP[receptor][2],
                    receptor_STDP[receptor][3],
                    voltage_gated
                );
                
                presyn_by_neuron[n_id].push_back(ps);
                
                if (n_id == "PyrOut" && receptor == "AMPA" && source_id == "PyrIn") {
                    SynRef = ps;
                }
            }
        }
    }
    
    // Set up connections for each neuron
    for (auto& [n_id, presyns] : presyn_by_neuron) {
        neurons[n_id]->set_presyn(presyns);
    }
    
    std::cout << "Number of PyrIn Forced spikes: " << PyrIn->force_spikes.size() << std::endl;
    std::cout << "Number of IntIn Forced spikes: " << IntIn->force_spikes.size() << std::endl;
    
    // Simulation loop
    double t = 0;
    std::vector<double> synref_w(n_steps, 0.0);
    
    for (size_t i = 0; i < n_steps; ++i) {
        PyrIn->update(i, t);
        PyrIn->record(i);
        
        IntIn->update(i, t);
        IntIn->record(i);
        
        PyrOut->update(i, t);
        PyrOut->record(i);
        
        if (SynRef) {
            synref_w[i] = SynRef->weight;
        }
        
        t += dt;
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed_time = end_time - start_time;
    std::cout << "Simulation time: " << elapsed_time.count() << " seconds" << std::endl;
    
    // Clean up
    for (auto& [id, neuron] : neurons) {
        delete neuron;
    }
    
    for (auto& [id, presyns] : presyn_by_neuron) {
        for (auto ps : presyns) {
            delete ps;
        }
    }
    
    return 0;
}