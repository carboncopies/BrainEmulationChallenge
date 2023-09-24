"""
Tests for module BG_API.py
"""
import json
import random
import pytest
import requests
import context
from src.components.NES_interfaces.BG_API import (
    API_call_raw,
    BGNES_handle_response,
    BGAPI_call,
    BGNES_Version,
    BGNES_Status,
    BGNES_GetToken,
    BGNES_simulation_create,
    BGNES_simulation_reset,
    BGNES_simulation_runfor,
    BGNES_get_simulation_status,
    BGNES_simulation_recordall,
    BGNES_get_recording,
    BGNES_sphere_create,
    BGNES_cylinder_create,
    BGNES_box_create,
    BGNES_BS_compartment_create,
    BGNES_connection_staple_create,
    BGNES_BS_receptor_create,
    BGNES_DAC_create,
    BGNES_DAC_set_output_list,
    BGNES_ADC_create,
    BGNES_ADC_set_sample_rate,
    BGNES_ADC_get_recorded_data,
    BGNES_QuickStart,
)


@pytest.fixture
def setup_NES() -> tuple[str, str]:
    """Sets up a BrainGenix NES simulation and returns the
    authentication token and simulation ID."""
    print("Getting authentication token...")
    username, password = "Admonishing", "Instruction"
    AUTHKEY = BGNES_GetToken(username, password)

    print("Calling BGNES_simulation_create...")
    name = random.sample(list("abcdefghijklmnop"), k=4)
    # SIMID = BGNES_simulation_create("".join(name))
    SIMID = "1"
    return AUTHKEY, SIMID


@pytest.fixture
def teardown_NES() -> str:
    """Resets a BrainGenix NES simulation."""
    return BGNES_simulation_reset()


def test_API_call_raw():
    """
    Tests a "raw" GET request to the BrainGenix API.
    """
    uri = "http://api.braingenix.org:8000"
    response = API_call_raw(uri)
    assert response.status_code == 200


def test_BGAPI_call():
    """
    Tests an API call to the BrainGenix API.
    """
    response = BGAPI_call("/Diagnostic/Version")
    assert response.ok
    assert isinstance(response.json()["Version"], str)


def test_BGNES_handle_response():
    """
    Tests how the responses from the BrainGenix API are handled.
    """
    response = BGAPI_call("/Diagnostic/Status")
    result = BGNES_handle_response(
        response, "BGNES_Status", ["SystemState", "ServiceStateNES"]
    )
    assert isinstance(result, list)
    assert isinstance(result[0], str)

    # Failure case 1: StatusCode is not 0 or 3
    # TODO: BGNE_handle_response() may need a possible refactor as
    #       the "except" branch raises an Exception that does not distinguish
    #       between whether the failure is because the status code is not 0 or
    #       3, or because the JSON does not contain a "StatusCode".
    #       Commenting out this test case until refactor is complete.

    # with pytest.raises(Exception) as excinfo:
    #     authkey, name = "foo", "bar"
    #     response = BGAPI_call(
    #         "/NES/Simulation/Create?AuthKey=%s&SimulationName=%s" % (authkey, name)
    #     )
    #     result = BGNES_handle_response(
    #         response, "BGNES_simulation_create", ["SimulationID"]
    #     )[0]
    # assert "API returned status code" in str(excinfo.value)

    # Failure case 2: Response does not contain JSON data with key
    # "StatusCode"
    # TODO: What is a case that always fails?
    # TODO: See TODO for Failure case 1 above.
    with pytest.raises(Exception) as excinfo:
        authkey, name = "foo", "bar"
        response = BGAPI_call(
            "/NES/Simulation/Create?AuthKey=%s&SimulationName=%s" % (authkey, name)
        )
        result = BGNES_handle_response(
            response, "BGNES_simulation_create", ["SimulationID"]
        )[0]

    assert "API did not return expected JSON data" in str(excinfo.value)

    # Failure case 3: GET request did not return a successful response.
    # TODO: What is a case that always fails?
    #       Code might need refactoring to return a HTTP error code
    #       for requests to arbitrary endpoints.
    # with pytest.raises(Exception) as excinfo:
    #     response = BGAPI_call("/foobar")
    # assert "Failed with GET status" in str(excinfo.value)


def test_BGNES_Version():
    """Tests if the correct version of BrainGenix NES is returned."""
    version = BGNES_Version()
    assert isinstance(version, str)
    assert version != ""

    # Version is of format XX.YY.ZZ
    assert len(version.split(".")) == 3
    major, minor, patch = version.split(".")
    assert major.isdigit() and minor.isdigit() and patch.isdigit()


def test_BGNES_Status():
    """Tests if a valid status of BrainGenix NES is returned."""
    systemstate, servicestate = BGNES_Status()
    assert isinstance(systemstate, str) and isinstance(servicestate, int)
    assert systemstate != "" and servicestate != None


def test_BGNES_GetToken():
    """Tests the token generation service of BrainGenix NES."""
    user, password = "Admonishing", "Instruction"
    token = BGNES_GetToken(user, password)

    # TODO: Make this more robust
    assert isinstance(token, str)
    assert len(token) != 0


def test_BGNES_simulation_create(setup_NES: tuple[str, str]):
    """Tests if attempting to create a simulation is successful."""
    _, _ = setup_NES
    simulation_id = BGNES_simulation_create("test")
    assert isinstance(simulation_id, str)
    assert simulation_id != ""
    assert simulation_id.isdigit()


