import pickle

from NES_interfaces import KGTRecords


def test_extract_t_Vm_from_neurons_orders_by_id():
    data = {
        't_ms': [0.0, 1.0],
        'neurons': {
            '2': {'Vm_mV': [-60.0, -59.0]},
            '0': {'Vm_mV': [-70.0, -69.0]},
            '1': {'Vm_mV': [-65.0, -64.0]},
        },
    }
    t_ms, vm = KGTRecords.extract_t_Vm(data)
    assert t_ms == [0.0, 1.0]
    assert vm == [[-70.0, -69.0], [-65.0, -64.0], [-60.0, -59.0]]


def test_extract_t_Vm_skips_neurons_without_Vm():
    data = {'t_ms': [0.0], 'neurons': {'0': {'Vm_mV': [-70.0]}, '1': {}}}
    _, vm = KGTRecords.extract_t_Vm(data)
    assert vm == [[-70.0]]


def test_extract_t_Vm_from_circuits():
    data = {
        't_ms': [0.0, 1.0],
        'circuits': {
            'regionA': {'cell0': {'Vm_mV': [-70.0, -68.0]}},
            'regionB': {'cell1': {'Vm_mV': [-71.0, -69.0]}},
        },
    }
    _, vm = KGTRecords.extract_t_Vm(data)
    assert sorted(vm) == [[-71.0, -69.0], [-70.0, -68.0]]


def test_extract_t_Vm_missing_data_returns_none():
    assert KGTRecords.extract_t_Vm({'neurons': {}}) == (None, None)
    assert KGTRecords.extract_t_Vm({'t_ms': [0.0]}) == (None, None)


def test_extract_spiketimes_orders_by_id():
    data = {
        '1': {'tSpike_ms': [5.0]},
        '0': {'tSpike_ms': [1.0, 2.0]},
    }
    assert KGTRecords.extract_spiketimes(data) == [[1.0, 2.0], [5.0]]


def test_extract_spiketimes_without_spikes_returns_none():
    assert KGTRecords.extract_spiketimes({'0': {}}) is None


def test_save_t_Vm_pickled_round_trip(tmp_path):
    out = tmp_path / 'nested' / 'out'
    KGTRecords.save_t_Vm_pickled([0.0, 1.0], [[-70.0, -69.0]], str(out), spikes_cells=[[0.5]])
    with open(out / 'groundtruth-Vm.pkl', 'rb') as f:
        saved = pickle.load(f)
    assert saved == {'t_ms': [0.0, 1.0], 'Vm_cells': [[-70.0, -69.0]], 'spikes_cells': [[0.5]]}


def test_plot_t_Vm_writes_figure(tmp_path):
    KGTRecords.plot_t_Vm([0.0, 1.0, 2.0], [[-70.0, -60.0, -70.0], [-65.0, -65.0, -64.0]],
                         str(tmp_path), figspecs={'figsize': (3, 3), 'linewidth': 0.5, 'figext': 'png'})
    assert (tmp_path / 'groundtruth-Vm.png').stat().st_size > 0