def test_BGNES_sphere_create(setup_NES: tuple[str, str]):
    """Tests sphere creation facility."""
    _, _ = setup_NES
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    assert isinstance(sphere_id, str)
    assert sphere_id != ""


def test_BGNES_cylinder_create(setup_NES: tuple[str, str]):
    """Tests cylinder creation facility."""
    cylinder_id = BGNES_cylinder_create(10, (0, 0, 0), 20, (10, 10, 10))
    assert isinstance(cylinder_id, str)
    assert cylinder_id != ""


def test_BGNES_box_create(setup_NES: tuple[str, str]):
    """Tests box creation facility."""
    box_id = BGNES_box_create((0, 0, 0), (10, 10, 10), (0, 0, 0))
    assert isinstance(box_id, str)
    assert box_id != ""


def test_BGNES_BS_compartment_create(setup_NES: tuple[str, str]):
    """Tests compartment creation facility."""
    # Case 1: Using a sphere
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    assert isinstance(compartment_id, str)
    assert compartment_id != ""

    # Case 2: Using a cylinder
    cylinder_id = BGNES_cylinder_create(10, (0, 0, 0), 20, (10, 10, 10))
    compartment_id = BGNES_BS_compartment_create(
        cylinder_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    assert isinstance(compartment_id, str)
    assert compartment_id != ""

    # Case 3: Using a box
    box_id = BGNES_box_create((0, 0, 0), (10, 10, 10), (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        box_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    assert isinstance(compartment_id, str)
    assert compartment_id != ""


def test_BGNES_connection_staple_create(setup_NES: tuple[str, str]):
    """Test staple creation facility."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    cylinder_id = BGNES_cylinder_create(10, (0, 0, 0), 20, (10, 10, 10))
    second_compartment_id = BGNES_BS_compartment_create(
        cylinder_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )

    staple_id = BGNES_connection_staple_create(compartment_id, second_compartment_id)
    assert isinstance(staple_id, str)
    assert staple_id != ""


def test_BGNES_BS_receptor_create(setup_NES: tuple[str, str]):
    """Test receptor creation facility."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    cylinder_id = BGNES_cylinder_create(10, (0, 0, 0), 20, (10, 10, 10))
    second_compartment_id = BGNES_BS_compartment_create(
        cylinder_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )

    receptor_id = BGNES_BS_receptor_create(
        compartment_id, second_compartment_id, 50.0, 30.0, (5, 5, 5)
    )
    assert isinstance(receptor_id, str)
    assert receptor_id != ""


def test_BGNES_DAC_create(setup_NES: tuple[str, str]):
    """Test DAC creation facility."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    DAC_id = BGNES_DAC_create(compartment_id, (2, 2, 2))
    assert isinstance(DAC_id, str)
    assert DAC_id != ""


def test_BGNES_DAC_set_output_list(setup_NES: tuple[str, str]):
    """Test if the output list for a DAC is set correctly."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    DAC_id = BGNES_DAC_create(compartment_id, (2, 2, 2))

    status = BGNES_DAC_set_output_list(DAC_id, [50.0, 60.0, 70.0], 100.0)
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_ADC_create(setup_NES: tuple[str, str]):
    """Test ADC creation facility."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    ADC_id = BGNES_ADC_create(compartment_id, (2, 2, 2))
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_ADC_set_sample_rate(setup_NES: tuple[str, str]):
    """Test if the sample rate of a created ADC is set correctly."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    ADC_id = BGNES_ADC_create(compartment_id, (2, 2, 2))
    status = BGNES_ADC_set_sample_rate(ADC_id, 1.0)
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_ADC_get_recorded_data(setup_NES: tuple[str, str]):
    """Test if an ADC returns the correct recorded data."""
    sphere_id = BGNES_sphere_create(10, (0, 0, 0))
    compartment_id = BGNES_BS_compartment_create(
        sphere_id, -60.0, -50.0, 30.0, 30.0, -20.0
    )
    ADC_id = BGNES_ADC_create(compartment_id, (2, 2, 2))
    status = BGNES_ADC_set_sample_rate(ADC_id, 1.0)

    data, timestep = BGNES_ADC_get_recorded_data(ADC_id)

    assert isinstance(data, float)
    assert isinstance(timestep, float)
    assert timestep >= 0.0


def test_BGNES_simulation_recordall(setup_NES: tuple[str, str]):
    """Test if the time for which data is to be recorded is set
    correctly."""
    status = BGNES_simulation_recordall(-1)
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_simulation_runfor(setup_NES: tuple[str, str]):
    """Test if the simulation is run for the set time."""
    status = BGNES_simulation_runfor(500.0)
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_get_simulation_status(setup_NES: tuple[str, str]):
    """Test if the correct simulation status is returned by
    an API call."""
    status = BGNES_get_simulation_status()
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_get_recording(setup_NES: tuple[str, str]):
    """Test if the recording of a simulation is returned correctly."""
    data = BGNES_get_recording()
    assert isinstance(data, dict)  # TODO: Make this more robust.


def test_BGNES_simulation_reset(setup_NES: tuple[str, str]):
    """Test if a NES simulation is reset correctly."""
    status = BGNES_simulation_reset()
    assert isinstance(status, str)
    assert status != ""


def test_BGNES_QuickStart():
    """Test if the quickstart function for the BrainGenix NES
    starts it up properly."""

    user, password = "Username", "Password"
    scriptversion = "0.0.1"
    retval = BGNES_QuickStart(user, password, scriptversion, True, False)

    assert retval  # TODO: Make this more robust.
